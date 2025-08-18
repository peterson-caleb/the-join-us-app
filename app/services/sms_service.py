# Modified file: app/services/sms_service.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from datetime import datetime, timedelta
import os
from collections import deque
import threading

class SMSService:
    def __init__(self, twilio_sid, twilio_auth_token, twilio_phone, message_log_service):
        self.client = Client(twilio_sid, twilio_auth_token)
        self.twilio_phone = twilio_phone
        self.message_log_service = message_log_service
        self.base_url = base_url
        
        # Rate limiting settings
        self.max_messages_per_day = 100  # Twilio's default limit
        self.max_messages_per_second = 3   # Conservative rate limit
        
        # Initialize rate limiting trackers
        self.daily_message_count = 0
        self.daily_reset_time = datetime.now()
        self.recent_messages = deque(maxlen=100)  # Track recent message timestamps
        self.lock = threading.Lock()  # Thread-safe counter updates
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging for SMS service"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        self.logger = logging.getLogger('sms_service')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # File handler for SMS service logs
            file_handler = logging.FileHandler('logs/sms_service.log')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)

    def _check_rate_limits(self):
        """
        Check if we're within rate limits
        Returns: (bool, str) - (is_allowed, reason_if_not_allowed)
        """
        now = datetime.now()
        
        with self.lock:
            # Reset daily counter if needed
            if (now - self.daily_reset_time).days >= 1:
                self.daily_message_count = 0
                self.daily_reset_time = now
            
            # Check daily limit
            if self.daily_message_count >= self.max_messages_per_day:
                return False, "Daily message limit exceeded"
            
            # Check per-second rate limit
            recent_count = sum(1 for t in self.recent_messages 
                               if (now - t).total_seconds() < 1)
            if recent_count >= self.max_messages_per_second:
                return False, "Per-second rate limit exceeded"
            
            return True, None

    def _update_rate_limiting_stats(self):
        """Update rate limiting counters after successful send"""
        now = datetime.now()
        with self.lock:
            self.daily_message_count += 1
            self.recent_messages.append(now)

    def send_invitation(self, phone_number, event_name, event_date, rsvp_token, event_id=None, contact_id=None): # Changed event_code to rsvp_token
        """
        Send an invitation SMS with a unique RSVP link.
        """
        # Updated message body to use the RSVP link
        rsvp_url = f"{self.base_url}/rsvp/{rsvp_token}"
        body = (f"You're invited to {event_name} on {event_date}! "
                f"Please RSVP here: {rsvp_url}")

        log_data = {
            'contact_id': contact_id, 'event_id': event_id, 'phone_number': phone_number,
            'message_type': 'invitation', 'direction': 'outgoing', 'body': body
        }

        try:
            is_allowed, limit_reason = self._check_rate_limits()
            if not is_allowed:
                self.logger.warning(f"Rate limit prevented sending to {phone_number}: {limit_reason}")
                log_data.update({'status': 'ERROR', 'error_message': limit_reason})
                self.message_log_service.create_log(log_data)
                return None, "ERROR", limit_reason
            
            message = self.client.messages.create(body=body, from_=self.twilio_phone, to=phone_number)
            self._update_rate_limiting_stats()
            
            self.logger.info(f"Successfully sent invitation to {phone_number} for {event_name}")
            log_data.update({'status': 'SENT', 'message_sid': message.sid})
            self.message_log_service.create_log(log_data)
            return message.sid, "SENT", None
            
        except TwilioRestException as e:
            error_msg = f"Twilio error sending SMS to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            
            if e.code == 21610: error_reason = "Invalid phone number"
            elif e.code == 21611: error_reason = "Phone cannot receive SMS"
            elif e.code == 21612: error_reason = "Too many messages to this number"
            else: error_reason = f"Twilio error: {str(e)}"
            
            log_data.update({'status': 'ERROR', 'error_message': error_reason})
            self.message_log_service.create_log(log_data)
            return None, "ERROR", error_reason
            
        except Exception as e:
            error_msg = f"Unexpected error sending SMS to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            error_reason = f"Unexpected error: {str(e)}"
            log_data.update({'status': 'ERROR', 'error_message': error_reason})
            self.message_log_service.create_log(log_data)
            return None, "ERROR", error_reason

    def send_confirmation(self, phone_number, event_name, status, event_id=None, contact_id=None):
        """
        Send a confirmation SMS with rate limiting and error handling
        Returns: (bool, error_message)
        """
        if status == 'YES': message_text = f"Great! You're confirmed for {event_name}. We'll send you more details soon."
        elif status == 'NO': message_text = f"Thanks for letting us know you can't make it to {event_name}."
        elif status == 'FULL': message_text = f"Sorry, {event_name} is now at full capacity. We'll add you to the waitlist."
        else: message_text = "Thanks for your response!"

        log_data = {
            'contact_id': contact_id, 'event_id': event_id, 'phone_number': phone_number,
            'message_type': 'confirmation', 'direction': 'outgoing', 'body': message_text
        }

        try:
            is_allowed, limit_reason = self._check_rate_limits()
            if not is_allowed:
                self.logger.warning(f"Rate limit prevented confirmation to {phone_number}: {limit_reason}")
                log_data.update({'status': 'ERROR', 'error_message': limit_reason})
                self.message_log_service.create_log(log_data)
                return False, limit_reason

            message = self.client.messages.create(body=message_text, from_=self.twilio_phone, to=phone_number)
            self._update_rate_limiting_stats()
            
            self.logger.info(f"Successfully sent confirmation to {phone_number} for {event_name}")
            log_data.update({'status': 'SENT', 'message_sid': message.sid})
            self.message_log_service.create_log(log_data)
            return True, None
            
        except TwilioRestException as e:
            error_msg = f"Twilio error sending confirmation to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            log_data.update({'status': 'ERROR', 'error_message': str(e)})
            self.message_log_service.create_log(log_data)
            return False, str(e)
            
        except Exception as e:
            error_msg = f"Unexpected error sending confirmation to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            log_data.update({'status': 'ERROR', 'error_message': str(e)})
            self.message_log_service.create_log(log_data)
            return False, str(e)
            
    def send_reminder(self, phone_number, event_name, expiry_hours, event_id=None, contact_id=None):
        """
        Send a reminder SMS with rate limiting and error handling.
        Returns: (message_sid, status, error_message)
        """
        body = (f"Just a reminder: Your invitation to {event_name} will expire in about {expiry_hours} hours. "
                "Please respond soon!")
        
        log_data = {
            'contact_id': contact_id, 'event_id': event_id, 'phone_number': phone_number,
            'message_type': 'reminder', 'direction': 'outgoing', 'body': body
        }

        try:
            is_allowed, limit_reason = self._check_rate_limits()
            if not is_allowed:
                self.logger.warning(f"Rate limit prevented sending reminder to {phone_number}: {limit_reason}")
                log_data.update({'status': 'ERROR', 'error_message': limit_reason})
                self.message_log_service.create_log(log_data)
                return None, "ERROR", limit_reason
            
            message = self.client.messages.create(body=body, from_=self.twilio_phone, to=phone_number)
            self._update_rate_limiting_stats()
            
            self.logger.info(f"Successfully sent reminder to {phone_number} for {event_name}")
            log_data.update({'status': 'SENT', 'message_sid': message.sid})
            self.message_log_service.create_log(log_data)
            return message.sid, "SENT", None
            
        except TwilioRestException as e:
            error_msg = f"Twilio error sending reminder to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            
            if e.code == 21610: error_reason = "Invalid phone number"
            elif e.code == 21611: error_reason = "Phone cannot receive SMS"
            else: error_reason = f"Twilio error: {str(e)}"
            
            log_data.update({'status': 'ERROR', 'error_message': error_reason})
            self.message_log_service.create_log(log_data)
            return None, "ERROR", error_reason
            
        except Exception as e:
            error_msg = f"Unexpected error sending reminder to {phone_number}: {str(e)}"
            self.logger.error(error_msg)
            error_reason = f"Unexpected error: {str(e)}"
            log_data.update({'status': 'ERROR', 'error_message': error_reason})
            self.message_log_service.create_log(log_data)
            return None, "ERROR", error_reason