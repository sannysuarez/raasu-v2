"""Product management routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.database import Product

products_bp = Blueprint('products', __name__, url_prefix='/products')

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@products_bp.route('/')
@login_required
def list_products():
    """List all products"""
    products = Product.query.filter_by(is_active=True).all()
    return render_template('products/list.html', products=products)

@products_bp.route('/api/all')
@login_required
def api_all_products():
    """API endpoint for all active products"""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'description': p.description
    } for p in products])

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    """Create new product (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        
        if not name or not price:
            flash('Name and price are required', 'danger')
            return redirect(url_for('products.create_product'))
        
        try:
            product = Product(
                name=name,
                price=float(price),
                description=description
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{name}" created successfully', 'success')
            return redirect(url_for('products.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating product: {str(e)}', 'danger')
    
    return render_template('products/create.html')

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product (admin only)"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name', product.name)
        product.price = float(request.form.get('price', product.price))
        product.description = request.form.get('description', product.description)
        
        try:
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully', 'success')
            return redirect(url_for('products.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    return render_template('products/edit.html', product=product)

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete product (admin only)"""
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    try:
        # Soft delete - mark as inactive
        product.is_active = False
        db.session.commit()
        flash(f'Product "{product_name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
    
    return redirect(url_for('products.list_products'))
