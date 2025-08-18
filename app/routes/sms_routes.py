# Modified file: app/routes/sms_routes.py
# app/routes/sms_routes.py
from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from .. import event_service, sms_service, message_log_service
from bson import ObjectId
import logging
from datetime import datetime
import json
from logging.handlers import RotatingFileHandler
import os

bp = Blueprint('sms', __name__)

# Configure logging
def setup_sms_logger():
    if not os.path.exists('logs'): os.makedirs('logs')
    logger = logging.getLogger('sms_logger')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler('logs/sms.log', maxBytes=10000000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

sms_logger = setup_sms_logger()

@bp.route('/sms', methods=['POST'])
def handle_sms():
    phone_number = request.form.get('From')
    message_body = request.form.get('Body', '').strip()
    
    status, event, invitee = event_service.process_rsvp(phone_number, message_body)

    # Log incoming message
    log_data = {
        'phone_number': phone_number,
        'message_type': 'rsvp_response', 'direction': 'incoming', 'body': message_body,
        'status': 'RECEIVED', 'message_sid': request.form.get('MessageSid')
    }
    if event: log_data['event_id'] = event._id
    if invitee: log_data['contact_id'] = ObjectId(invitee.get('contact_id'))
    message_log_service.create_log(log_data)
    
    resp = MessagingResponse()
    
    if status in ['YES', 'NO', 'FULL'] and event:
        sms_service.send_confirmation(
            phone_number=phone_number, event_name=event.name, status=status,
            event_id=event._id,
            contact_id=ObjectId(invitee.get('contact_id')) if invitee else None
        )
        return str(resp) # Return empty TwiML response
    else:
        message = "Sorry, we couldn't process your response. Please reply with 'EVENT_CODE YES' or 'EVENT_CODE NO'."
        resp.message(message)
        return str(resp)

@bp.route('/sms/logs', methods=['GET'])
def view_logs():
    # This should be protected by authentication and admin check
    try:
        with open('logs/sms.log', 'r') as log_file:
            logs = log_file.readlines()[-100:]  # Get last 100 lines
        return {'logs': logs}
    except Exception as e:
        sms_logger.error(f"Error reading logs: {str(e)}")
        return {'error': 'Unable to read logs'}, 500