from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto_dashboard.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Crypto API URL
CRYPTO_API = "https://api.coingecko.com/api/v3/simple/price"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'client'

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(50), nullable=False)
    tokens_held = db.Column(db.Float, nullable=False)
    price_prediction = db.Column(db.Float, nullable=True)
    invested_aed = db.Column(db.Float, nullable=False)
    invested_usd = db.Column(db.Float, nullable=False)

# Load user for login session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('client_dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('client_dashboard'))
    investments = db.session.query(User, Investment).join(Investment).all()
    return render_template('admin_dashboard.html', investments=investments)

@app.route('/client')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        return redirect(url_for('admin_dashboard'))
    investments = Investment.query.filter_by(user_id=current_user.id).all()
    return render_template('client_dashboard.html', investments=investments)

@app.route('/crypto_price/<token>', methods=['GET'])
def get_crypto_price(token):
    response = requests.get(f"{CRYPTO_API}?ids={token}&vs_currencies=aed,usd")
    return jsonify(response.json())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)


