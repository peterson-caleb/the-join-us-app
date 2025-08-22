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
                # --- THIS LOGIC IS CORRECTED ---
                # Call the new service method that handles both creating the group
                # and adding the user as the owner.
                success = user_service.create_group_for_user(current_user.id, group_name)
                if success:
                    flash(f"Group '{group_name}' created and is now your active group.", 'success')
                else:
                    flash('Could not create group.', 'error')

            except Exception as e:
                flash(f'Error creating group: {e}', 'error')
        return redirect(url_for('groups.manage'))

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

    return redirect(url_for('home'))