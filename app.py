from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import sys
from pip._vendor import cachecontrol
import logging
from flask_cors import CORS
import requests
import json
from flask import jsonify  # Add this import for the jsonify function
import time
from oauthlib.oauth2 import OAuth2Error  # Add this import for OAuth2 error handling  # Import the scraping function
from crypto_price_service import price_service 


os.chmod(os.path.abspath(__file__), 0o755)
# Updated global current_prices
current_prices = {
    'rndr': 0.0,
    'bst': 0.0,
    'ybr': 0.0,
    'rio': 0.0,
    'props': 0.0,
}

def update_prices(current_prices):
    """Update prices for all tokens using CoinGecko API."""
    print('hello world')
    for token in current_prices.keys():
        price = price_service.get_current_price(token)
        if price > 0:
            current_prices[token] = price
        else:
            print(f"Failed to fetch price for {token}, keeping previous value.")
    print(f"Updated prices: {current_prices}")
    return current_prices  # Debugging

# Schedule the price update every 2 minutes
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure the instance directory exists
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)


# Initialize Flask app
app = Flask(__name__)
import secrets  # Use this for secure secret key generation

# Set secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
# Configure SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


CORS(app, resources={r"/*": {"origins": "*"}})


@app.before_request
def log_request_info():
    logging.info('Headers: %s', request.headers)
    logging.info('Method: %s', request.method)
    logging.info('Path: %s', request.path)

@app.route('/debug')
def debug():
    return {
        'headers': dict(request.headers),
        'method': request.method,
        'path': request.path
    }


# Initialize database, bcrypt, and login manager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Changed from 'login_page' to 'login'



# Update User model to include Google ID
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True)  # Made nullable for Google login
    role = db.Column(db.String(50), nullable=False)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    amount_invested_aed = db.Column(db.Float, nullable=False)
    tokens_held_rndr = db.Column(db.Integer, nullable=False, default=0)
    tokens_held_props = db.Column(db.Integer, nullable=False, default=0)
    tokens_held_bst = db.Column(db.Integer, nullable=False, default=0)
    tokens_held_rio = db.Column(db.Integer, nullable=False, default=0)
    tokens_held_ybr = db.Column(db.Integer, nullable=False, default=0)
    price_prediction = db.Column(db.Float, nullable=False)
    
    # New commission-related fields
    commission_percentage = db.Column(db.Float, nullable=False, default=10.0)  # Default 10%
    commission_type = db.Column(db.String(50), nullable=False, default='percentage')  # or 'fixed'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/test_update_prices')
def test_update_prices():
    global current_prices
    current_prices=update_prices(current_prices)  # Call the function directly
    return (current_prices)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    # Check if user is admin
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            # Extract client data from form
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            # Create a new user for the client
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            new_user = User(
                name=name,
                email=email,
                password=hashed_password,
                role='client'
            )
            db.session.add(new_user)
            db.session.flush()  # This will populate the id without committing
            
            # Create new client record
            new_client = Client(
                name=name,
                amount_invested_aed=float(request.form.get('amount_invested_aed')),
                tokens_held_rndr=float(request.form.get('tokens_rndr')),
                tokens_held_props=float(request.form.get('tokens_props')),
                tokens_held_bst=float(request.form.get('tokens_bst')),
                tokens_held_rio=float(request.form.get('tokens_rio')),
                tokens_held_ybr=float(request.form.get('tokens_ybr')),
                price_prediction=0.0  # You might want to add this to the form or set a default
            )
            db.session.add(new_client)
            db.session.commit()
            
            flash('Client added successfully', 'success')
            return redirect(url_for('admin_dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding client: {str(e)}', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    # If it's a GET request, redirect to admin dashboard
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_client/<int:client_id>', methods=['DELETE'])
@login_required
def remove_client(client_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized access'}), 403

    try:
        # Find and delete the client
        client = Client.query.get_or_404(client_id)
        
        # Also find and delete the associated user
        user = User.query.filter_by(name=client.name).first()
        
        if user:
            db.session.delete(user)
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify({'message': 'Client removed successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# Regular login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login_page.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.password and bcrypt.check_password_hash(user.password, password):
        login_user(user)
        flash('Login successful!', 'success')
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    else:
        flash('Invalid email or password!', 'error')
        return redirect(url_for('login'))

# Error handler for OAuth errors
@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, OAuth2Error):
        flash('Failed to authenticate with Google.', 'error')
        return redirect(url_for('login'))
    raise error


# Admin dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    clients = Client.query.all()
    conversion_rate_aed_to_usd = 3.67

    # Totals
    total_rndr = total_props = total_bst = total_rio = total_ybr = 0
    total_invested_aed = 0

    for client in clients:
        total_rndr += client.tokens_held_rndr
        total_props += client.tokens_held_props
        total_bst += client.tokens_held_bst
        total_rio += client.tokens_held_rio
        total_ybr += client.tokens_held_ybr
        total_invested_aed += client.amount_invested_aed

    total_invested_usd = total_invested_aed / conversion_rate_aed_to_usd
    for client in clients:
        client.converted_to_usd = round(client.amount_invested_aed / conversion_rate_aed_to_usd, 2)


    return render_template(
        'admin_dashboard.html',
        clients=clients,
        current_prices=current_prices,
        total_rndr=total_rndr,
        total_props=total_props,
        total_bst=total_bst,
        total_rio=total_rio,
        total_ybr=total_ybr,
        total_invested_usd=total_invested_usd,
        total_invested_aed=total_invested_aed,
    )
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    # Ensure prices are updated
    global current_prices
    current_prices = update_prices(current_prices)

    current_client = Client.query.filter_by(name=current_user.name).first()
    if current_client:
        conversion_rate_aed_to_usd = 3.67
        current_client.converted_to_usd = round(current_client.amount_invested_aed / conversion_rate_aed_to_usd, 2)

        # Calculate the current value of each token
        current_values = {
            'rndr': current_prices['rndr'] * current_client.tokens_held_rndr,
            'props': current_prices['props'] * current_client.tokens_held_props,
            'bst': current_prices['bst'] * current_client.tokens_held_bst,
            'rio': current_prices['rio'] * current_client.tokens_held_rio,
            'ybr': current_prices['ybr'] * current_client.tokens_held_ybr
        }

        # Calculate total value of all tokens
        total_value = sum(current_values.values())

        # Calculate commission
        if current_client.commission_type == 'percentage':
            commission_amount = total_value * (current_client.commission_percentage / 100)
            net_value = total_value - commission_amount
        else:
            # If it's a fixed commission, you might want to adjust this logic
            commission_amount = current_client.commission_percentage
            net_value = total_value - commission_amount

        # Prepare client data with current prices and values
        client_data = {
            'name': current_client.name,
            'amount_invested_aed': current_client.amount_invested_aed,
            'converted_to_usd': current_client.converted_to_usd,
            'tokens_held_rndr': current_client.tokens_held_rndr,
            'tokens_held_props': current_client.tokens_held_props,
            'tokens_held_bst': current_client.tokens_held_bst,
            'tokens_held_rio': current_client.tokens_held_rio,
            'tokens_held_ybr': current_client.tokens_held_ybr,
            'current_prices': current_prices,
            'current_values': current_values,
            'total_value': total_value,
            'commission_percentage': current_client.commission_percentage,
            'commission_amount': commission_amount,
            'net_value': net_value
        }

        return render_template('client_dashboard.html', client=client_data)
    else:
        flash('No holdings found for this account.', 'info')
        return redirect(url_for('home'))
# Define a flag to track
#  whether the function has already run
@app.route('/api/prices/update')
@login_required
def update_prices_for_clients():
    """API endpoint for getting updated prices via AJAX."""
    if current_user.role in ('admin','client'):
        global current_prices
        current_prices = update_prices(current_prices)  # Call the function to update prices
        
        # Return the updated prices
        return jsonify(current_prices)
    
    return jsonify({'error': 'Unauthorized'}), 401

first_request_done = False

@app.before_request
def initialize_on_first_request():
    global first_request_done
    if not first_request_done:
        # Run database initialization logic
        with app.app_context():
            db.create_all()
     

        # Add test accounts (admin and clients)
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                name='Admin',
                email='admin@example.com',
                password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                role='admin'
            )
            db.session.add(admin)

        # Add Client 1
        if not User.query.filter_by(email='client1@example.com').first():
            client1 = User(
                name='Client1',
                email='client1@example.com',
                password=bcrypt.generate_password_hash('client123').decode('utf-8'),
                role='client'
            )
            client1_data = Client(
                name='Client1',
                amount_invested_aed=10000.0,
                tokens_held_rndr=50,  # Correctly set Render tokens
                tokens_held_props=10,  # Example for Propbase tokens
                tokens_held_bst=5,     # Example for Blocksquare tokens
                tokens_held_rio=3,     # Example for Realio tokens
                tokens_held_ybr=2,     # Example for YieldBricks tokens
                price_prediction=200.0,
                commission_percentage=10.0,  # 10% commission
                commission_type='percentage'
            )
            db.session.add(client1)
            db.session.add(client1_data)

        # Add Client 2
        if not User.query.filter_by(email='client2@example.com').first():
            client2 = User(
                name='Client2',
                email='client2@example.com',
                password=bcrypt.generate_password_hash('client123').decode('utf-8'),
                role='client'
            )
            client2_data = Client(
                name='Client2',
                amount_invested_aed=20000.0,
                tokens_held_rndr=30,  # Example for Render tokens
                tokens_held_props=20,  # Example for Propbase tokens
                tokens_held_bst=10,    # Example for Blocksquare tokens
                tokens_held_rio=5,     # Example for Realio tokens
                tokens_held_ybr=3,     # Example for YieldBricks tokens
                price_prediction=300.0,
                commission_percentage=10.0,  # 10% commission
                commission_type='percentage'
            )
            db.session.add(client2)
            db.session.add(client2_data)


        # Add Client 3
        if not User.query.filter_by(email='client3@example.com').first():
            client3 = User(
                name='Client3',
                email='client3@example.com',
                password=bcrypt.generate_password_hash('client123').decode('utf-8'),
                role='client'
            )
            client3_data = Client(
                name='Client3',
                amount_invested_aed=15000.0,
                tokens_held_rndr=40,  # Example for Render tokens
                tokens_held_props=15,  # Example for Propbase tokens
                tokens_held_bst=8,     # Example for Blocksquare tokens
                tokens_held_rio=4,     # Example for Realio tokens
                tokens_held_ybr=1, 
                price_prediction=100.0,
                commission_percentage=10.0,  # 10% commission
                commission_type='percentage'
            )
            db.session.add(client3)
            db.session.add(client3_data) 

        # Commit changes to the database
        db.session.commit()

        # Mark initialization as complete
        first_request_done = True

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))


# In your app.py, before running the app
def init_db():
    with app.app_context():
        try:
            # Create tables only if they don't exist
            db.create_all()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000,debug=True)