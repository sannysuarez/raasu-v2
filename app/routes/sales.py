"""Sales and reporting routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.database import Sale, SaleItem, Product
from datetime import datetime, timedelta
import json

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_sale():
    """Create new sale"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            items = data.get('items', [])
            
            if not items:
                return jsonify({'error': 'No items in sale'}), 400
            
            # Create sale
            sale = Sale(user_id=current_user.id)
            db.session.add(sale)
            db.session.flush()  # Get sale ID
            
            # Add items
            total = 0
            for item_data in items:
                product = Product.query.get(item_data['product_id'])
                if not product:
                    raise ValueError(f"Product {item_data['product_id']} not found")
                
                quantity = int(item_data['quantity'])
                price = float(product.price)
                item_total = quantity * price
                
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=price,
                    total=item_total
                )
                db.session.add(sale_item)
                total += item_total
            
            sale.total_amount = total
            db.session.commit()
            
            return jsonify({
                'success': True,
                'sale_id': sale.id,
                'total': total,
                'message': f'Sale created successfully. Total: {total:.2f}'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    products = Product.query.filter_by(is_active=True).all()
    return render_template('sales/new.html', products=products)

@sales_bp.route('/')
@login_required
def list_sales():
    """List sales"""
    page = request.args.get('page', 1, type=int)
    sales = Sale.query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('sales/list.html', sales=sales)

@sales_bp.route('/<int:sale_id>')
@login_required
def view_sale(sale_id):
    """View sale details"""
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales/view.html', sale=sale)

@sales_bp.route('/analytics/daily', methods=['GET'])
@login_required
def daily_analytics():
    """Get daily sales analytics for last 30 days"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)

    sales = Sale.query.filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).all()

    # Group by date
    daily_data = {}
    for i in range(30):
        date = start_date + timedelta(days=i)
        daily_data[date.isoformat()] = 0.0

    for sale in sales:
        date_key = sale.sale_date.isoformat()
        daily_data[date_key] += sale.total_amount

    return jsonify({
        'dates': list(daily_data.keys()),
        'totals': list(daily_data.values()),
        'currency': 'INR'
    })

@sales_bp.route('/analytics/chart')
@login_required
def analytics_chart():
    """Display 7-day analytics chart"""
    return render_template('sales/analytics.html')

@sales_bp.route('/today-total')
@login_required
def today_total():
    """Get today's total sales"""
    today = datetime.now().date()
    total = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sale_date == today
    ).scalar() or 0.0
    
    return jsonify({'total': total, 'date': today.isoformat()})

@sales_bp.route('/api/print/<int:sale_id>', methods=['POST'])
@login_required
def print_receipt(sale_id):
    """Print receipt for sale"""
    sale = Sale.query.get_or_404(sale_id)
    
    try:
        from app.utils.printer_detector import PrinterDetector
        from app.utils.receipt_printer import ThermalReceiptPrinter
        
        # Get available printers
        printers = PrinterDetector.get_all_printers()
        
        if not printers:
            return jsonify({'error': 'No printers detected'}), 404
        
        # Use first available printer
        printer_info = printers[0]
        
        # Initialize printer
        if printer_info['type'] == 'Serial/Bluetooth':
            printer = ThermalReceiptPrinter()
            if not printer.connect(printer_info['port']):
                return jsonify({'error': 'Failed to connect to printer'}), 500
        
        # Prepare items
        items = []
        for si in sale.items:
            items.append({
                'product_name': si.product.name,
                'quantity': si.quantity,
                'price': si.price
            })
        
        # Print receipt
        printer.print_revenue_receipt(
            venture_name='RAASU POS',
            address='Address will be configured',
            items=items,
            total=sale.total_amount,
            user_name=sale.user.username,
            date=sale.created_at
        )
        
        if printer_info['type'] == 'Serial/Bluetooth':
            printer.disconnect()
        
        # Mark as printed
        sale.is_printed = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Receipt printed successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
