# app/routes/event_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .. import event_service, contact_service, sms_service
from datetime import datetime
from bson import ObjectId
from flask_login import login_required, current_user
import pytz

bp = Blueprint('events', __name__)

# --- NEW: Helper to ensure a group is active ---
def require_active_group(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.active_group_id:
            flash("Please select or create a group to continue.", "info")
            return redirect(url_for('groups.manage'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/events', methods=['GET', 'POST'])
@require_active_group
def manage_events():
    group_id = current_user.active_group_id
    
    if request.method == 'POST':
        try:
            event_data = {
                'name': request.form['name'],
                'date': request.form['date'],
                'capacity': int(request.form['capacity']),
                'details': request.form.get('details', '')
            }
            event_service.create_event(event_data, group_id)
            flash('Event created successfully!', 'success')
        except ValueError as e:
            flash(f'Error creating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))
    
    show_past = request.args.get('show_past', 'false').lower() == 'true'
    events = event_service.get_events(group_id)
    
    now = datetime.now(pytz.UTC)
    today = now.date()
    
    if not show_past:
        filtered_events = []
        for event in events:
            event_date = event.get('date')
            if isinstance(event_date, str):
                try:
                    event_date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
                    if event_date_obj >= today:
                        filtered_events.append(event)
                except ValueError:
                    filtered_events.append(event)
            elif isinstance(event_date, datetime):
                if event_date.date() >= today:
                    filtered_events.append(event)
            else:
                filtered_events.append(event)
        events = filtered_events
    
    for event in events:
        event['_id'] = str(event['_id'])
        if isinstance(event.get('date'), str):
            try:
                event['date'] = datetime.strptime(event['date'], '%Y-%m-%d')
            except ValueError:
                event['date'] = None
    
    return render_template('events/list.html', events=events, now=now, show_past=show_past)

@bp.route('/events/<event_id>/edit', methods=['POST'])
@require_active_group
def edit_event(event_id):
    group_id = current_user.active_group_id
    try:
        event = event_service.get_event(group_id, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))

        event_data = {
            'name': request.form['name'],
            'date': request.form['date'],
            'capacity': int(request.form['capacity']),
            'details': request.form.get('details', '')
        }
        
        event_service.update_event(group_id, event_id, event_data)
        flash('Event updated successfully!', 'success')
        
    except ValueError:
        flash('Invalid capacity value. Please enter a number.', 'error')
    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
        
    return redirect(url_for('events.manage_events'))
    
@bp.route('/events/<event_id>/manual_rsvp/<invitee_id>', methods=['POST'])
@require_active_group
def manual_rsvp(event_id, invitee_id):
    group_id = current_user.active_group_id
    new_status = request.form.get('status')
    if not new_status:
        flash('No status provided.', 'error')
        return redirect(url_for('events.manage_invitees', event_id=event_id))

    success, message = event_service.manual_rsvp(group_id, event_id, invitee_id, new_status, sms_service)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
        
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/invitees', methods=['GET'])
@require_active_group
def manage_invitees(event_id):
    group_id = current_user.active_group_id
    event = event_service.get_event(group_id, event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events.manage_events'))
    
    contacts = contact_service.get_contacts(group_id)
    current_invitee_ids = {invitee.get('contact_id') for invitee in event.invitees}
    
    return render_template(
        'events/manage_invitees.html',
        event=event,
        contacts=contacts,
        current_invitee_ids=current_invitee_ids
    )

@bp.route('/events/<event_id>/add_invitees', methods=['POST'])
@require_active_group
def add_invitees(event_id):
    group_id = current_user.active_group_id
    selected_contact_ids = request.form.getlist('invitees_to_add')
    if not selected_contact_ids:
        flash('No invitees selected.', 'warning')
        return redirect(url_for('events.manage_invitees', event_id=event_id))
    try:
        invitees_to_add = [contact_service.get_contact(group_id, cid) for cid in selected_contact_ids]
        added_count = event_service.add_invitees(group_id, event_id, invitees_to_add)
        
        if added_count > 0:
            flash(f'{added_count} new invitees added successfully!', 'success')
        else:
            flash('No new invitees were added (they may already be on the list).', 'info')
    except Exception as e:
        flash(f'Error adding invitees: {str(e)}', 'error')
    
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/toggle_automation', methods=['POST'])
@require_active_group
def toggle_automation(event_id):
    group_id = current_user.active_group_id
    try:
        event = event_service.get_event(group_id, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
        new_status = 'active' if event.automation_status == 'paused' else 'paused'
        event_service.update_event(group_id, event_id, {'automation_status': new_status})
        flash(f'Event automation has been set to {new_status}.', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/reorder_invitees', methods=['POST'])
@require_active_group
def reorder_invitees(event_id):
    group_id = current_user.active_group_id
    try:
        new_order = request.json.get('invitee_order', [])
        event_service.reorder_invitees(group_id, event_id, new_order)
        return jsonify({'message': 'Order updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/events/<event_id>/delete_invitee/<invitee_id>', methods=['POST'])
@require_active_group
def delete_invitee(event_id, invitee_id):
    group_id = current_user.active_group_id
    try:
        event_service.delete_invitee(group_id, event_id, invitee_id)
        flash('Invitee removed successfully!', 'success')
    except Exception as e:
        flash(f'Error removing invitee: {str(e)}', 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/retry_invitee/<invitee_id>', methods=['POST'])
@require_active_group
def retry_invitee(event_id, invitee_id):
    group_id = current_user.active_group_id
    success, message = event_service.retry_invitation(group_id, event_id, invitee_id, sms_service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/duplicate', methods=['POST'])
@require_active_group
def duplicate_event(event_id):
    group_id = current_user.active_group_id
    try:
        event = event_service.get_event(group_id, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
        duplicate_data = {
            'name': f"COPY - {event.name}",
            'date': event.date.strftime('%Y-%m-%d') if hasattr(event.date, 'strftime') else event.date,
            'capacity': event.capacity,
            'details': event.details or '',
            'automation_status': 'paused'
        }
        
        new_event_id = event_service.create_event(duplicate_data, group_id)
        
        flash('Event duplicated successfully!', 'success')
        return redirect(url_for('events.manage_events') + f'?edit_event={new_event_id}')
        
    except Exception as e:
        flash(f'Error duplicating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))

@bp.route('/events/<event_id>/delete', methods=['POST'])
@require_active_group
def delete_event(event_id):
    group_id = current_user.active_group_id
    try:
        if event_service.delete_event(group_id, event_id):
            flash('Event deleted successfully!', 'success')
        else:
            flash('Event not found.', 'error')
    except Exception as e:
        flash(f'Error deleting event: {str(e)}', 'error')
    return redirect(url_for('events.manage_events'))

# --- Public RSVP URL Routes (Do NOT require login or group) ---
@bp.route('/rsvp/<token>', methods=['GET'])
def rsvp_page(token):
    event, invitee = event_service.find_event_and_invitee_by_token(token)
    if not event or not invitee:
        return render_template("events/rsvp_confirmation.html", success=False, message="This invitation link is invalid or has expired.")
    if invitee['status'] not in ['invited', 'ERROR']:
        return render_template("events/rsvp_confirmation.html", success=True, message="Thank you, we have already received your response.")
    return render_template("events/rsvp_page.html", event=event, invitee=invitee, token=token)

@bp.route('/rsvp/submit/<token>/<response>', methods=['GET'])
def submit_rsvp(token, response):
    success, message = event_service.process_rsvp_from_url(token, response, sms_service)
    event, invitee = event_service.find_event_and_invitee_by_token(token)
    return render_template("events/rsvp_confirmation.html", success=success, message=message, event=event, invitee=invitee)