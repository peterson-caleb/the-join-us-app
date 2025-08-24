# app/routes/group_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user
from .. import group_service, user_service, event_service

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
                success = user_service.create_group_for_user(current_user.id, group_name)
                if success:
                    # Refresh the user object to get the new active group
                    refreshed_user = user_service.get_user(current_user.id)
                    if refreshed_user:
                        login_user(refreshed_user, fresh=False)
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
            refreshed_user = user_service.get_user(current_user.id)
            if refreshed_user:
                login_user(refreshed_user, fresh=False)
            flash('Switched to a different group.', 'success')
        else:
            flash('Could not switch group.', 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')

    return redirect(request.referrer or url_for('home'))

@bp.route('/<group_id>/edit', methods=['POST'])
@login_required
def edit_group(group_id):
    new_name = request.form.get('name')
    if not new_name:
        flash('Group name cannot be empty.', 'error')
        return redirect(url_for('groups.manage'))
        
    try:
        success = group_service.update_group(group_id, current_user.id, {'name': new_name})
        if success:
            flash('Group updated successfully.', 'success')
        else:
            flash('Group not found or you do not have permission to edit it.', 'error')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        
    return redirect(url_for('groups.manage'))

@bp.route('/<group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group_to_delete = group_service.get_group(group_id)
    if not group_to_delete:
        flash('Group not found.', 'error')
        return redirect(url_for('groups.manage'))

    confirmation_text = request.form.get('confirmation_text')
    if confirmation_text != group_to_delete.name:
        flash('The confirmation text did not match the group name. Deletion cancelled.', 'error')
        return redirect(url_for('groups.manage'))

    try:
        # 1. Delete all events associated with the group
        deleted_events_count = event_service.delete_events_for_group(group_id, current_user.id)
        
        # 2. Delete the group itself
        success = group_service.delete_group(group_id, current_user.id)
        
        if success:
            flash(f"Group '{group_to_delete.name}' and its {deleted_events_count} events have been permanently deleted.", 'success')
            
            # 3. Check if the deleted group was the active one
            if current_user.active_group_id_str == group_id:
                user_service.switch_active_group(current_user.id, None) # This will auto-select a new one if available
                refreshed_user = user_service.get_user(current_user.id)
                if refreshed_user:
                    login_user(refreshed_user, fresh=False)
        else:
            flash('Group not found or you do not have permission to delete it.', 'error')
            
    except Exception as e:
        flash(f'An error occurred during deletion: {e}', 'error')
        
    return redirect(url_for('groups.manage'))
