from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from forms import LoginForm, SignUpForm, ForgotPasswordForm, ResetPasswordForm, ProfileForm, AnswerForm, DeleteAccountForm
from datetime import datetime
import logging
import os
import secrets

app = Flask(__name__)
# Fix for running behind a reverse proxy (Tailscale, nginx, Render, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Database: use `DATABASE_URL` / `SQLALCHEMY_DATABASE_URI` when provided,
# otherwise fall back to a local SQLite file for simplicity and easy Render
# deployment without needing a managed Postgres DB.
database_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key: read from env or generate a random one for local dev
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Determine environment (Render sets PORT); treat presence of PORT as production
is_prod = bool(os.environ.get('PORT') or os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER'))

# Cookie and CSRF settings
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '1' if is_prod else '0') == '1'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = int(os.environ.get('WTF_CSRF_TIME_LIMIT', '3600'))  # seconds
app.config['PREFERRED_URL_SCHEME'] = 'https' if is_prod else os.environ.get('PREFERRED_URL_SCHEME', 'http')

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login" # type: ignore
login_manager.session_protection = "strong"

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; upgrade-insecure-requests"
    return response

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=True)
    birthdate = db.Column(db.String(10), nullable=True)
    firstName = db.Column(db.String(100), nullable=True)
    lastName = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(250), nullable=True)
    points = db.Column(db.Integer, default=0, nullable=False)

class Challenges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    published = db.Column(db.Boolean, default=False, nullable=False)
    ciphertext = db.Column(db.Text, nullable=True)
    plaintext = db.Column(db.Text, nullable=True)
    tips = db.Column(db.Text, nullable=True)
    title = db.Column(db.String(250), nullable=True)
    points_reward = db.Column(db.Integer, default=10, nullable=False)
    release_time = db.Column(db.DateTime, nullable=True)  # When the challenge becomes available
    closing_time = db.Column(db.DateTime, nullable=True)  # When the challenge closes
    
    def is_active(self):
        """Check if challenge is currently active (published and within time window)"""
        if not self.published:
            return False
        now = datetime.now()
        if self.release_time and now < self.release_time:
            return False  # Not yet released
        if self.closing_time and now > self.closing_time:
            return False  # Already closed
        return True
    
    def get_status(self):
        """Return status: 'active', 'upcoming', 'closed', or 'unpublished'"""
        if not self.published:
            return 'unpublished'
        now = datetime.now()
        if self.release_time and now < self.release_time:
            return 'upcoming'
        if self.closing_time and now > self.closing_time:
            return 'closed'
        return 'active'

class CompletedChallenges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.now)
    time_taken_seconds = db.Column(db.Integer, nullable=True)  # Time in seconds
    points_earned = db.Column(db.Integer, nullable=True)  # Actual points awarded
    # Ensure each user can only complete each challenge once
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),)

class ChallengeAttempts(db.Model):
    """Track when users start a challenge for time-based scoring"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge_attempt'),)

def calculate_points(base_points, time_seconds):
    """Calculate points based on time taken. Faster = more bonus points.
    
    Bonus structure:
    - Under 10 mins: 100% bonus (2x points)
    - Under 1 hour: 50% bonus (1.5x points)
    - Under 5 hours: 25% bonus (1.25x points)
    - Under 10 hours: 10% bonus (1.1x points)
    - Under 30 hours: 5% bonus (1.05x points)
    - Over 30 hours: base points only
    """
    if time_seconds < 600:  # Under 10 minutes
        multiplier = 2.0
    elif time_seconds < 3600:  # Under 1 hour
        multiplier = 1.5
    elif time_seconds < 18000:  # Under 5 hours
        multiplier = 1.25
    elif time_seconds < 36000:  # Under 10 hours
        multiplier = 1.1
    elif time_seconds < 108000:  # Under 30 hours
        multiplier = 1.05
    else:
        multiplier = 1.0
    
    return int(base_points * multiplier)

# Create database
with app.app_context():
    db.create_all()
    # Configure basic logging to stderr for Render logs
    logging.basicConfig(level=logging.INFO)
    
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Routes
@app.route('/')
def index():
    return render_template('index.html')

# Help pages
@app.route('/help/caesar')
def help_caesar():
    return render_template('help/caesar.html')

@app.route('/help/vigenere')
def help_vigenere():
    return render_template('help/vigenere.html')

@app.route('/help/substitution')
def help_substitution():
    return render_template('help/substitution.html')

@app.route('/help/playfair')
def help_playfair():
    return render_template('help/playfair.html')

@app.route('/help/transposition')
def help_transposition():
    return render_template('help/transposition.html')

@app.route('/leaderboard')
def leaderboard():
    users = Users.query.order_by(Users.points.desc()).all()
    
    # Calculate rankings with ties
    ranked_users = []
    current_rank = 1
    previous_points = None
    
    for i, user in enumerate(users):
        if previous_points is not None and user.points < previous_points:
            current_rank = i + 1
        ranked_users.append({
            'rank': current_rank,
            'username': user.username,
            'school': user.school or 'N/A',
            'points': user.points
        })
        previous_points = user.points
    
    return render_template('leaderboard.html', users=ranked_users)

@app.route('/challenges')
def challenges():
    return render_template('challenges.html')

@app.route('/challenge/<int:challenge_id>')
def challenge_detail(challenge_id):
    challenge = Challenges.query.get(challenge_id)
    
    if not challenge or not challenge.published:
        return render_template('challenges/notPublished.html')
    
    # Check time window
    status = challenge.get_status()
    if status == 'upcoming':
        return render_template('challenges/notPublished.html', 
                               message=f"This challenge opens on {challenge.release_time.strftime('%d %B %Y at %H:%M')}")
    if status == 'closed':
        return render_template('challenges/notPublished.html',
                               message=f"This challenge closed on {challenge.closing_time.strftime('%d %B %Y at %H:%M')}")
    
    # Check if user has already completed this challenge
    already_completed = False
    if current_user.is_authenticated:
        already_completed = CompletedChallenges.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first() is not None
        
        # Start tracking time if not already started and not completed
        if not already_completed:
            existing_attempt = ChallengeAttempts.query.filter_by(
                user_id=current_user.id,
                challenge_id=challenge_id
            ).first()
            if not existing_attempt:
                attempt = ChallengeAttempts()
                attempt.user_id = current_user.id
                attempt.challenge_id = challenge_id
                db.session.add(attempt)
                db.session.commit()
    
    form = AnswerForm()
    return render_template('challenges/challenge.html', challenge=challenge, already_completed=already_completed, form=form)

@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_answer(challenge_id):
    challenge = Challenges.query.get(challenge_id)
    
    if not challenge or not challenge.is_active():
        return render_template('challenges/notPublished.html')
    
    form = AnswerForm()
    
    # Check if already completed
    already_completed = CompletedChallenges.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first() is not None
    
    if already_completed:
        flash("You have already completed this challenge!", "error")
        return render_template('challenges/challenge.html', challenge=challenge, already_completed=True, form=form)
    
    if form.validate_on_submit():
        # Normalize answer: keep only alphabetic letters, lowercase
        answer = ''.join(c.lower() for c in (form.answer.data or '') if c.isalpha())
        correct_answer = ''.join(c.lower() for c in (challenge.plaintext or '') if c.isalpha())
        
        if answer == correct_answer:
            # Calculate time taken from release time
            if challenge.release_time:
                time_taken = (datetime.now() - challenge.release_time).total_seconds()
            else:
                # Fallback to attempt time if no release_time set
                attempt = ChallengeAttempts.query.filter_by(
                    user_id=current_user.id,
                    challenge_id=challenge_id
                ).first()
                if attempt:
                    time_taken = (datetime.now() - attempt.started_at).total_seconds()
                else:
                    time_taken = 108000  # Default to 30 hours (no bonus)
            
            time_taken_seconds = int(time_taken)
            
            # Calculate points with time bonus
            points_earned = calculate_points(challenge.points_reward, time_taken_seconds)
            
            # Record completion with time and points
            completion = CompletedChallenges()
            completion.user_id = current_user.id
            completion.challenge_id = challenge_id
            completion.time_taken_seconds = time_taken_seconds
            completion.points_earned = points_earned
            db.session.add(completion)
            current_user.points += points_earned
            db.session.commit()
            
            # Format time for display
            mins, secs = divmod(time_taken_seconds, 60)
            if mins > 0:
                time_str = f"{mins}m {secs}s"
            else:
                time_str = f"{secs}s"
            
            # Show bonus if earned
            bonus = points_earned - challenge.points_reward
            if bonus > 0:
                flash(f"Correct! Completed in {time_str}. You earned {challenge.points_reward} + {bonus} speed bonus = {points_earned} points!", "success")
            else:
                flash(f"Correct! Completed in {time_str}. You earned {points_earned} points!", "success")
            
            return render_template('challenges/challenge.html', challenge=challenge, already_completed=True, form=form)
        else:
            flash("Incorrect answer. Try again!", "error")
    
    return render_template('challenges/challenge.html', challenge=challenge, already_completed=False, form=form)

@app.route('/rules')
def rules():
    return "Rules Page - Coming Soon!"

@app.route('/dashboard')
@login_required
def dashboard():
    # Get all challenges and completed challenge IDs
    all_challenges = Challenges.query.order_by(Challenges.id).all()
    completed = CompletedChallenges.query.filter_by(user_id=current_user.id).all()
    completed_ids = set(c.challenge_id for c in completed)

    # Build a list of dicts with challenge and status
    challenge_statuses = []
    for challenge in all_challenges:
        status = challenge.get_status()
        challenge_statuses.append({
            'challenge': challenge,
            'status': status
        })

    # Calculate leaderboard position
    users = Users.query.order_by(Users.points.desc()).all()
    position = 1
    for i, user in enumerate(users):
        if user.id == current_user.id:
            # Handle ties - find actual position
            for j, u in enumerate(users):
                if u.points > current_user.points:
                    position = j + 2
                elif u.points == current_user.points and u.id != current_user.id:
                    continue
                else:
                    position = j + 1
                    break
            break

    return render_template('dashboard.html',
                           challenge_statuses=challenge_statuses,
                           completed_ids=completed_ids,
                           position=position,
                           total_users=len(users))

# Authentication Routes
@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    form = LoginForm()
    next_page = request.args.get('next')
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        next_page = form.next.data

        user = Users.query.filter_by(username=username).first()

        if user and user.password and password and check_password_hash(user.password, password):
            login_user(user)
            # Validate next_page to prevent open redirect
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")
    
    form.next.data = next_page
    return render_template("auth/login.html", form=form)

@app.route('/auth/signup', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    form = SignUpForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data

        if Users.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
            return render_template("auth/signUp.html", form=form)

        if Users.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return render_template("auth/signUp.html", form=form)


        password_val = form.password.data or ''
        hashed_password = generate_password_hash(password_val, method="pbkdf2:sha256")

        new_user = Users()
        new_user.username = username
        new_user.password = hashed_password
        new_user.email = email
        new_user.birthdate = str(form.birthdate.data)
        new_user.firstName = form.firstName.data
        new_user.lastName = form.lastName.data
        new_user.school = form.school.data
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.exception("Error creating new user")
            flash("An error occurred while creating your account. Please try again later.", "error")
            return render_template("auth/signUp.html", form=form)

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))
    
    return render_template("auth/signUp.html", form=form)

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    delete_form = DeleteAccountForm()
    
    if form.validate_on_submit():
        current_user.firstName = form.firstName.data
        current_user.lastName = form.lastName.data
        current_user.email = form.email.data
        current_user.birthdate = form.birthdate.data
        current_user.school = form.school.data
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))
    
    # Pre-populate form with current data
    if request.method == "GET":
        form.firstName.data = current_user.firstName
        form.lastName.data = current_user.lastName
        form.email.data = current_user.email
        form.birthdate.data = current_user.birthdate
        form.school.data = current_user.school
    
    return render_template("profile.html", form=form, delete_form=delete_form)

@app.route('/profile/delete', methods=["POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user = Users.query.get(current_user.id)
        # Delete user's completed challenges first
        CompletedChallenges.query.filter_by(user_id=current_user.id).delete()
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash("Your account has been deleted.", "success")
        return redirect(url_for("index"))
    return redirect(url_for("profile"))

@app.route('/auth/forgot-password', methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = Users.query.filter_by(email=email).first()
        
        if user:
            # Store user id in session for the reset step
            session['reset_user_id'] = user.id
            return redirect(url_for("reset_password"))
        else:
            flash("No account found with that email address.", "error")
    
    return render_template("auth/forgotPassword.html", form=form)

@app.route('/auth/reset-password', methods=["GET", "POST"])
def reset_password():
    user_id = session.get('reset_user_id')
    
    if not user_id:
        flash("Please start the password reset process again.", "error")
        return redirect(url_for("forgot_password"))
    
    user = Users.query.get(user_id)
    if not user:
        session.pop('reset_user_id', None)
        flash("Invalid reset session. Please try again.", "error")
        return redirect(url_for("forgot_password"))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        password_val = form.password.data or ''
        user.password = generate_password_hash(password_val, method="pbkdf2:sha256")
        db.session.commit()
        session.pop('reset_user_id', None)
        flash("Password reset successfully! Please login.", "success")
        return redirect(url_for("login"))
    
    return render_template("auth/resetPassword.html", form=form, username=user.username)

if __name__ == '__main__':
    # Runtime configuration for local / Tailscale development:
    # - Set DEV_ALLOW_HTTP=1 to run without SSL (useful for local or Tailscale)
    # - Set SSL_CERT and SSL_KEY to point to certificate files when using HTTPS
    # - Set FLASK_HOST / FLASK_PORT / FLASK_DEBUG to override defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5500'))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'

    ssl_cert = os.environ.get('SSL_CERT') or 'lr.tail24ded.ts.net.crt'
    ssl_key = os.environ.get('SSL_KEY') or 'lr.tail24ded.ts.net.key'

    # If DEV_ALLOW_HTTP=1 -> run without SSL and bind to 0.0.0.0 (for Tailscale)
    allow_http = os.environ.get('DEV_ALLOW_HTTP', '0') == '1'

    use_ssl = False
    if not allow_http and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        use_ssl = True

    if use_ssl:
        app.run(host=host, debug=debug, port=port, ssl_context=(ssl_cert, ssl_key))
    else:
        if allow_http:
            # Allow insecure cookies for local HTTP development
            app.config['SESSION_COOKIE_SECURE'] = False
            bind_host = os.environ.get('FLASK_BIND', '0.0.0.0')
            print(f"Running without SSL on http://{bind_host}:{port} (DEV_ALLOW_HTTP=1)")
            app.run(host=bind_host, debug=debug, port=port)
        else:
            # No certs found and HTTP not allowed: fall back to localhost without SSL
            print("No SSL certificate/key found. To run with HTTP set DEV_ALLOW_HTTP=1 or provide SSL_CERT and SSL_KEY.")
            app.run(host=host, debug=debug, port=port)