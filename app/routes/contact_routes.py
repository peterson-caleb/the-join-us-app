# app/routes/contact_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .. import contact_service, message_log_service
from flask_login import login_required

bp = Blueprint('contacts', __name__)

# --- NEW PUBLIC ROUTE FOR JOINING THE CONTACT LIST ---
@bp.route('/join', methods=['GET', 'POST'])
def join_list():
    if request.method == 'POST':
        try:
            contact_data = {
                'name': request.form['name'],
                'phone': request.form['phone'],
                'tags': [] # Tags are not set on public registration
            }
            contact_service.create_contact(contact_data)
            # Redirect to a success page after successful sign-up
            return redirect(url_for('contacts.join_success'))
        except ValueError as e:
            # Catch duplicate phone number error from the service
            flash(str(e), 'error')
        except Exception as e:
            # Catch any other unexpected errors
            flash('An unexpected error occurred. Please try again.', 'error')
            
    return render_template('contacts/join.html')

# --- NEW SUCCESS PAGE ROUTE ---
@bp.route('/join-success')
def join_success():
    return render_template('contacts/join_success.html')


# --- EXISTING ADMIN-ONLY ROUTES ---
@bp.route('/master-list', methods=['GET', 'POST'])
@login_required
def manage_master_list():
    if request.method == 'POST':
        contact_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        }
        try:
            contact_service.create_contact(contact_data)
            flash('Contact added successfully!', 'success')
        except ValueError as e:
            flash(str(e), 'error')
        return redirect(url_for('contacts.manage_master_list'))

    tag_filter = request.args.get('tags')
    filters = {}
    if tag_filter:
        filters['tags'] = {'$in': tag_filter.split(',')}

    contacts = contact_service.get_contacts(filters)
    all_tags = contact_service.get_all_tags()
    
    return render_template('contacts/list.html', 
                           master_list=contacts, 
                           all_tags=all_tags, 
                           selected_tags=tag_filter.split(',') if tag_filter else [])

@bp.route('/delete_contact/<contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact_service.delete_contact(contact_id)
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('contacts.manage_master_list'))

@bp.route('/edit_contact/<contact_id>', methods=['POST'])
@login_required
def edit_contact(contact_id):
    contact_data = {
        'name': request.form['name'],
        'phone': request.form['phone'],
        'tags': [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
    }
    contact_service.update_contact(contact_id, contact_data)
    flash('Contact updated successfully!', 'success')
    return redirect(url_for('contacts.manage_master_list'))

@bp.route('/contact/<contact_id>/history')
@login_required
def message_history(contact_id):
    contact = contact_service.get_contact(contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts.manage_master_list'))
        
    logs = message_log_service.get_logs_for_contact(contact_id)
    
    return render_template('contacts/history.html', contact=contact, logs=logs)