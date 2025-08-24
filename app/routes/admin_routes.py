# app/routes/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from functools import wraps
from .. import group_service, user_service, admin_dashboard_service, system_settings_service

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

@bp.route('/view_group/<group_id>', methods=['POST'])
@admin_required
def view_group_as_admin(group_id):
    group = group_service.get_group(group_id)
    if not group:
        flash("Group not found.", "error")
        return redirect(url_for('admin.system_panel'))
    
    # Store the group ID we want to view in the session
    session['viewing_group_id'] = group_id
    flash(f"You are now viewing the system as the owner of '{group.name}'.", "info")
    return redirect(url_for('events.manage_events')) # Redirect to a common page

@bp.route('/exit_view_mode', methods=['POST'])
@admin_required
def exit_view_mode():
    if 'viewing_group_id' in session:
        session.pop('viewing_group_id')
        flash("You have returned to your normal administrator view.", "info")
    return redirect(url_for('admin.system_panel'))

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def platform_settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            system_settings_service.update_setting(key, value)
        flash("Platform settings updated successfully.", "success")
        return redirect(url_for('admin.platform_settings'))

    settings = system_settings_service.get_all_settings()
    return render_template('admin/settings.html', settings=settings)