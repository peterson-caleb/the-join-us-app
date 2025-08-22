# app/routes/group_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import group_service, user_service

bp = Blueprint('groups', __name__, url_prefix='/groups')

@bp.route('/', methods=['GET', 'POST'])
@login_required
def manage():
    if request.method == 'POST':
        group_name = request.form.get('name')
        if not group_name:
            flash('Group name is required.', 'error')
        else:
            try:
                # This logic will be expanded later to handle invites
                group_id = group_service.create_group(group_name, current_user._id)
                # For now, we just create it but don't add the user yet
                flash(f"Group '{group_name}' created. Functionality to join/manage will be added soon.", 'success')
            except Exception as e:
                flash(f'Error creating group: {e}', 'error')
        return redirect(url_for('groups.manage'))

    # The user's groups are already available globally via the context processor
    return render_template('groups/manage.html')

@bp.route('/switch/<group_id>')
@login_required
def switch(group_id):
    try:
        success = user_service.switch_active_group(current_user.id, group_id)
        if success:
            flash('Switched to a different group.', 'success')
        else:
            flash('Could not switch group.', 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')

    # Redirect to the dashboard after switching
    return redirect(url_for('home'))