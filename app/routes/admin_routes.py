# app/routes/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from .. import group_service, user_service, admin_dashboard_service

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/system-panel')
@admin_required
def system_panel():
    all_groups = user_service.get_all_groups_with_owners()
    return render_template('admin/system_panel.html', all_groups=all_groups)

@bp.route('/global-dashboard')
@admin_required
def global_dashboard():
    stats = admin_dashboard_service.get_global_stats()
    return render_template('admin/global_dashboard.html', stats=stats)

@bp.route('/users')
@admin_required
def manage_users():
    users = admin_dashboard_service.get_all_users_with_details()
    return render_template('admin/users.html', users=users)