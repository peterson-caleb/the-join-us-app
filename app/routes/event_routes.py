# app/routes/event_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, g, Response
# BUGFIX: Added group_service to the imports to find the event owner
from .. import event_service, contact_service, sms_service, user_service, group_service
from datetime import datetime, timedelta
from bson import ObjectId
from flask_login import login_required, current_user
import pytz
from functools import wraps
from ..models.event import Event 

bp = Blueprint('events', __name__)

def require_active_group(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
      
        if not g.active_group:
            flash("Please select or create a group to continue.", "info")
            return redirect(url_for('groups.manage'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/events', methods=['GET', 'POST'])
@require_active_group
def manage_events():
    group_id = g.active_group._id
    
    if request.method == 'POST':
        try:
            expiry_hours_str = request.form.get('invitation_expiry_hours')
            event_data = {
                'name': request.form['name'],
                'date': request.form['date'],
                'capacity': int(request.form['capacity']),
                'details': request.form.get('details', ''),
                'location': request.form.get('location', ''),
                'start_time': request.form.get('start_time', ''),
                'invitation_expiry_hours': float(expiry_hours_str) if expiry_hours_str else None,
                'allow_rsvp_after_expiry': 'allow_rsvp_after_expiry' in request.form,
                'organizer_is_attending': 'organizer_is_attending' in request.form,
                'show_attendee_list': 'show_attendee_list' in request.form
            }
            event_service.create_event(event_data, group_id)
            flash('Event created successfully!', 'success')
        except ValueError:
            flash(f'Invalid input for capacity or expiry hours. Please enter a number.', 'error')
        except Exception as e:
            flash(f'Error creating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))
    
    show_past = request.args.get('show_past', 'false').lower() == 'true'
    events = event_service.get_events(group_id)
    
    now = datetime.now(pytz.UTC)
    today = now.date()
    
    for event in events:
        event['_id'] = str(event['_id'])

        # Create categorized lists of attendee names for the popover
        attendee_names_by_status = {
            'YES': [], 'NO': [], 'invited': [], 'pending': [], 'EXPIRED': [], 'ERROR': []
        }
        for i in event.get('invitees', []):
            status = i.get('status', 'pending')
            if status in attendee_names_by_status:
                attendee_names_by_status[status].append(i['name'])
        event['attendee_names_by_status'] = attendee_names_by_status
    
        date_val = event.get('date')
        if isinstance(date_val, str):
            try:
                event['date'] = datetime.strptime(date_val, '%Y-%m-%d')
            except (ValueError, TypeError):
                event['date'] = None

    if not show_past:
        events = [
            e for e in events if e.get('date') and e.get('date').date() >= today
        ]

    default_expiry_hours = current_app.config.get('INVITATION_EXPIRY_HOURS', 24)

    return render_template('events/list.html', events=events, now=now, show_past=show_past, default_expiry_hours=default_expiry_hours)


@bp.route('/events/<event_id>/edit', methods=['POST'])
@require_active_group
def edit_event(event_id):
    group_id = g.active_group._id
    try:
        event = event_service.get_event(group_id, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))

        expiry_hours_str = request.form.get('invitation_expiry_hours')
        event_data = {
            'name': request.form['name'],
            'date': request.form['date'],
            'capacity': int(request.form['capacity']),
            'details': request.form.get('details', ''),
            'location': request.form.get('location', ''),
            'start_time': request.form.get('start_time', ''),
            'invitation_expiry_hours': float(expiry_hours_str) if expiry_hours_str else None,
            'allow_rsvp_after_expiry': 'allow_rsvp_after_expiry' in request.form,
            'organizer_is_attending': 'organizer_is_attending' in request.form,
            'show_attendee_list': 'show_attendee_list' in request.form
        }
        
        event_service.update_event(group_id, event_id, event_data)
        flash('Event updated successfully!', 'success')
        
    except ValueError:
        flash('Invalid input for capacity or expiry hours. Please enter a number.', 'error')
    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
        
    return redirect(url_for('events.manage_events'))
    
@bp.route('/events/<event_id>/manual_rsvp/<invitee_id>', methods=['POST'])
@require_active_group
def manual_rsvp(event_id, invitee_id):
    group_id = g.active_group._id
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
    group_id = g.active_group._id
    owner_id = g.active_group.owner_id
    
    event = event_service.get_event(group_id, event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events.manage_events'))
    
    contacts = contact_service.get_contacts(owner_id)
    all_tags = contact_service.get_all_tags(owner_id)
    current_invitee_ids = list({invitee.get('contact_id') for invitee in event.invitees})
    
    return render_template(
        'events/manage_invitees.html',
        event=event,
        contacts=contacts,
        all_tags=all_tags,
        current_invitee_ids=current_invitee_ids
    )

@bp.route('/events/<event_id>/add_invitees', methods=['POST'])
@require_active_group
def add_invitees(event_id):
    group_id = g.active_group._id
    owner_id = g.active_group.owner_id
    selected_contact_ids = request.form.getlist('invitees_to_add')
    if not selected_contact_ids:
        flash('No invitees selected.', 'warning')
        return redirect(url_for('events.manage_invitees', event_id=event_id))

    try:
        invitees_to_add = [contact_service.get_contact(owner_id, cid) for cid in selected_contact_ids]
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
    group_id = g.active_group._id
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
    group_id = g.active_group._id
    try:
        new_order = request.json.get('invitee_order', [])
        event_service.reorder_invitees(group_id, event_id, new_order)
        return jsonify({'message': 'Order updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/events/<event_id>/delete_invitee/<invitee_id>', methods=['POST'])
@require_active_group
def delete_invitee(event_id, invitee_id):
    group_id = g.active_group._id
    try:
        event_service.delete_invitee(group_id, event_id, invitee_id)
        flash('Invitee removed successfully!', 'success')
    except Exception as e:
        flash(f'Error removing invitee: {str(e)}', 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/retry_invitee/<invitee_id>', methods=['POST'])
@require_active_group
def retry_invitee(event_id, invitee_id):
    group_id = g.active_group._id
    success, message = event_service.retry_invitation(group_id, event_id, invitee_id, sms_service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('events.manage_invitees', event_id=event_id))

@bp.route('/events/<event_id>/duplicate', methods=['POST'])
@require_active_group
def duplicate_event(event_id):
    group_id = g.active_group._id
    copy_invitees = 'copy_invitees' in request.form
    try:
        new_event_id = event_service.duplicate_event(group_id, event_id, copy_invitees=copy_invitees)
        
        if new_event_id:
            flash('Event duplicated successfully!', 'success')
            return redirect(url_for('events.manage_events') + f'?edit_event={new_event_id}')
        else:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
    except Exception as e:
        flash(f'Error duplicating event: {str(e)}', 'error')
        return redirect(url_for('events.manage_events'))

@bp.route('/events/<event_id>/archive', methods=['POST'])
@require_active_group
def archive_event(event_id):
    group_id = g.active_group._id
    try:
        if event_service.archive_event(group_id, event_id):
            flash('Event archived successfully!', 'success')
        else:
            flash('Event not found or could not be archived.', 'error')
    except Exception as e:
        flash(f'Error archiving event: {str(e)}', 'error')
    return redirect(url_for('events.manage_events'))

# NEW FEATURE: Send messages to event invitees
@bp.route('/events/<event_id>/send_message', methods=['POST'])
@require_active_group
def send_message(event_id):
    group_id = g.active_group._id
    try:
        event = event_service.get_event(group_id, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('events.manage_events'))
        
        # Get the message and recipient type from the form
        message_text = request.form.get('message_text', '').strip()
        recipient_type = request.form.get('recipient_type', 'confirmed')
        
        if not message_text:
            flash('Message cannot be empty.', 'error')
            return redirect(url_for('events.manage_invitees', event_id=event_id))
        
        if len(message_text) > 160:
            flash('Message exceeds 160 character limit.', 'error')
            return redirect(url_for('events.manage_invitees', event_id=event_id))
        
        # Prefix the message
        full_message = f"Event Msg: {message_text}"
        
        # Filter invitees based on recipient type
        if recipient_type == 'confirmed':
            recipients = [inv for inv in event.invitees if inv.get('status') == 'YES']
        else:  # 'all'
            recipients = [inv for inv in event.invitees if inv.get('status') in ['YES', 'invited', 'NO', 'EXPIRED']]
        
        if not recipients:
            flash('No recipients found matching the selected criteria.', 'warning')
            return redirect(url_for('events.manage_invitees', event_id=event_id))
        
        # Send messages
        success_count = 0
        failed_count = 0
        
        for invitee in recipients:
            success, error = sms_service.send_event_message(
                invitee['phone'], 
                full_message, 
                contact_id=invitee.get('contact_id'),
                event_id=event.get('_id'),
                group_id=event.get('group_id')
            )
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        # Save the message to the event for display on RSVP page
        if success_count > 0:
            event_service.add_message_to_event(
                group_id, 
                event_id, 
                message_text, 
                recipient_type,
                current_user.name
            )
        
        # Flash appropriate message
        if failed_count == 0:
            flash(f'Message sent successfully to {success_count} recipient(s)!', 'success')
        elif success_count == 0:
            flash(f'Failed to send message to all {failed_count} recipient(s).', 'error')
        else:
            flash(f'Message sent to {success_count} recipient(s), but failed for {failed_count}.', 'warning')
            
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
    
    return redirect(url_for('events.manage_invitees', event_id=event_id))

# --- Public RSVP URL Routes (Do NOT require login or group) ---
@bp.route('/rsvp/<token>', methods=['GET'])
def rsvp_page(token):
    event, invitee = event_service.find_event_and_invitee_by_token(token)
    if not event or not invitee:
        return render_template("events/rsvp_confirmation.html", success=False, message="This invitation link is invalid or has expired.")
    
    expiry_datetime_est = None
    if invitee.get('invited_at') and invitee.get('status') == 'invited':
        utc = pytz.timezone('UTC')
        est = pytz.timezone('US/Eastern')
        
        invited_at_utc = utc.localize(invitee['invited_at'])
        expiry_hours = event.invitation_expiry_hours or current_app.config.get('INVITATION_EXPIRY_HOURS', 24)
        expiry_datetime_utc = invited_at_utc + timedelta(hours=expiry_hours)
        expiry_datetime_est = expiry_datetime_utc.astimezone(est)

    confirmed_guests = []
    if event.show_attendee_list:
        confirmed_guests = [{'name': i['name'], 'is_host': False} for i in event.invitees if i.get('status') == 'YES']
        if event.organizer_is_attending:
            group = group_service.get_group(event.group_id)
            if group:
                owner = user_service.get_user(group.owner_id)
                if owner:
                    # Use the owner's full name
                    confirmed_guests.insert(0, {'name': owner.name, 'is_host': True})
    
    capacity_details = None
    if invitee.get('status') == 'YES':
        confirmed_count = sum(1 for i in event.invitees if i.get('status') == 'YES')
        capacity_details = {
            'confirmed': confirmed_count,
            'capacity': event.capacity,
            'organizer_attending': event.organizer_is_attending
        }

    # Get messages visible to this invitee
    visible_messages = event_service.get_visible_messages(event, invitee)

    return render_template(
        "events/rsvp_page.html", 
        event=event, 
        invitee=invitee, 
        token=token, 
        expiry_datetime_est=expiry_datetime_est,
        confirmed_guests=confirmed_guests,
        capacity_details=capacity_details,
        event_messages=visible_messages
    )

@bp.route('/api/rsvp/<token>', methods=['POST'])
def submit_rsvp_api(token):
    data = request.get_json()
    response = data.get('response')
    
    success, message, event = event_service.process_rsvp_from_url(token, response, sms_service)
    
    json_response = {'success': success, 'message': message}

    if success and event and response.upper() == 'YES':
        confirmed_count = sum(1 for i in event.invitees if i.get('status') == 'YES')
        json_response['capacity_details'] = {
            'confirmed': confirmed_count,
            'capacity': event.capacity,
            'organizer_attending': event.organizer_is_attending
        }
        if event.show_attendee_list:
            confirmed_guests = [{'name': i['name'], 'is_host': False} for i in event.invitees if i.get('status') == 'YES']
            if event.organizer_is_attending:
                group = group_service.get_group(event.group_id)
                if group:
                    owner = user_service.get_user(group.owner_id)
                    if owner:
                         # Use the owner's full name
                        confirmed_guests.insert(0, {'name': owner.name, 'is_host': True})
            json_response['confirmed_guests'] = confirmed_guests

    return jsonify(json_response)

@bp.route('/rsvp/submit/<token>/<response>', methods=['GET'])
def submit_rsvp(token, response):
    success, message, event = event_service.process_rsvp_from_url(token, response, sms_service)
    return render_template("events/rsvp_confirmation.html", success=success, message=message, event=event, invitee=None)

@bp.route('/event/<event_id>/calendar.ics')
def generate_ics(event_id):
    event_data = event_service.events_collection.find_one({"_id": ObjectId(event_id)})
    if not event_data:
        return "Event not found", 404

    event = Event.from_dict(event_data)
    
    now_utc_str = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    start_time_str = event.start_time or "09:00"
    try:
        start_dt_local = datetime.combine(event.date, datetime.strptime(start_time_str, '%H:%M').time())
    except (ValueError, TypeError):
        start_dt_local = datetime.now()

    end_dt_local = start_dt_local + timedelta(hours=2)

    start_dt_utc_str = start_dt_local.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
    end_dt_utc_str = end_dt_local.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')

    ics_content = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//JoinUs//RSVP App//EN",
        "BEGIN:VEVENT",
        f"UID:{event._id}@joinus.app", f"DTSTAMP:{now_utc_str}",
        f"DTSTART:{start_dt_utc_str}", f"DTEND:{end_dt_utc_str}",
        f"SUMMARY:{event.name}",
    ]
    if event.details:
        clean_details = event.details.replace('\r\n', '\\n').replace('\n', '\\n')
        ics_content.append(f"DESCRIPTION:{clean_details}")
    if event.location:
        ics_content.append(f"LOCATION:{event.location}")
    
    ics_content.extend(["END:VEVENT", "END:VCALENDAR"])
    
    response_body = "\r\n".join(ics_content)
    
    return Response(
        response_body,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment;filename={event.name.replace(' ', '_')}.ics"}
    )