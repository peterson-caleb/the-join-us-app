# app/routes/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from .. import group_service, user_service

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator to ensure user is an admin
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
    all_groups = group_service.get_all_groups_with_owners()
    current_user_group_ids = [gm['group_id'] for gm in current_user.group_memberships]
    return render_template('admin/system_panel.html', 
                           all_groups=all_groups,
                           current_user_group_ids=current_user_group_ids)

@bp.route('/groups/join/<group_id>', methods=['POST'])
@admin_required
def admin_join_group(group_id):
    try:
        user_service.add_admin_to_group(current_user.id, group_id)
        flash("You have successfully joined the group.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for('admin.system_panel'))