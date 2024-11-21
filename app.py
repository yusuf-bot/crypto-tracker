from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from crypto_price_service import price_service 
from token_price_cache import price_cache  # Import our price cache


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database, bcrypt, and login manager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Changed from 'login_page' to 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin' or 'client'

# Client model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    amount_invested_aed = db.Column(db.Float, nullable=False)
    tokens_held = db.Column(db.Integer, nullable=False)
    token_name = db.Column(db.String(100), nullable=False)
    price_prediction = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login routes
@app.route('/login', methods=['GET'])
def login():
    return render_template('login_page.html')

@app.route('/login', methods=['POST'])
def handle_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user)
        flash('Login successful!', 'success')
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    else:
        flash('Invalid email or password!', 'danger')
        return redirect(url_for('login'))

# Admin dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    clients = Client.query.all()
    conversion_rate_aed_to_usd = 0.27
    
    for client in clients:
        # Convert AED investment to USD
        client.converted_to_usd = client.amount_invested_aed * conversion_rate_aed_to_usd
        
        # Get current holdings data from cache
        holdings_data = price_cache.calculate_holdings(
            client.token_name,
            client.tokens_held
        )
        
        # Update client object with current values
        client.current_price = holdings_data['current_price']
        client.current_holdings = holdings_data['total_value']
        client.last_updated = holdings_data['last_updated']
        client.data_source = holdings_data['data_source']
        
        # Calculate profit/loss
        if client.current_holdings > 0:
            client.profit_loss = client.current_holdings - client.converted_to_usd
            client.profit_loss_percentage = (client.profit_loss / client.converted_to_usd) * 100
        else:
            client.profit_loss = 0
            client.profit_loss_percentage = 0
    
    return render_template('admin_dashboard.html', clients=clients)


@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    current_client = Client.query.filter_by(name=current_user.name).first()
    if current_client:
        conversion_rate_aed_to_usd = 0.27
        current_client.converted_to_usd = current_client.amount_invested_aed * conversion_rate_aed_to_usd
        
        # Get current holdings data from cache
        holdings_data = price_cache.calculate_holdings(
            current_client.token_name,
            current_client.tokens_held
        )
        
        # Update client object with current values
        current_client.current_price = holdings_data['current_price']
        current_client.current_holdings = holdings_data['total_value']
        current_client.last_updated = holdings_data['last_updated']
        current_client.data_source = holdings_data['data_source']
        
        # Calculate profit/loss
        if current_client.current_holdings > 0:
            current_client.profit_loss = current_client.current_holdings - current_client.converted_to_usd
            current_client.profit_loss_percentage = (current_client.profit_loss / current_client.converted_to_usd) * 100
        else:
            current_client.profit_loss = 0
            current_client.profit_loss_percentage = 0
        
        return render_template('client_dashboard.html', client=current_client)
    else:
        flash('No holdings found for this account.', 'info')
        return redirect(url_for('home'))

# Define a flag to track
#  whether the function has already run

@app.route('/api/prices/update')
@login_required
def update_prices():
    """API endpoint for getting updated prices via AJAX"""
    if current_user.role == 'admin':
        clients = Client.query.all()
        updates = {}
        
        for client in clients:
            holdings_data = price_cache.calculate_holdings(
                client.token_name,
                client.tokens_held
            )
            updates[client.name] = holdings_data
        
        return jsonify(updates)
    
    else:
        client = Client.query.filter_by(name=current_user.name).first()
        if client:
            holdings_data = price_cache.calculate_holdings(
                client.token_name,
                client.tokens_held
            )
            return jsonify({client.name: holdings_data})
    
    return jsonify({'error': 'Unauthorized'}), 401

first_request_done = False

@app.before_request
def initialize_on_first_request():
    global first_request_done
    if not first_request_done:
        # Run database initialization logic
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
                tokens_held=50,
                token_name='Bitcoin',
                price_prediction=200.0
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
                tokens_held=30,
                token_name='Ethereum',
                price_prediction=300.0
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
                tokens_held=40,
                token_name='Ripple',
                price_prediction=100.0
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

if __name__ == '__main__':
    app.run(debug=True)