from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.transaction import Transaction
from app.mining import mining_system
from config import Config
import random
import string
from flask_mail import Message
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import mail
from app.forms import ForgotPasswordForm, ResetPasswordForm

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Registration attempt - Username: {username}, Email: {email}")  # Debug log
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Username {username} already exists")  # Debug log
            flash('Username already exists')
            return redirect(url_for('main.register'))
            
        if User.query.filter_by(email=email).first():
            print(f"Email {email} already registered")  # Debug log
            flash('Email already registered')
            return redirect(url_for('main.register'))
            
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
            print(f"User registered successfully - ID: {user.id}")  # Debug log
            flash('Registration successful! Please login.')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error registering user: {e}")  # Debug log
            flash('Error registering user')
            return redirect(url_for('main.register'))
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        print(f"Login attempt - Username: {username}")  # Debug log
        
        # Let's check the database directly
        all_users = User.query.all()
        print("All users in database:")  # Debug log
        for u in all_users:
            print(f"ID: {u.id}, Username: {u.username}")  # Debug log
        
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User found with ID: {user.id}")  # Debug log
            # Let's verify the stored password hash
            print(f"Stored password hash: {user.password_hash}")  # Debug log
            if user.check_password(password):
                print("Password check passed")  # Debug log
                login_user(user, remember=remember)
                user.is_active = True
                try:
                    db.session.commit()
                    print(f"Login successful for user: {username}")  # Debug log
                    return redirect(url_for('main.dashboard'))
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during login: {e}")  # Debug log
                    flash('Error updating user status')
                    return redirect(url_for('main.login'))
            else:
                print(f"Invalid password for user: {username}")  # Debug log
        else:
            print(f"No user found with username: {username}")  # Debug log
            
        flash('Invalid username or password')
    return render_template('login.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    active_users = mining_system.get_active_users_count()
    mining_rate = mining_system.calculate_mining_rate(active_users)
    transactions = Transaction.query.filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.timestamp.desc()).limit(10)
    
    return render_template('dashboard.html',
                         user=current_user,
                         mining_rate=mining_rate,
                         active_users=active_users,
                         transactions=transactions)

@bp.route('/transfer', methods=['POST'])
@login_required
def transfer():
    try:
        receiver_id = request.form.get('receiver_id')
        amount = float(request.form.get('amount'))
        
        # Clean up UUID format
        receiver_id = receiver_id.strip().replace(' ', '')
        
        if current_user.balance < amount:
            return jsonify({'error': 'Insufficient balance'}), 400
            
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'error': 'Receiver not found. Please check the ID and try again.'}), 404
            
        if receiver.id == current_user.id:
            return jsonify({'error': 'Cannot transfer to yourself'}), 400
            
        # Check if transfer would exceed max GADA for receiver
        if receiver.balance + amount > Config.MAX_GADA:
            return jsonify({'error': f'Transfer would exceed receiver\'s maximum limit of {Config.MAX_GADA} GADA'}), 400
            
        current_user.balance -= amount
        receiver.balance += amount
        
        transaction = Transaction(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            amount=amount
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully sent {amount:.2f} GADA to {receiver.username}'
        })
    except ValueError:
        return jsonify({'error': 'Please enter a valid amount'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Transfer failed. Please try again.'}), 500

@bp.route('/logout')
@login_required
def logout():
    current_user.is_active = False
    try:
        db.session.commit()
    except:
        db.session.rollback()
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/mining/start', methods=['POST'])
@login_required
def start_mining():
    current_user.is_mining = True
    current_user.mining_power = float(request.json.get('mining_power', 0.5))
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/mining/stop', methods=['POST'])
@login_required
def stop_mining():
    current_user.is_mining = False
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/mining/power', methods=['POST'])
@login_required
def update_mining_power():
    power = float(request.json.get('mining_power', 0.5))
    current_user.mining_power = power
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/mining/stats')
@login_required
def mining_stats():
    active_users = mining_system.get_active_users_count()
    mining_rate = mining_system.calculate_mining_rate(active_users)
    
    # Update user balance in database if mining
    if current_user.is_mining:
        mining_system.update_user_balance(current_user.id, mining_rate)
    
    # Get fresh balance from database
    db.session.refresh(current_user)
    
    return jsonify({
        'rate': mining_rate,
        'active_users': active_users,
        'current_balance': current_user.balance,
        'is_mining': current_user.is_mining,
        'mining_power': current_user.mining_power
    })

@bp.route('/active-users')
@login_required
def active_users():
    # Get all users instead of just active ones
    users = User.query.all()
    return render_template('active_users.html', users=users)

@bp.route('/user/<user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('main.dashboard'))
        
    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) | 
        (Transaction.receiver_id == user.id)
    ).order_by(Transaction.timestamp.desc()).limit(10)
    
    return render_template('user_profile.html', profile_user=user, transactions=transactions)

def generate_reset_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            reset_code = generate_reset_code()
            user.reset_code = reset_code
            user.reset_code_timestamp = datetime.utcnow()
            
            try:
                db.session.commit()
                
                # Send email
                msg = Message('Password Reset Request',
                            recipients=[user.email])
                msg.body = f'''To reset your password, use this code: {reset_code}

This code will expire in 1 hour.

If you did not make this request, please ignore this email.
'''
                mail.send(msg)
                flash('An email has been sent with instructions to reset your password.', 'success')
                return redirect(url_for('main.reset_password'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'error')
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('forgot_password.html', form=form)

@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(reset_code=form.code.data).first()
        
        if user and user.reset_code_timestamp:
            # Check if code is still valid (1 hour)
            if datetime.utcnow() - user.reset_code_timestamp < timedelta(hours=1):
                user.set_password(form.new_password.data)
                user.reset_code = None
                user.reset_code_timestamp = None
                
                try:
                    db.session.commit()
                    flash('Your password has been updated! You can now log in.', 'success')
                    return redirect(url_for('main.login'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred. Please try again.', 'error')
            else:
                flash('This reset code has expired. Please request a new one.', 'error')
        else:
            flash('Invalid reset code.', 'error')
            
    return render_template('reset_password.html', form=form)

@bp.route('/qr/payment/<user_id>', methods=['GET'])
@login_required
def qr_payment(user_id):
    receiver = User.query.get(user_id)
    if not receiver:
        abort(404)
    
    return render_template('qr_payment.html', receiver=receiver)

@bp.route('/qr/validate/<user_id>')
@login_required
def validate_qr(user_id):
    receiver = User.query.get(user_id)
    if not receiver:
        return jsonify({'error': 'Invalid QR code'}), 404
    
    return jsonify({
        'username': receiver.username,
        'id': receiver.id
    }) 