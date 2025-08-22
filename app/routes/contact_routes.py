# app/routes/contact_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .. import contact_service, message_log_service
from flask_login import login_required, current_user
from functools import wraps

bp = Blueprint('contacts', __name__)

# --- Helper to ensure a group is active ---
def require_active_group(f):
    @wraps(f) # --- THIS LINE IS THE FIX ---
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.active_group_id:
            flash("Please select or create a group to continue.", "info")
            return redirect(url_for('groups.manage'))
        return f(*args, **kwargs)
    return decorated_function

# --- Public route, does NOT require login ---
@bp.route('/join', methods=['GET', 'POST'])
def join_list():
    flash("Public sign-ups are temporarily disabled.", "info")
    return render_template('contacts/join.html', disabled=True)

@bp.route('/join-success')
def join_success():
    return render_template('contacts/join_success.html')

# --- Admin-only routes ---
@bp.route('/master-list', methods=['GET', 'POST'])
@require_active_group
def manage_master_list():
    group_id = current_user.active_group_id
    if request.method == 'POST':
        contact_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        }
        try:
            contact_service.create_contact(contact_data, group_id)
            flash('Contact added successfully!', 'success')
        except ValueError as e:
            flash(str(e), 'error')
        return redirect(url_for('contacts.manage_master_list'))

    tag_filter = request.args.get('tags')
    filters = {}
    if tag_filter:
        filters['tags'] = {'$in': tag_filter.split(',')}

    contacts = contact_service.get_contacts(group_id, filters)
    all_tags = contact_service.get_all_tags(group_id)
    
    return render_template('contacts/list.html', 
                           master_list=contacts, 
                           all_tags=all_tags, 
                           selected_tags=tag_filter.split(',') if tag_filter else [])

@bp.route('/delete_contact/<contact_id>', methods=['POST'])
@require_active_group
def delete_contact(contact_id):
    group_id = current_user.active_group_id
    contact_service.delete_contact(group_id, contact_id)
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('contacts.manage_master_list'))

@bp.route('/edit_contact/<contact_id>', methods=['POST'])
@require_active_group
def edit_contact(contact_id):
    group_id = current_user.active_group_id
    contact_data = {
        'name': request.form['name'],
        'phone': request.form['phone'],
        'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
    }
    contact_service.update_contact(group_id, contact_id, contact_data)
    flash('Contact updated successfully!', 'success')
    return redirect(url_for('contacts.manage_master_list'))

@bp.route('/contact/<contact_id>/history')
@require_active_group
def message_history(contact_id):
    group_id = current_user.active_group_id
    contact = contact_service.get_contact(group_id, contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts.manage_master_list'))
        
    logs = message_log_service.get_logs_for_contact(group_id, contact_id)
    
    return render_template('contacts/history.html', contact=contact, logs=logs)