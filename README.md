# RAASU v2.0.0

Web-based Thermal Printer POS System with SQLite Database

## Features

- **Web-based Interface**: Modern, responsive Flask web application
- **User Authentication**: 3 standard users + 1 admin account
- **Product Management**: Admin can add, edit, and delete products
- **Sales Tracking**: Daily sales recording with SQLite database
- **Thermal Printer Support**: USB and Bluetooth printer detection
- **Receipt Printing**: Automatic receipt generation with ESC/POS commands
- **Analytics**: 7-day sales comparison with charts
- **Dashboard**: Real-time statistics and quick actions

## Setup

### Requirements
- Python 3.8+
- Flask
- SQLAlchemy
- PySerial
- PyUSB

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py
```

The application will be available at `http://localhost:5000`

### Default Login Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**Users:**
- Username: `user1`, `user2`, `user3`
- Password: `user123` (all users)

## Project Structure

```
app/
├── models/
│   ├── __init__.py
│   └── database.py          # SQLAlchemy models
├── routes/
│   ├── auth.py              # Authentication routes
│   ├── products.py          # Product management
│   ├── sales.py             # Sales and reporting
│   └── main.py              # Dashboard
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
└── utils/
    ├── init_db.py           # Database initialization
    ├── printer_detector.py   # Thermal printer detection
    └── receipt_printer.py    # Receipt printing logic

config.py                      # Flask configuration
run.py                        # Application entry point
settings.py                   # Application settings
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET /auth/profile` - View user profile

### Products (Admin only)
- `GET /products/` - List products
- `GET /products/api/all` - API: Get all products
- `POST /products/create` - Create product
- `POST /products/<id>/edit` - Edit product
- `POST /products/<id>/delete` - Delete product

### Sales
- `POST /sales/new` - Create new sale
- `GET /sales/` - Sales history
- `GET /sales/<id>` - View sale details
- `GET /sales/analytics/daily` - Get 7-day analytics
- `GET /sales/analytics/chart` - Analytics chart page
- `POST /sales/api/print/<id>` - Print receipt

### Dashboard
- `GET /` - Main dashboard
- `GET /api/dashboard-stats` - Dashboard statistics

## Notes

- Bootstrap template can be customized by replacing templates
- Venture name and address can be configured in settings
- Printer detection happens automatically on printer selection
- Daily sales are grouped by date in the database

## Future Enhancements

- Inventory management
- Multiple printer support
- Advanced reporting
- Email receipts
- Payment integration
- Barcode scanning
