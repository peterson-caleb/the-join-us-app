# app/services/sms_service.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from datetime import datetime, timedelta
from flask import current_app

class SMSService:
    def __init__(self, sid, auth_token, twilio_phone, message_log_service, base_url, settings_service, enabled=False):
        self.sid = sid
        self.auth_token = auth_token
        self.twilio_phone = twilio_phone
        self.base_url = base_url
        self.message_log_service = message_log_service
        self.settings_service = settings_service
        self.enabled = enabled
        
        if self.sid and self.auth_token:
            self.client = Client(self.sid, self.auth_token)
        else:
            self.client = None
            logging.warning("Twilio credentials not found. SMS service will be simulated.")
        
        from app import mongo
        self.groups_collection = mongo.db.groups

    def _check_recipient_spam(self, to_number):
        """Platform-wide check to prevent spamming a single phone number."""
        limit = current_app.config['RECIPIENT_SPAM_LIMIT']
        window = current_app.config['RECIPIENT_SPAM_WINDOW_MINUTES']
        
        start_time = datetime.utcnow() - timedelta(minutes=window)
        recent_sends = self.message_log_service.get_sms_count_for_recipient_since(to_number, start_time)
        
        if recent_sends >= limit:
            reason = f"Recipient spam protection: Number has received {recent_sends} messages in the last {window} minutes (limit is {limit})."
            return False, reason
        return True, "Recipient OK"

    def _check_global_rate_limits(self):
        """Checks if sending an SMS would violate the global platform limits from DB settings."""
        hourly_limit = self.settings_service.get_setting('sms_hourly_limit')
        daily_limit = self.settings_service.get_setting('sms_daily_limit')
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        hourly_count = self.message_log_service.get_sms_count_since(one_hour_ago)
        if hourly_count >= hourly_limit:
            return False, f"Global hourly SMS limit reached ({hourly_count}/{hourly_limit})."

        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        daily_count = self.message_log_service.get_sms_count_since(one_day_ago)
        if daily_count >= daily_limit:
            return False, f"Global daily SMS limit reached ({daily_count}/{daily_limit})."

        return True, "Global limits OK"

    def _check_group_rate_limits(self, group_id):
        """Checks if sending an SMS would violate the specific group's limits."""
        group = self.groups_collection.find_one({"_id": group_id})
        if not group:
            return False, "Group not found for quota check."

        hourly_limit = group.get('sms_hourly_limit', 100)
        daily_limit = group.get('sms_daily_limit', 500)

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        hourly_count = self.message_log_service.get_sms_count_for_group_since(group_id, one_hour_ago)
        if hourly_count >= hourly_limit:
            return False, f"Group hourly SMS limit reached ({hourly_count}/{hourly_limit})."

        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        daily_count = self.message_log_service.get_sms_count_for_group_since(group_id, one_day_ago)
        if daily_count >= daily_limit:
            return False, f"Group daily SMS limit reached ({daily_count}/{daily_limit})."

        return True, "Group limits OK"

    def _send(self, to_number, message_body, contact_id=None, event_id=None, group_id=None):
        """Private method to handle sending logic with all guardrails."""
        log_kwargs = {'contact_id': contact_id, 'event_id': event_id, 'group_id': group_id}
        
        if not self.enabled:
            reason = 'SMS sending is disabled globally.'
            self.message_log_service.log_message(to_number, message_body, 'blocked', error_message=reason, **log_kwargs)
            return True, None

        can_send, reason = self._check_recipient_spam(to_number)
        if not can_send:
            logging.error(f"SMS BLOCKED: {reason}")
            self.message_log_service.log_message(to_number, message_body, 'blocked', error_message=reason, **log_kwargs)
            return False, reason

        can_send, reason = self._check_global_rate_limits()
        if not can_send:
            logging.error(f"SMS BLOCKED: {reason}")
            self.message_log_service.log_message(to_number, message_body, 'blocked', error_message=reason, **log_kwargs)
            return False, reason
            
        can_send, reason = self._check_group_rate_limits(group_id)
        if not can_send:
            logging.error(f"SMS BLOCKED: {reason}")
            self.message_log_service.log_message(to_number, message_body, 'blocked', error_message=reason, **log_kwargs)
            return False, reason

        if not self.client:
            reason = 'Twilio client not initialized.'
            self.message_log_service.log_message(to_number, message_body, 'failed', error_message=reason, **log_kwargs)
            return False, reason

        try:
            message = self.client.messages.create(to=to_number, from_=self.twilio_phone, body=message_body)
            self.message_log_service.log_message(to_number, message_body, 'sent', message.sid, **log_kwargs)
            return True, None
        except TwilioRestException as e:
            self.message_log_service.log_message(to_number, message_body, 'failed', error_message=str(e), **log_kwargs)
            return False, str(e)
        except Exception as e:
            reason = f"Unexpected error: {str(e)}"
            self.message_log_service.log_message(to_number, message_body, 'failed', error_message=reason, **log_kwargs)
            return False, reason

    def send_invitation(self, invitee, event):
        rsvp_url = f"{self.base_url}/rsvp/{invitee['rsvp_token']}"
        message_body = f"Hi {invitee['name']}, you're invited to {event['name']}! Please RSVP here: {rsvp_url}"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))

    def send_confirmation(self, invitee, event):
        event_date_str = event.get('date').strftime('%A, %B %d') if isinstance(event.get('date'), datetime) else 'the event date'
        message_body = f"Thanks for confirming, {invitee['name']}! We've got you down for {event['name']} on {event_date_str}. See you there!"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))

    def send_reminder(self, invitee, event):
        rsvp_url = f"{self.base_url}/rsvp/{invitee['rsvp_token']}"
        message_body = f"Hi {invitee['name']}, just a friendly reminder to RSVP for {event['name']}. Please respond here: {rsvp_url}"
        return self._send(invitee['phone'], message_body, contact_id=invitee.get('contact_id'), event_id=event.get('_id'), group_id=event.get('group_id'))
