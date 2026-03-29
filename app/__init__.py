from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    with app.app_context():
        # Import models
        from app.models.database import User, Product, Sale
        
        # Create tables
        db.create_all()
        
        # Initialize default users and products
        from app.utils.init_db import init_database
        init_database()
        
        # Register blueprints
        from app.routes.auth import auth_bp
        from app.routes.products import products_bp
        from app.routes.sales import sales_bp
        from app.routes.main import main_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(products_bp)
        app.register_blueprint(sales_bp)
        app.register_blueprint(main_bp)
    
    return app
