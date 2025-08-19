# app/services/message_log_service.py
from datetime import datetime, timedelta
from bson import ObjectId

class MessageLogService:
    def __init__(self, db):
        self.db = db
        self.logs_collection = db.message_logs
        
        # --- From your file: Keep these excellent performance improvements ---
        self.logs_collection.create_index([("contact_id", 1)])
        self.logs_collection.create_index([("event_id", 1)])
        # --- New: Add an index for the rate-limiting query to keep it fast ---
        self.logs_collection.create_index([("timestamp", -1)])

    def log_message(self, to_number, message_body, status, message_sid=None, error_message=None, contact_id=None, event_id=None):
        """
        Logs an SMS message attempt to the database. 
        This is a new, unified method that combines the logic from both files.
        """
        log_entry = {
            "to_number": to_number,
            "message_body": message_body,
            "status": status,  # e.g., 'sent', 'failed', 'blocked'
            "message_sid": message_sid,
            "error_message": error_message,
            "timestamp": datetime.utcnow() # Using 'timestamp' for consistency
        }
        
        # --- From your file: Preserve the smart ObjectId conversion ---
        if contact_id:
            log_entry['contact_id'] = ObjectId(contact_id) if isinstance(contact_id, str) else contact_id
        if event_id:
            log_entry['event_id'] = ObjectId(event_id) if isinstance(event_id, str) else event_id

        self.logs_collection.insert_one(log_entry)
        return log_entry

    def get_sms_count_since(self, start_time):
        """
        Counts the number of successfully sent SMS messages since a given start time.
        This function is ESSENTIAL for the rate-limiting guardrails.
        """
        count = self.logs_collection.count_documents({
            "timestamp": {"$gte": start_time},
            "status": "sent" 
        })
        return count

    def get_logs_for_contact(self, contact_id):
        """
        Retrieve all message logs for a specific contact.
        This is kept from your original file.
        """
        # I've updated this to sort by 'timestamp' to match the unified field name
        return list(self.logs_collection.find({'contact_id': ObjectId(contact_id)}).sort('timestamp', -1))