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

# --- NEW ROUTES for invitations ---

@bp.route('/<group_id>/invite', methods=['POST'])
@login_required
def invite_member(group_id):
    email_to_invite = request.form.get('email')
    try:
        user_service.invite_user_to_group(current_user, email_to_invite, group_id)
        flash(f"Invitation sent to {email_to_invite}.", "success")
    except (ValueError, PermissionError) as e:
        flash(str(e), "error")
    except Exception:
        flash("An unexpected error occurred.", "error")
    return redirect(url_for('groups.manage'))

@bp.route('/invitations/<group_id>/accept', methods=['POST'])
@login_required
def accept_invitation(group_id):
    try:
        user_service.accept_group_invitation(current_user.id, group_id)
        flash("You have joined the group!", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for('groups.manage'))

@bp.route('/invitations/<group_id>/decline', methods=['POST'])
@login_required
def decline_invitation(group_id):
    try:
        user_service.decline_group_invitation(current_user.id, group_id)
        flash("Invitation declined.", "info")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for('home'))