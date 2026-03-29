"""Database initialization with default data"""
from app import db
from app.models.database import User, Product

def init_database():
    """Initialize database with default users and sample products"""
    
    # Add default users if they don't exist
    users = [
        {
            'username': 'Admin',
            'email': 'ceo@raasu.local',
            'password': 'ceo@admin',
            'is_admin': True
        },
        {
            'username': 'admin',
            'email': 'admin@raasu.local',
            'password': 'admin123',
            'is_admin': True
        },
        {
            'username': 'Ibrahim',
            'email': 'ibrahim@raasu.local',
            'password': 'me@user',
            'is_admin': False
        },
        {
            'username': 'Umar',
            'email': 'umar@raasu.local',
            'password': 'me@user',
            'is_admin': False
        },
        {
            'username': 'Sanni',
            'email': 'sanni@raasu.local',
            'password': 'me@user',
            'is_admin': False
        }
    ]
    
    for user_data in users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                is_admin=user_data['is_admin']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    # Add default products if none exist
    if Product.query.count() == 0:
        sample_products = [
            {'name': 'Product A', 'price': 100.00, 'description': 'Sample Product A'},
            {'name': 'Product B', 'price': 250.00, 'description': 'Sample Product B'},
            {'name': 'Product C', 'price': 50.00, 'description': 'Sample Product C'},
            {'name': 'Product D', 'price': 150.00, 'description': 'Sample Product D'},
        ]
        
        for prod_data in sample_products:
            product = Product(**prod_data)
            db.session.add(product)
    
    db.session.commit()
