from flask import Flask, render_template, request, url_for, redirect, flash, session
import requests
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from forms import LoginForm, SignUpForm, ForgotPasswordForm, ResetPasswordForm, ProfileForm, AnswerForm, DeleteAccountForm
from datetime import datetime
from sqlalchemy import func
import db_client
import logging
import os
import secrets
import atexit
import signal
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)
# Fix for running behind a reverse proxy (Tailscale, nginx, Render, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Database: use `DATABASE_URL` / `SQLALCHEMY_DATABASE_URI` when provided,
# otherwise fall back to a local SQLite file for simplicity and easy Render
# deployment without needing a managed Postgres DB.
database_url = os.getenv('DATABASE_URL')  or 'https://cambscipher.tail24ded.ts.net'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key handling:
# - Prefer `SECRET_KEY` environment variable when provided.
# - Otherwise persist a generated key to `instance/secret_key` so it remains
#   consistent for the lifetime of the server process.
# - Remove the file on server shutdown (SIGINT/SIGTERM or normal exit).
env_secret = os.getenv('SECRET_KEY')
secret_file_path = os.path.join(app.instance_path, 'secret_key')
_manage_secret_file = False
if env_secret:
    app.config['SECRET_KEY'] = env_secret
else:
    _manage_secret_file = True
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, 'r') as f:
                app.config['SECRET_KEY'] = f.read().strip()
        except Exception:
            app.config['SECRET_KEY'] = secrets.token_hex(32)
            try:
                with open(secret_file_path, 'w') as f:
                    f.write(app.config['SECRET_KEY'])
                os.chmod(secret_file_path, 0o600)
            except Exception:
                pass
    else:
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        try:
            with open(secret_file_path, 'w') as f:
                f.write(app.config['SECRET_KEY'])
            os.chmod(secret_file_path, 0o600)
        except Exception:
            pass


def _cleanup_secret_file():
    try:
        if _manage_secret_file and os.path.exists(secret_file_path):
            os.remove(secret_file_path)
    except Exception:
        pass


def _signal_handler(signum, frame):
    _cleanup_secret_file()
    try:
        signal.signal(signum, signal.SIG_DFL)
    except Exception:
        pass
    os._exit(0)


# Register cleanup for normal interpreter exit and termination signals
atexit.register(_cleanup_secret_file)
try:
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
except Exception:
    # Some environments may not allow setting signal handlers
    pass

# Determine environment (Render sets PORT); treat presence of PORT as production
is_prod = bool(os.getenv('PORT') or os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER'))

# Cookie and CSRF settings
# Keep cookies HttpOnly and set SameSite by env (default: Lax)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

# Enable secure cookies when running in production (behind TLS like Tailscale)
# This allows local development over HTTP while ensuring browsers require TLS in prod.
app.config['SESSION_COOKIE_SECURE'] = bool(is_prod)
app.config['REMEMBER_COOKIE_SECURE'] = bool(is_prod)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Enable CSRF protection for all Flask-WTF forms
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60  # 1 hour

# Prefer https URLs when in production (external TLS handled by reverse proxy)
app.config['PREFERRED_URL_SCHEME'] = 'https' if is_prod else 'http'

login_manager = LoginManager(app)
login_manager.login_view = "login" # type: ignore
login_manager.session_protection = "strong"

# Initialize CSRF protection (adds validation for POST, PUT, DELETE, etc.)
csrf = CSRFProtect(app)


@app.after_request
def set_secure_headers(response):
    # Basic security headers to harden the app against common attacks
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'no-referrer-when-downgrade')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=()')
    # Conservative CSP to allow static assets while preventing cross-origin content
    csp = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline';"
    response.headers.setdefault('Content-Security-Policy', csp)
    return response

class RemoteUser(UserMixin):
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.username = data.get('username')
        self.password = data.get('password')
        self.email = data.get('email')
        self.birthdate = data.get('birthdate')
        self.firstName = data.get('firstName')
        self.lastName = data.get('lastName')
        self.school = data.get('school')
        self.points = data.get('points')


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

    
@login_manager.user_loader
def load_user(user_id):
    try:
        data = db_client.get_user_by_id(int(user_id))
        if not data:
            return None
        return RemoteUser(data)
    except Exception:
        return None

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
    users = db_client.get_leaderboard()
    ranked_users = []
    current_rank = 1
    previous_points = None
    for i, user in enumerate(users):
        if previous_points is not None and user['points'] < previous_points:
            current_rank = i + 1
        ranked_users.append({
            'rank': current_rank,
            'username': user['username'],
            'school': user.get('school', 'N/A'),
            'points': user.get('points', 0)
        })
        previous_points = user.get('points', 0)
    return render_template('leaderboard.html', users=ranked_users)

@app.route('/challenges')
def challenges():
    return render_template('challenges.html')

@app.route('/challenge/<int:challenge_id>')
def challenge_detail(challenge_id):
    challenge = db_client.get_challenge(challenge_id)
    if not challenge or not challenge.get('published'):
        return render_template('challenges/notPublished.html')

    status = challenge.get('status')
    if status == 'upcoming':
        rt = challenge.get('release_time')
        return render_template('challenges/notPublished.html', message=f"This challenge opens on {rt}")
    if status == 'closed':
        ct = challenge.get('closing_time')
        return render_template('challenges/notPublished.html', message=f"This challenge closed on {ct}")

    already_completed = False
    if current_user.is_authenticated:
        completed = db_client.get_user_completed(current_user.id)
        completed_ids = set(r['challenge_id'] for r in completed)
        already_completed = challenge_id in completed_ids

        if not already_completed:
            try:
                db_client.start_attempt(current_user.id, challenge_id)
            except Exception:
                pass

    form = AnswerForm()
    return render_template('challenges/challenge.html', challenge=challenge, already_completed=already_completed, form=form)

@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_answer(challenge_id):
    challenge = db_client.get_challenge(challenge_id)
    if not challenge or challenge.get('status') != 'active':
        return render_template('challenges/notPublished.html')

    form = AnswerForm()

    already_completed = False
    if current_user.is_authenticated:
        completed = db_client.get_user_completed(current_user.id)
        completed_ids = set(r['challenge_id'] for r in completed)
        already_completed = challenge_id in completed_ids
    if already_completed:
        flash("You have already completed this challenge!", "error")
        return render_template('challenges/challenge.html', challenge=challenge, already_completed=True, form=form)

    if form.validate_on_submit():
        answer = form.answer.data or ''
        res = db_client.submit_answer(current_user.id, challenge_id, answer)
        if not res.get('ok'):
            if res.get('reason') == 'incorrect':
                flash("Incorrect answer. Try again!", "error")
            elif res.get('reason') == 'already_completed':
                flash("You have already completed this challenge!", "error")
            else:
                flash("Submission failed.", "error")
            return render_template('challenges/challenge.html', challenge=challenge, already_completed=False, form=form)

        time_taken_seconds = res.get('time_seconds', 0)
        points_earned = res.get('points', 0)

        mins, secs = divmod(time_taken_seconds, 60)
        time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
        bonus = points_earned - (challenge.get('points_reward') or 0)
        if bonus > 0:
            flash(f"Correct! Completed in {time_str}. You earned {challenge.get('points_reward')} + {bonus} speed bonus = {points_earned} points!", "success")
        else:
            flash(f"Correct! Completed in {time_str}. You earned {points_earned} points!", "success")

        try:
            data = db_client.get_user_by_id(current_user.id)
            if data:
                current_user.points = data.get('points')
        except Exception:
            pass

        return render_template('challenges/challenge.html', challenge=challenge, already_completed=True, form=form)

    return render_template('challenges/challenge.html', challenge=challenge, already_completed=False, form=form)

@app.route('/rules')
def rules():
    return "Rules Page - Coming Soon!"

@app.route('/dashboard')
@login_required
def dashboard():
    all_challenges = db_client.list_challenges()
    completed_rows = db_client.get_user_completed(current_user.id)
    completed_ids = set(r['challenge_id'] for r in completed_rows)

    challenge_statuses = []
    for ch in all_challenges:
        challenge_statuses.append({'challenge': ch, 'status': ch.get('status')})

    users = db_client.get_leaderboard()
    position = 1
    for i, u in enumerate(users):
        if u.get('id') == current_user.id:
            position = i + 1
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

        user_data = db_client.get_user_by_username(username)
        if user_data and user_data.get('password') and password and check_password_hash(user_data.get('password'), password):
            user_obj = RemoteUser(user_data)
            login_user(user_obj)
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

        # Attempt to create via DB service
        payload = {
            'username': username,
            'password': form.password.data or '',
            'email': email,
            'birthdate': str(form.birthdate.data),
            'firstName': form.firstName.data,
            'lastName': form.lastName.data,
            'school': form.school.data,
        }
        try:
            res = db_client.create_user(payload)
        except Exception:
            logging.exception("Error creating new user via DB service")
            flash("An error occurred while creating your account. Please try again later.", "error")
            return render_template("auth/signUp.html", form=form)

        if not res.get('ok'):
            reason = res.get('reason')
            if reason == 'username_taken':
                flash("Username already taken!", "error")
            elif reason == 'email_taken':
                flash("Email already registered!", "error")
            else:
                flash("An error occurred while creating your account.", "error")
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
        payload = {
            'firstName': form.firstName.data,
            'lastName': form.lastName.data,
            'email': form.email.data,
            'birthdate': form.birthdate.data,
            'school': form.school.data,
        }
        try:
            db_client.update_user(current_user.id, payload)
            # refresh local user
            data = db_client.get_user_by_id(current_user.id)
            if data:
                current_user.firstName = data.get('firstName')
                current_user.lastName = data.get('lastName')
                current_user.email = data.get('email')
                current_user.birthdate = data.get('birthdate')
                current_user.school = data.get('school')
            flash("Profile updated successfully!", "success")
        except Exception:
            logging.exception("Error updating user via DB service")
            flash("An error occurred while updating your profile.", "error")
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
        try:
            db_client.delete_user(current_user.id)
            logout_user()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("index"))
        except Exception:
            logging.exception("Error deleting user via DB service")
            flash("An error occurred while deleting your account.", "error")
            return redirect(url_for("profile"))
    return redirect(url_for("profile"))

@app.route('/auth/forgot-password', methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = db_client.get_user_by_email(email)

        if user:
            session['reset_user_id'] = user.get('id')
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
        try:
            db_client.update_password(user_id, password_val)
            session.pop('reset_user_id', None)
            flash("Password reset successfully! Please login.", "success")
            return redirect(url_for("login"))
        except Exception:
            logging.exception("Error resetting password via DB service")
            flash("An error occurred while resetting your password.", "error")
            return redirect(url_for("forgot_password"))
    
    return render_template("auth/resetPassword.html", form=form, username=user.username)

if __name__ == '__main__':
    # Simplified runtime for basic HTTP development
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5500'))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    bind_host = os.getenv('FLASK_BIND', '127.0.0.1')

    # Ensure cookies are not set as secure so local HTTP works
    print(f"Running on http://{bind_host}:{port}")
    app.run(host=bind_host, debug=debug, port=port)