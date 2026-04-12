"""Sales and reporting routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.database import Sale, SaleItem, Product
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import xlwt
import xlrd

# West Africa Time (WAT) timezone
WAT = ZoneInfo("Africa/Lagos")

HISTORY_FOLDER_NAME = 'raasu-venture-sales'
HISTORY_FILE_SUFFIX = '.xls'


def get_sales_history_folder():
    history_dir = Path(current_app.root_path).parent / HISTORY_FOLDER_NAME
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def get_history_file_path(date):
    return get_sales_history_folder() / f"{date.isoformat()}{HISTORY_FILE_SUFFIX}"


def write_daily_sales_xls(date):
    sales = Sale.query.filter(Sale.sale_date == date).order_by(Sale.created_at.asc()).all()
    history_file = get_history_file_path(date)

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Sales')

    headers = ['Sale ID', 'Date', 'Time', 'User', 'Total Amount', 'Payment Method', 'Printed', 'Items Count']
    for col_idx, header in enumerate(headers):
        sheet.write(0, col_idx, header)

    daily_total = 0.0
    for row_idx, sale in enumerate(sales, start=1):
        sale_time = sale.created_at.strftime('%H:%M:%S') if sale.created_at else ''
        sheet.write(row_idx, 0, sale.id)
        sheet.write(row_idx, 1, sale.sale_date.isoformat())
        sheet.write(row_idx, 2, sale_time)
        sheet.write(row_idx, 3, sale.user.username)
        sheet.write(row_idx, 4, float(sale.total_amount))
        sheet.write(row_idx, 5, sale.payment_method)
        sheet.write(row_idx, 6, 'Yes' if sale.is_printed else 'No')
        sheet.write(row_idx, 7, sale.items.count())
        daily_total += float(sale.total_amount)

    summary_row = len(sales) + 2
    sheet.write(summary_row, 3, 'Daily Total')
    sheet.write(summary_row, 4, float(daily_total))

    workbook.save(str(history_file))


def read_daily_total_from_xls(date):
    history_file = get_history_file_path(date)
    if not history_file.exists():
        return 0.0

    workbook = xlrd.open_workbook(str(history_file))
    sheet = workbook.sheet_by_index(0)
    if sheet.nrows < 2:
        return 0.0

    total = 0.0
    for row_idx in range(1, sheet.nrows):
        try:
            label_value = sheet.cell_value(row_idx, 3)
            if isinstance(label_value, str) and label_value == 'Daily Total':
                continue
            cell_value = sheet.cell_value(row_idx, 4)
            if isinstance(cell_value, (int, float)):
                total += float(cell_value)
        except IndexError:
            continue

    return total


def load_sales_history(start_date, end_date):
    history_dir = get_sales_history_folder()
    has_xls = any(path.suffix == HISTORY_FILE_SUFFIX for path in history_dir.iterdir())
    if not has_xls:
        sync_sales_history_from_db()

    daily_data = {}
    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i)
        if get_history_file_path(date).exists():
            total = read_daily_total_from_xls(date)
        else:
            total = 0.0
        daily_data[date.isoformat()] = total

    return daily_data


def sync_sales_history_from_db():
    history_dir = get_sales_history_folder()
    history_dir.mkdir(parents=True, exist_ok=True)
    unique_dates = {sale.sale_date for sale in Sale.query.all()}
    for date in unique_dates:
        write_daily_sales_xls(date)

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
            write_daily_sales_xls(sale.sale_date)
            
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
    end_date = datetime.now(WAT).date()
    start_date = end_date - timedelta(days=29)

    daily_data = load_sales_history(start_date, end_date)

    return jsonify({
        'dates': list(daily_data.keys()),
        'totals': list(daily_data.values()),
        'currency': 'NGN'
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
    today = datetime.now(WAT).date()
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
        if printer_info['type'] == 'Bluetooth':
            printer = ThermalReceiptPrinter()
            if not printer.connect(bluetooth_addr=printer_info['address']):
                return jsonify({'error': 'Failed to connect to Bluetooth printer'}), 500
        elif printer_info['type'] == 'Serial/Bluetooth':
            printer = ThermalReceiptPrinter()
            if not printer.connect(port=printer_info['port']):
                return jsonify({'error': 'Failed to connect to printer'}), 500
        elif printer_info['type'] == 'USB':
            printer = ThermalReceiptPrinter()
            if not printer.connect(usb_vendor_id=printer_info['vendor_id'], usb_product_id=printer_info['product_id']):
                return jsonify({'error': 'Failed to connect to USB printer'}), 500
        
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
        
        if printer_info['type'] in ['Serial/Bluetooth', 'Bluetooth', 'USB']:
            printer.disconnect()
        
        # Mark as printed
        sale.is_printed = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Receipt printed successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
