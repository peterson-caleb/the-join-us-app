# app/routes/contact_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .. import contact_service, message_log_service
from flask_login import login_required, current_user
from functools import wraps

bp = Blueprint('contacts', __name__)

# This decorator is no longer needed here because contacts are not group-dependent.
# We will use @login_required directly.

# --- Public route, does NOT require login ---
@bp.route('/join', methods=['GET', 'POST'])
def join_list():
    # This feature will be replaced by user-specific contact collection links
    flash("Public sign-ups are disabled.", "info")
    return render_template('contacts/join.html', disabled=True)

@bp.route('/join-success')
def join_success():
    return render_template('contacts/join_success.html')

# --- User-only routes for their own contacts ---
@bp.route('/my-contacts', methods=['GET', 'POST'])
@login_required
def manage_contacts():
    owner_id = current_user.id
    if request.method == 'POST':
        contact_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        }
        try:
            contact_service.create_contact(contact_data, owner_id)
            flash('Contact added successfully!', 'success')
        except ValueError as e:
            flash(str(e), 'error')
        return redirect(url_for('contacts.manage_contacts'))

    tag_filter = request.args.get('tags')
    filters = {}
    if tag_filter:
        filters['tags'] = {'$in': tag_filter.split(',')}

    contacts = contact_service.get_contacts(owner_id, filters)
    all_tags = contact_service.get_all_tags(owner_id)
    
    return render_template('contacts/list.html', 
                           contacts=contacts, 
                           all_tags=all_tags, 
                           selected_tags=tag_filter.split(',') if tag_filter else [])

@bp.route('/delete_contact/<contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    owner_id = current_user.id
    contact_service.delete_contact(owner_id, contact_id)
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('contacts.manage_contacts'))

@bp.route('/edit_contact/<contact_id>', methods=['POST'])
@login_required
def edit_contact(contact_id):
    owner_id = current_user.id
    try:
        contact_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        }
        contact_service.update_contact(owner_id, contact_id, contact_data)
        flash('Contact updated successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f"An error occurred while updating the contact: {str(e)}", "error")
    return redirect(url_for('contacts.manage_contacts'))

@bp.route('/contact/<contact_id>/history')
@login_required
def message_history(contact_id):
    # Note: Message logs are still associated with a group_id. This is acceptable
    # as it shows which group's event triggered the message. We are just fetching
    # the contact by the owner.
    owner_id = current_user.id
    contact = contact_service.get_contact(owner_id, contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts.manage_contacts'))
        
    # This logic may need to be revisited later if message logs should also be user-owned
    # For now, we find all logs sent to this contact's ID, regardless of group
    logs = message_log_service.get_logs_for_contact(contact_id)
    
    return render_template('contacts/history.html', contact=contact, logs=logs)