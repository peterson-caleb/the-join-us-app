# Create new file: app/services/message_log_service.py
from datetime import datetime
from bson import ObjectId

class MessageLogService:
    def __init__(self, db):
        self.db = db
        self.logs_collection = db['message_logs']
        self.logs_collection.create_index([("contact_id", 1)])
        self.logs_collection.create_index([("event_id", 1)])

    def create_log(self, log_data):
        """
        Creates a new message log entry.
        """
        log_data['created_at'] = datetime.utcnow()
        if 'contact_id' in log_data and isinstance(log_data['contact_id'], str):
            log_data['contact_id'] = ObjectId(log_data['contact_id'])
        if 'event_id' in log_data and isinstance(log_data['event_id'], str):
            log_data['event_id'] = ObjectId(log_data['event_id'])
        self.logs_collection.insert_one(log_data)

    def get_logs_for_contact(self, contact_id):
        """Retrieve all message logs for a specific contact."""
        return list(self.logs_collection.find({'contact_id': ObjectId(contact_id)}).sort('created_at', -1))