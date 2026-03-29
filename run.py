"""
RAASU v2.0.0 - Web-based Thermal Printer POS System
Main entry point
"""
import os
from app import create_app, db
from app.models.database import User, Product, Sale, SaleItem

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Make database models available in shell context"""
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Sale': Sale,
        'SaleItem': SaleItem
    }

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized')

@app.cli.command()
def seed_db():
    """Seed database with sample data"""
    from app.utils.init_db import init_database
    init_database()
    print('Database seeded')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
