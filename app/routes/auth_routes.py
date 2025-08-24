# app/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .. import user_service, registration_code_service

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = user_service.get_user_by_email(email)
        if user and user_service.verify_password(user, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Check for a code in the URL query parameters
    code_from_url = request.args.get('code')
    is_code_valid = registration_code_service.validate_code(code_from_url)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Use the code from the hidden input if it exists, otherwise from the form
        invitation_code = request.form.get('invitation_code_hidden') or request.form.get('invitation_code')
        
        try:
            if not registration_code_service.validate_code(invitation_code):
                flash('Invalid or expired invitation code.', 'error')
                # Pass the invalid code back to the template if it came from URL
                return render_template('auth/register.html', code_from_url=code_from_url, is_code_valid=False)
            
            user = user_service.create_user(
                username=username,
                email=email,
                password=password,
                registration_method='invite_code'
            )
            
            registration_code_service.use_code(invitation_code)
            
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('home'))
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('An error occurred during registration.', 'error')
    
    return render_template('auth/register.html', code_from_url=code_from_url, is_code_valid=is_code_valid)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/admin/invitation-codes', methods=['GET', 'POST'])
@login_required
def manage_invitation_codes():
    if not current_user.is_admin:
        flash('Unauthorized access', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        expires_in_days = int(request.form.get('expires_in_days', 7))
        max_uses = int(request.form.get('max_uses', 1))
        
        code = registration_code_service.create_code(
            created_by_user_id=current_user.id,
            expires_in_days=expires_in_days,
            max_uses=max_uses
        )
        flash(f'New invitation code created: {code}', 'success')
    
    active_codes = registration_code_service.list_active_codes()
    return render_template('auth/invitation_codes.html', codes=active_codes)
