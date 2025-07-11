from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import login_user, UserMixin, LoginManager, login_required, current_user
import json
import re

# Load environment variables
load_dotenv()

# Initialize Flask app and config
app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Secure session cookies for production
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Trust proxy headers (needed for HTTPS on Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model definition
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=True)  # Stores OpenAI output
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=True)
    output_text = db.Column(db.Text, nullable=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        login_user(new_user)
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, request.form.get('password', '')):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

# Dashboard (protected)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# Logout route
@app.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
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
@login_required
def analyze():
    user = current_user
    if user.credits <= 0:
        return jsonify({'error': 'out_of_credits'}), 403
    user.credits -= 1
    db.session.commit()
    data = request.get_json() or {}
    idea = data.get('idea', '')
    mode = data.get('mode', 'general')
    prompts = {
        'general': (
            f"Act as a startup analyst. Analyze: '{idea}'. "
            "Return a JSON object with these keys: summary, target_audience, value_proposition, pros_cons, competitor_review, swot, rating (1-5 stars, integer), startup_costs (with a brief breakdown, always include this field even if you have to estimate or say 'minimal'), and tech_stack (recommended for MVP). "
            "Each key should have a concise value."
        ),
        'sharktank': (
            f"Act like a Shark Tank investor. Review: '{idea}'. "
            "Return a JSON object with these keys: summary, target_audience, value_proposition, pros_cons, competitor_review, swot, rating (1-5 stars, integer), startup_costs (with a brief breakdown, always include this field even if you have to estimate or say 'minimal'), and tech_stack (recommended for MVP). "
            "Each key should have a concise value."
        ),
        'lean': (
            f"Act as a Lean Startup coach. Analyze: '{idea}'. "
            "Return a JSON object with these keys: summary, target_audience, value_proposition, pros_cons, competitor_review, swot, rating (1-5 stars, integer), startup_costs (with a brief breakdown, always include this field even if you have to estimate or say 'minimal'), and tech_stack (recommended for MVP). "
            "Each key should have a concise value."
        ),
        'vc': (
            f"Act like a VC. Analyze: '{idea}'. "
            "Return a JSON object with these keys: summary, target_audience, value_proposition, pros_cons, competitor_review, swot, rating (1-5 stars, integer), startup_costs (with a brief breakdown, always include this field even if you have to estimate or say 'minimal'), and tech_stack (recommended for MVP). "
            "Each key should have a concise value."
        ),
        'tech': (
            f"Act as a technical co-founder. Analyze: '{idea}'. "
            "Return a JSON object with these keys: summary, target_audience, value_proposition, pros_cons, competitor_review, swot, rating (1-5 stars, integer), startup_costs (with a brief breakdown, always include this field even if you have to estimate or say 'minimal'), and tech_stack (recommended for MVP). "
            "Each key should have a concise value."
        ),
    }
    prompt = prompts.get(mode, prompts['general'])
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        # Remove code block markers if present (robust version)
        result_text_clean = re.sub(r'^```(?:json)?\s*([\s\S]*?)\s*```$', r'\1', result_text.strip(), flags=re.MULTILINE)
        try:
            result_json = json.loads(result_text_clean)
        except Exception:
            # fallback: return as plain text if not valid JSON
            result_json = {'raw': result_text}
        # Generate plain text for export and saving
        def format_plain_text(data):
            if 'raw' in data:
                return data['raw']
            text = ''
            if data.get('summary'): text += 'Summary:\n' + data['summary'] + '\n\n'
            if data.get('target_audience'): text += 'Target Audience:\n' + data['target_audience'] + '\n\n'
            if data.get('value_proposition'): text += 'Value Proposition:\n' + data['value_proposition'] + '\n\n'
            if data.get('pros_cons'):
                text += 'Pros & Cons:\n'
                for k, v in data['pros_cons'].items():
                    if isinstance(v, list):
                        text += k.capitalize() + ':\n'
                        for item in v:
                            text += '- ' + item + '\n'
                    else:
                        text += k.capitalize() + ': ' + v + '\n'
                text += '\n'
            if data.get('competitor_review'): text += 'Competitor Review:\n' + data['competitor_review'] + '\n\n'
            if data.get('swot'):
                text += 'SWOT Analysis:\n'
                for k, v in data['swot'].items():
                    if isinstance(v, list):
                        text += k.capitalize() + ':\n'
                        for item in v:
                            text += '- ' + item + '\n'
                    else:
                        text += k.capitalize() + ': ' + v + '\n'
                text += '\n'
            if data.get('startup_costs'): text += 'Startup Costs:\n' + str(data['startup_costs']) + '\n\n'
            if data.get('tech_stack'): text += 'Tech Stack:\n' + str(data['tech_stack']) + '\n\n'
            if data.get('rating'): text += 'Rating: ' + str(data['rating']) + ' / 5\n'
            return text
        plain_text = format_plain_text(result_json)
        rating = result_json.get('rating') if isinstance(result_json, dict) else None
        # Save the idea and output
        idea_obj = Idea(user_id=user.id, content=idea, output=result_text, rating=rating, output_text=plain_text)
        db.session.add(idea_obj)
        db.session.commit()
        return jsonify({'result': result_json, 'remaining_credits': user.credits})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_idea', methods=['POST'])
@login_required
def save_idea():
    user_id = current_user.id
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    output = data.get('output', None)
    if not content:
        return jsonify({'error': 'empty_content'}), 400
    idea = Idea(user_id=user_id, content=content, output=output)
    db.session.add(idea)
    db.session.commit()
    return jsonify({'success': True, 'idea_id': idea.id, 'created_at': idea.created_at})

@app.route('/ideas', methods=['GET'])
@login_required
def get_ideas():
    user_id = current_user.id
    ideas = Idea.query.filter_by(user_id=user_id).order_by(Idea.created_at.desc()).all()
    ideas_data = [
        {'id': idea.id, 'content': idea.content, 'created_at': idea.created_at.isoformat()}
        for idea in ideas
    ]
    return jsonify({'ideas': ideas_data})

@app.route('/delete_idea/<int:idea_id>', methods=['DELETE'])
@login_required
def delete_idea(idea_id):
    user_id = current_user.id
    idea = Idea.query.filter_by(id=idea_id, user_id=user_id).first()
    if not idea:
        return jsonify({'error': 'not_found'}), 404
    db.session.delete(idea)
    db.session.commit()
    return jsonify({'success': True})

# Run server
def create_app():
    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    create_app().run(debug=True)