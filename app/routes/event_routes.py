# app/routes/event_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .. import event_service, contact_service
from datetime import datetime
from bson import ObjectId
from flask_login import login_required
import pytz
import json

bp = Blueprint('events', __name__)

@bp.route('/events', methods=['GET', 'POST'])
@login_required
def manage_events():
    if request.method == 'POST':
        try:
            event_data = {
                'name': request.form['name'],
                'date': request.form['date'],
                'capacity': int(request.form['capacity']),
                'details': request.form.get('details', '')
            }
            event_service.create_event(event_data)
            flash('Event created successfully!', 'success')
        except ValueError as e:
            flash(f'Error creating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))
    
    show_past = request.args.get('show_past', 'false').lower() == 'true'
    events = event_service.get_events()
    
    now = datetime.now(pytz.UTC)
    today = now.date()
    
    # Filter events based on show_past parameter
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
                    # If date parsing fails, include the event to be safe
                    filtered_events.append(event)
            elif isinstance(event_date, datetime):
                if event_date.date() >= today:
                    filtered_events.append(event)
            else:
                # Include events with invalid dates to be safe
                filtered_events.append(event)
        events = filtered_events
    
    for event in events:
        event['_id'] = str(event['_id'])
        # --- MODIFICATION START ---
        # Ensure date is a datetime object for formatting in Jinja
        if isinstance(event.get('date'), str):
            try:
                event['date'] = datetime.strptime(event['date'], '%Y-%m-%d')
            except ValueError:
                event['date'] = None # Handle invalid date strings
        # --- MODIFICATION END ---
    
    return render_template('events/list.html', events=events, now=now, show_past=show_past)

@bp.route('/events/<event_id>/edit', methods=['POST'])
@login_required
def edit_event(event_id):
    """Update an existing event's details."""
    try:
        event = event_service.get_event(event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))

        event_data = {
            'name': request.form['name'],
            'date': request.form['date'],
            'capacity': int(request.form['capacity']),
            'details': request.form.get('details', '')
        }
        
        event_service.update_event(event_id, event_data)
        flash('Event updated successfully!', 'success')
        
    except ValueError:
        flash('Invalid capacity value. Please enter a number.', 'error')
    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
        
    return redirect(url_for('events.manage_events'))

@bp.route('/events/<event_id>/invitees', methods=['GET'])
@login_required
def manage_invitees(event_id):
    event = event_service.get_event(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events.manage_events'))
    
    contacts = contact_service.get_contacts()
    current_invitee_ids = {invitee.get('contact_id') for invitee in event.invitees}
    
    return render_template(
        'events/manage_invitees.html',
        event=event,
        contacts=contacts,
        current_invitee_ids=current_invitee_ids
    )

@bp.route('/events/<event_id>/add_invitees', methods=['POST'])
@login_required
def add_invitees(event_id):
    selected_contact_ids = request.form.getlist('invitees_to_add')
    if not selected_contact_ids:
        flash('No invitees selected.', 'warning')
        return redirect(url_for('events.manage_invitees', event_id=event_id))
    try:
        invitees_to_add = [contact_service.get_contact(cid) for cid in selected_contact_ids]
        added_count = event_service.add_invitees(event_id, invitees_to_add)
        
        if added_count > 0:
            flash(f'{added_count} new invitees added successfully!', 'success')
        else:
            flash('No new invitees were added (they may already be on the list).', 'info')
    except Exception as e:
        flash(f'Error adding invitees: {str(e)}', 'error')
    
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/toggle_automation', methods=['POST'])
@login_required
def toggle_automation(event_id):
    try:
        event = event_service.get_event(event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
        new_status = 'active' if event.automation_status == 'paused' else 'paused'
        event_service.update_event(event_id, {'automation_status': new_status})
        flash(f'Event automation has been set to {new_status}.', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/reorder_invitees', methods=['POST'])
@login_required
def reorder_invitees(event_id):
    try:
        new_order = request.json.get('invitee_order', [])
        event_service.reorder_invitees(event_id, new_order)
        return jsonify({'message': 'Order updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/events/<event_id>/delete_invitee/<invitee_id>', methods=['POST'])
@login_required
def delete_invitee(event_id, invitee_id):
    try:
        event_service.delete_invitee(event_id, invitee_id)
        flash('Invitee removed successfully!', 'success')
    except Exception as e:
        flash(f'Error removing invitee: {str(e)}', 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/retry_invitee/<invitee_id>', methods=['POST'])
@login_required
def retry_invitee(event_id, invitee_id):
    """Manually retries sending an invitation to a specific invitee."""
    success, message = event_service.retry_invitation(event_id, invitee_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/duplicate', methods=['POST'])
@login_required
def duplicate_event(event_id):
    """Duplicate an existing event."""
    try:
        event = event_service.get_event(event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
        # Create duplicate event data without invitees
        duplicate_data = {
            'name': f"COPY - {event.name}",
            'date': event.date.strftime('%Y-%m-%d') if hasattr(event.date, 'strftime') else event.date,
            'capacity': event.capacity,
            'details': event.details or '',
            'automation_status': 'paused'
        }
        
        # Create the duplicate event
        new_event_id = event_service.create_event(duplicate_data)
        
        flash('Event duplicated successfully!', 'success')
        return redirect(url_for('events.manage_events') + f'?edit_event={new_event_id}')
        
    except Exception as e:
        flash(f'Error duplicating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))

@bp.route('/events/<event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete an entire event."""
    try:
        if event_service.delete_event(event_id):
            flash('Event deleted successfully!', 'success')
        else:
            flash('Event not found.', 'error')
    except Exception as e:
        flash(f'Error deleting event: {str(e)}', 'error')
    return redirect(url_for('events.manage_events'))

# --- RSVP URL Routes ---
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
    success, message = event_service.process_rsvp_from_url(token, response)
    event, invitee = event_service.find_event_and_invitee_by_token(token)
    return render_template("events/rsvp_confirmation.html", success=success, message=message, event=event, invitee=invitee)