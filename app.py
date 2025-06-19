from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Initialize Flask app and config
app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model definition
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Home route
@app.route('/')
def home():
    return render_template('homepage.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password_hash = generate_password_hash(request.form.get('password', ''), method='pbkdf2:sha256')
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        new_user = User(email=email, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, request.form.get('password', '')):
            session['user_id'] = user.id
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

# Dashboard (protected)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

# Validator page
@app.route('/validator')
def validator():
    return render_template('validator.html')

# Subscribe route
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip()
    # TODO: add subscriber to mailing list
    print(f"New subscriber: {email}")
    return redirect(url_for('home'))

# Analyze endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if user.credits <= 0:
        return jsonify({'error': 'out_of_credits'}), 403
    user.credits -= 1
    db.session.commit()

    data = request.get_json() or {}
    idea = data.get('idea', '')
    mode = data.get('mode', 'general')

    prompts = {
        'general': f"Act as a startup analyst. Analyze: '{idea}'. Provide summary, audience, value prop, pros/cons, competitor review, SWOT.",
        'sharktank': f"Act like a Shark Tank investor. Review: '{idea}'. Viability, investment amount, flaws, scaling, risks, profitability.",
        'lean': f"Act as a Lean Startup coach. Analyze: '{idea}'. MVP advice, validation, tests, assumptions, risks.",
        'vc': f"Act like a VC. Analyze: '{idea}'. TAM/SAM/SOM, GTM, defensibility, CAC/LTV, team strength.",
        'tech': f"Act as a technical co-founder. Analyze: '{idea}'. Build time, tech stack, risks, 3-month feasibility, architecture."            
    }
    prompt = prompts.get(mode, prompts['general'])

    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=800
        )
        result = response.choices[0].message.content.strip()
        return jsonify({'result': result, 'remaining_credits': user.credits})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run server
def create_app():
    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    create_app().run(debug=True)