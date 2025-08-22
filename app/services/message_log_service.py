# app/services/message_log_service.py
from datetime import datetime, timedelta
from bson import ObjectId

class MessageLogService:
    def __init__(self, db):
        self.db = db
        self.logs_collection = db.message_logs
        
        # Create indexes for performance
        self.logs_collection.create_index([("contact_id", 1)])
        self.logs_collection.create_index([("event_id", 1)])
        self.logs_collection.create_index([("timestamp", -1)])
        self.logs_collection.create_index([("group_id", 1)]) # NEW index for group queries

    def log_message(self, to_number, message_body, status, message_sid=None, error_message=None, contact_id=None, event_id=None, group_id=None):
        """Logs an SMS message attempt to the database."""
        log_entry = {
            "to_number": to_number,
            "message_body": message_body,
            "status": status,
            "message_sid": message_sid,
            "error_message": error_message,
            "timestamp": datetime.utcnow()
        }
        
        if contact_id:
            log_entry['contact_id'] = ObjectId(contact_id) if isinstance(contact_id, str) else contact_id
        if event_id:
            log_entry['event_id'] = ObjectId(event_id) if isinstance(event_id, str) else event_id
        if group_id:
            log_entry['group_id'] = ObjectId(group_id) if isinstance(group_id, str) else group_id

        self.logs_collection.insert_one(log_entry)
        return log_entry

    def get_sms_count_since(self, start_time):
        """
        Counts the number of successfully sent SMS messages since a given start time.
        NOTE: This is currently for the GLOBAL rate-limiter. It will be made
        group-aware in the next implementation step.
        """
        count = self.logs_collection.count_documents({
            "timestamp": {"$gte": start_time},
            "status": "sent" 
        })
        return count

    def get_logs_for_contact(self, group_id, contact_id):
        """Retrieve all message logs for a specific contact within a group."""
        return list(self.logs_collection.find({
            'contact_id': ObjectId(contact_id),
            'group_id': ObjectId(group_id)
        }).sort('timestamp', -1))