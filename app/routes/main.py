"""Main routes for dashboard and home"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.database import Sale, Product, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    """Main dashboard"""
    # Get statistics
    today = datetime.now().date()
    
    today_total = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sale_date == today
    ).scalar() or 0.0
    
    total_products = Product.query.filter_by(is_active=True).count()
    total_sales = Sale.query.count()
    total_users = User.query.count()
    
    stats = {
        'today_total': today_total,
        'total_products': total_products,
        'total_sales': total_sales,
        'total_users': total_users,
        'is_admin': current_user.is_admin
    }
    
    return render_template('dashboard.html', stats=stats)

@main_bp.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    today = datetime.now().date()
    
    today_total = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sale_date == today
    ).scalar() or 0.0
    
    total_products = Product.query.filter_by(is_active=True).count()
    total_sales = Sale.query.count()
    
    return jsonify({
        'today_total': today_total,
        'total_products': total_products,
        'total_sales': total_sales,
        'date': today.isoformat()
    })
