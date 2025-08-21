# app/services/event_service.py
from datetime import datetime, timedelta
from bson import ObjectId
from ..models.event import Event
import logging
from logging.handlers import RotatingFileHandler
import os
import pytz
import secrets

class EventService:
    # ... (init, logging, and other methods are unchanged) ...
    def __init__(self, db, sms_service=None, invitation_expiry_hours=24):
        self.db = db
        self.events_collection = db['events']
        self.sms_service = sms_service
        self.invitation_expiry_hours = invitation_expiry_hours
        self.timezone = pytz.timezone('UTC')
        
        self.logger = self._setup_logging()

    def _setup_logging(self):
        logger = logging.getLogger('event_service')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            if not os.path.exists('logs'):
                os.makedirs('logs')

            file_handler = RotatingFileHandler('logs/event_service.log', maxBytes=1024 * 1024, backupCount=5)
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        return logger

    def get_current_time(self):
        return datetime.now(self.timezone)
        
    def _send_invitations(self, event, invitees_to_send):
        now = self.get_current_time()
        
        for invitee in invitees_to_send:
            invitee['rsvp_token'] = secrets.token_urlsafe(16)
            
            # MODIFIED: Unpack the new tuple return value
            success, reason = self.sms_service.send_invitation(invitee, event.to_dict())
            
            update_fields = {
                "invitees.$.rsvp_token": invitee['rsvp_token']
            }

            if success:
                update_fields["invitees.$.status"] = "invited"
                update_fields["invitees.$.invited_at"] = now
                update_fields["invitees.$.error_message"] = None # Clear any previous error
                self.logger.info(f"Successfully sent invitation to {invitee['phone']}")
            else:
                update_fields["invitees.$.status"] = "ERROR"
                # MODIFIED: Store the failure reason in the database
                update_fields["invitees.$.error_message"] = reason 
                self.logger.error(f"Failed to send invitation to {invitee['phone']}: {reason}")

            self.events_collection.update_one(
                {"_id": event._id, "invitees._id": invitee['_id']},
                {"$set": update_fields}
            )
            
    # --- NEW METHOD START ---
    def manual_rsvp(self, event_id, invitee_id, new_status):
        """
        Allows a host to manually set an invitee's RSVP status.
        Triggers a confirmation SMS if the status is set to 'YES'.
        """
        event = self.get_event(event_id)
        if not event:
            return False, "Event not found."

        invitee = next((i for i in event.invitees if str(i.get('_id')) == invitee_id), None)
        if not invitee:
            return False, "Invitee not found in this event."

        # Update the status in the database
        success = self.update_invitee_status(event_id, ObjectId(invitee_id), new_status)
        if not success:
            return False, "Failed to update status in the database."

        # If confirmed, send the confirmation SMS to the guest
        if new_status == 'YES':
            self.sms_service.send_confirmation(invitee, event.to_dict())
            message = f"Successfully confirmed {invitee.get('name')}. A confirmation SMS has been sent to them."
        else:
            message = f"Successfully marked {invitee.get('name')} as declined."
            
        return True, message
    # --- NEW METHOD END ---

    def process_expired_invitations(self):
        self.logger.info("Starting expired invitations check (process_expired_invitations)")
        now = self.get_current_time()
        expiry_threshold = now - timedelta(hours=self.invitation_expiry_hours)

        self.events_collection.update_many(
            {
                "automation_status": "active",
                "invitees": {
                    "$elemMatch": {
                        "status": "invited",
                        "invited_at": {"$lt": expiry_threshold}
                    }
                }
            },
            {
                "$set": {
                    "invitees.$[elem].status": "EXPIRED",
                    "invitees.$[elem].expired_at": now
                }
            },
            array_filters=[
                {"elem.status": "invited", "elem.invited_at": {"$lt": expiry_threshold}}
            ]
        )
        self.logger.info("Completed expired invitations check.")

    def manage_event_capacity(self):
        self.logger.info("Starting event capacity management")
        events = self.events_collection.find({"automation_status": "active"})
        for event_data in events:
            try:
                event = Event.from_dict(event_data)
                available_spots = self._calculate_available_spots(event)
                if available_spots > 0:
                    next_invitees = self._get_next_invitees(event, available_spots)
                    if next_invitees:
                        self._send_invitations(event, next_invitees)
            except Exception as e:
                self.logger.error(f"Error managing capacity for event {event_data.get('_id')}: {str(e)}")

    def _calculate_available_spots(self, event):
        confirmed_count = sum(1 for i in event.invitees if i.get('status') == 'YES')
        invited_count = sum(1 for i in event.invitees if i.get('status') == 'invited')
        return event.capacity - (confirmed_count + invited_count)

    def _get_next_invitees(self, event, limit):
        pending_invitees = [i for i in event.invitees if i.get('status') == 'pending']
        pending_invitees.sort(key=lambda x: x.get('priority', float('inf')))
        return pending_invitees[:limit]

    def send_pending_reminders(self):
        self.logger.info("Running send_pending_reminders job (no action taken).")
        pass
    
    def process_rsvp_from_url(self, token, response):
        event, invitee = self.find_event_and_invitee_by_token(token)
        if not event or not invitee: return False, "This invitation link is invalid."
        if invitee['status'] not in ['invited', 'ERROR']: return True, "You have already responded."
        response = response.upper()
        if response not in ['YES', 'NO']: return False, "Invalid response provided."
        
        success = self.update_invitee_status(event._id, invitee['_id'], response)
        
        if success and response == 'YES':
            self.sms_service.send_confirmation(invitee, event.to_dict())

        return success, f"Thank you! Your response for {event.name} has been recorded."

    def update_invitee_status(self, event_id, invitee_id, status):
        result = self.events_collection.update_one(
            {"_id": ObjectId(event_id), "invitees._id": ObjectId(invitee_id)},
            {"$set": {
                "invitees.$.status": status,
                "invitees.$.responded_at": self.get_current_time()
            }}
        )
        return result.modified_count > 0

    def find_event_and_invitee_by_token(self, token):
        event_data = self.events_collection.find_one({"invitees.rsvp_token": token})
        if not event_data: return None, None
        event = Event.from_dict(event_data)
        invitee = next((i for i in event.invitees if i.get("rsvp_token") == token), None)
        return event, invitee

    def get_event(self, event_id):
        event_data = self.events_collection.find_one({"_id": ObjectId(event_id)})
        return Event.from_dict(event_data) if event_data else None

    def get_events(self):
        return list(self.events_collection.find())

    def create_event(self, event_data):
        event = Event.from_dict(event_data, invitation_expiry_hours=self.invitation_expiry_hours)
        result = self.events_collection.insert_one(event.to_dict())
        return str(result.inserted_id)

    def update_event(self, event_id, event_data):
        self.events_collection.update_one({"_id": ObjectId(event_id)}, {"$set": event_data})
        return self.get_event(event_id)

    def delete_event(self, event_id):
        result = self.events_collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count > 0

    def add_invitees(self, event_id, invitees):
        event = self.get_event(event_id)
        if not event:
            raise ValueError("Event not found")
        current_contact_ids = {str(i.get('contact_id')) for i in event.invitees}
        start_priority = max([i.get('priority', -1) for i in event.invitees] + [-1]) + 1
        
        newly_added_count = 0
        new_invitees_to_add = []
        
        for invitee_data in invitees:
            contact_id_str = str(invitee_data['_id'])
            if contact_id_str not in current_contact_ids:
                new_invitee = {
                    "_id": ObjectId(), "name": invitee_data['name'], "phone": invitee_data['phone'],
                    "status": "pending", "priority": start_priority + newly_added_count,
                    "added_at": self.get_current_time(), "contact_id": contact_id_str
                }
                new_invitees_to_add.append(new_invitee)
                current_contact_ids.add(contact_id_str)
                newly_added_count += 1
        if newly_added_count > 0:
            self.events_collection.update_one(
                {"_id": ObjectId(event_id)},
                {"$push": {"invitees": {"$each": new_invitees_to_add}}}
            )
        return newly_added_count

    def delete_invitee(self, event_id, invitee_id):
        self.events_collection.update_one({"_id": ObjectId(event_id)}, {"$pull": {"invitees": {"_id": ObjectId(invitee_id)}}})

    def reorder_invitees(self, event_id, invitee_order):
        event = self.get_event(event_id)
        if not event: raise ValueError("Event not found")
        invitees_dict = {str(i['_id']): i for i in event.invitees}
        new_invitees = []
        for i, invitee_id in enumerate(invitee_order):
            if invitee_id in invitees_dict:
                invitee = invitees_dict[invitee_id]
                invitee['priority'] = i
                new_invitees.append(invitee)
        self.update_event(event_id, {"invitees": new_invitees})
        return new_invitees
    
    def retry_invitation(self, event_id, invitee_id):
        """
        Finds a specific invitee marked as 'ERROR' and re-attempts to send their invitation.
        """
        # Find the event and the specific invitee in one query for efficiency
        event_data = self.events_collection.find_one(
            {"_id": ObjectId(event_id), "invitees._id": ObjectId(invitee_id)},
            {"invitees.$": 1}  # Projection to get only the matched invitee
        )
        if not event_data or not event_data.get('invitees'):
            return False, "Invitee or event not found."

        invitee = event_data['invitees'][0]
        
        # We need the full event object to pass to the SMS service
        event = self.get_event(event_id)

        if invitee.get('status') != 'ERROR':
            return False, f"Cannot retry for {invitee.get('name')}. Their status is not 'ERROR'."

        # Generate a new token for the new invitation link
        invitee['rsvp_token'] = secrets.token_urlsafe(16)
        
        # Call the SMS service to resend the invitation
        success, reason = self.sms_service.send_invitation(invitee, event.to_dict())

        # Prepare the database update based on the result
        update_fields = {"invitees.$.rsvp_token": invitee['rsvp_token']}
        if success:
            update_fields["invitees.$.status"] = "invited"
            update_fields["invitees.$.invited_at"] = self.get_current_time()
            update_fields["invitees.$.error_message"] = None  # Clear the old error
            message = f"Invitation for {invitee.get('name')} was successfully resent."
        else:
            update_fields["invitees.$.error_message"] = reason  # Update with the new error
            message = f"Failed to resend invitation for {invitee.get('name')}: {reason}"

        # Apply the update to the database
        self.events_collection.update_one(
            {"_id": ObjectId(event_id), "invitees._id": ObjectId(invitee_id)},
            {"$set": update_fields}
        )

        return success, message