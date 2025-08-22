# app/services/sms_service.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from datetime import datetime, timedelta

class SMSService:
    def __init__(self, sid, auth_token, twilio_phone, message_log_service, base_url, enabled=False, hourly_limit=100, daily_limit=500):
        self.sid = sid
        self.auth_token = auth_token
        self.twilio_phone = twilio_phone
        self.base_url = base_url
        self.message_log_service = message_log_service
        
        # Guardrail settings (will be replaced by per-group limits)
        self.enabled = enabled
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        
        if self.sid and self.auth_token:
            self.client = Client(self.sid, self.auth_token)
        else:
            self.client = None
            logging.warning("Twilio credentials not found. SMS service will be simulated.")

    def _check_rate_limits(self):
        """
        Checks if sending an SMS would violate hourly or daily limits.
        NOTE: This is the GLOBAL rate-limiter. The next step will make this group-aware.
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        hourly_count = self.message_log_service.get_sms_count_since(one_hour_ago)
        if hourly_count >= self.hourly_limit:
            return False, f"Hourly SMS limit reached ({hourly_count}/{self.hourly_limit})."

        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        daily_count = self.message_log_service.get_sms_count_since(one_day_ago)
        if daily_count >= self.daily_limit:
            return False, f"Daily SMS limit reached ({daily_count}/{self.daily_limit})."

        return True, "Limits OK"

    def _send(self, to_number, message_body, contact_id=None, event_id=None, group_id=None):
        """Private method to handle the actual sending logic including all guardrails."""
        log_kwargs = {'contact_id': contact_id, 'event_id': event_id, 'group_id': group_id}
        
        if not self.enabled:
            reason = 'SMS sending is disabled globally.'
            logging.info(f"SMS sending is disabled. [Simulated Send] To: {to_number}")
            self.message_log_service.log_message(to_number, message_body, status='blocked', error_message=reason, **log_kwargs)
            return True, None

        can_send, reason = self._check_rate_limits()
        if not can_send:
            logging.error(f"SMS BLOCKED: Rate limit exceeded. Reason: {reason}")
            self.message_log_service.log_message(to_number, message_body, status='blocked', error_message=reason, **log_kwargs)
            return False, reason

        if not self.client:
            reason = 'Twilio client not initialized.'
            logging.warning(f"SMS not sent to {to_number} ({reason}).")
            self.message_log_service.log_message(to_number, message_body, status='failed', error_message=reason, **log_kwargs)
            return False, reason

        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.twilio_phone,
                body=message_body
            )
            logging.info(f"SMS sent successfully to {to_number}. SID: {message.sid}")
            self.message_log_service.log_message(to_number, message_body, status='sent', message_sid=message.sid, **log_kwargs)
            return True, None
        except TwilioRestException as e:
            logging.error(f"Failed to send SMS to {to_number}. Error: {e}")
            self.message_log_service.log_message(to_number, message_body, status='failed', error_message=str(e), **log_kwargs)
            return False, str(e)
        except Exception as e:
            reason = f"Unexpected error: {str(e)}"
            logging.error(f"An unexpected error occurred sending SMS to {to_number}. Error: {e}")
            self.message_log_service.log_message(to_number, message_body, status='failed', error_message=reason, **log_kwargs)
            return False, reason

    def send_invitation(self, invitee, event):
        """Sends an RSVP invitation SMS."""
        rsvp_url = f"{self.base_url}/rsvp/{invitee['rsvp_token']}"
        message_body = f"Hi {invitee['name']}, you're invited to {event['name']}! Please RSVP here: {rsvp_url}"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))

    def send_confirmation(self, invitee, event):
        """Sends a confirmation SMS to a guest who RSVP'd 'YES'."""
        event_date_str = event.get('date').strftime('%A, %B %d') if isinstance(event.get('date'), datetime) else 'the event date'
        message_body = f"Thanks for confirming, {invitee['name']}! We've got you down for {event['name']} on {event_date_str}. See you there!"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))

    def send_reminder(self, invitee, event):
        """Sends a reminder SMS to a guest with a pending invitation."""
        rsvp_url = f"{self.base_url}/rsvp/{invitee['rsvp_token']}"
        message_body = f"Hi {invitee['name']}, just a friendly reminder to RSVP for {event['name']}. Please respond here: {rsvp_url}"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))