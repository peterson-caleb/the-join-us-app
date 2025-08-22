# app/services/admin_dashboard_service.py
from pymongo.database import Database
from bson import ObjectId

class AdminDashboardService:
    def __init__(self, db: Database):
        self.db = db
        self.users_collection = db['users']
        self.groups_collection = db['groups']
        self.events_collection = db['events']
        self.contacts_collection = db['master_list']
        self.logs_collection = db['message_logs']

    def get_global_stats(self):
        """Calculates system-wide statistics."""
        total_users = self.users_collection.count_documents({})
        total_groups = self.groups_collection.count_documents({})
        total_events = self.events_collection.count_documents({})
        total_contacts = self.contacts_collection.count_documents({})
        total_sms_sent = self.logs_collection.count_documents({'status': 'sent'})

        return {
            'total_users': total_users,
            'total_groups': total_groups,
            'total_events': total_events,
            'total_contacts': total_contacts,
            'total_sms_sent': total_sms_sent
        }
        
    def get_all_users_with_details(self):
        """Fetches all users and enriches them with group count and ownership details."""
        pipeline = [
            {
                '$project': {
                    'username': 1,
                    'email': 1,
                    'is_admin': 1,
                    'created_at': 1,
                    'group_membership_count': {'$size': '$group_memberships'}
                }
            },
            {
                '$sort': {'created_at': -1}
            }
        ]
        return list(self.users_collection.aggregate(pipeline))