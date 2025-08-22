# app/services/dashboard_service.py
from datetime import datetime, timedelta
from pymongo.database import Database
from bson import ObjectId

class DashboardService:
    def __init__(self, db: Database):
        self.db = db
        self.events_collection = db['events']
        self.logs_collection = db['message_logs']

    def get_stats(self, period_days: int = 7):
        """
        Calculates statistics for a given period.
        If period_days is 0, it calculates stats for all time.
        """
        end_date = datetime.utcnow()
        if period_days > 0:
            start_date = end_date - timedelta(days=period_days)
        else:
            start_date = datetime.min # A very early date for "all time"

        message_stats = self._get_message_stats_count(start_date, end_date)
        rsvp_stats = self._get_rsvp_stats_count(start_date, end_date)

        # Calculate response rate
        total_responses = rsvp_stats.get('YES', 0) + rsvp_stats.get('NO', 0)
        if total_responses > 0:
            response_rate = (rsvp_stats.get('YES', 0) / total_responses) * 100
        else:
            response_rate = 0

        return {
            'messages_sent': message_stats,
            'confirmed_rsvps': rsvp_stats.get('YES', 0),
            'declined_rsvps': rsvp_stats.get('NO', 0),
            'response_rate': round(response_rate, 1)
        }

    def _get_message_stats_count(self, start_date: datetime, end_date: datetime):
        """Counts sent messages within a date range."""
        query = {
            'status': 'sent',
            'timestamp': {'$gte': start_date, '$lte': end_date}
        }
        return self.logs_collection.count_documents(query)

    def _get_rsvp_stats_count(self, start_date: datetime, end_date: datetime):
        """Counts YES/NO RSVPs within a date range using an aggregation pipeline."""
        pipeline = [
            {'$unwind': '$invitees'},
            {
                '$match': {
                    'invitees.status': {'$in': ['YES', 'NO']},
                    'invitees.responded_at': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': '$invitees.status',
                    'count': {'$sum': 1}
                }
            }
        ]
        results = list(self.events_collection.aggregate(pipeline))
        stats_dict = {}
        for item in results:
            stats_dict[item['_id']] = item['count']
        return stats_dict

    # --- NEW METHODS for getting detailed lists ---

    def get_sent_messages_details(self, period_days: int = 7):
        """Gets a detailed list of sent messages for the period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days) if period_days > 0 else datetime.min
        
        pipeline = [
            {'$match': {'status': 'sent', 'timestamp': {'$gte': start_date, '$lte': end_date}}},
            {'$sort': {'timestamp': -1}},
            {
                '$lookup': {
                    'from': 'master_list',
                    'localField': 'contact_id',
                    'foreignField': '_id',
                    'as': 'contact_info'
                }
            },
            {'$unwind': {'path': '$contact_info', 'preserveNullAndEmptyArrays': True}},
            {
                '$lookup': {
                    'from': 'events',
                    'localField': 'event_id',
                    'foreignField': '_id',
                    'as': 'event_info'
                }
            },
            {'$unwind': {'path': '$event_info', 'preserveNullAndEmptyArrays': True}},
            {
                '$project': {
                    '_id': 0,
                    'recipient_name': '$contact_info.name',
                    'event_name': '$event_info.name',
                    'timestamp': '$timestamp'
                }
            }
        ]
        return list(self.logs_collection.aggregate(pipeline))

    def get_rsvp_details(self, period_days: int = 7, status: str = 'YES'):
        """Gets a detailed list of RSVPs for a given status and period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days) if period_days > 0 else datetime.min

        pipeline = [
            {'$unwind': '$invitees'},
            {
                '$match': {
                    'invitees.status': status,
                    'invitees.responded_at': {'$gte': start_date, '$lte': end_date}
                }
            },
            {'$sort': {'invitees.responded_at': -1}},
            {
                '$project': {
                    '_id': 0,
                    'guest_name': '$invitees.name',
                    'event_name': '$name',
                    'responded_at': '$invitees.responded_at'
                }
            }
        ]
        return list(self.events_collection.aggregate(pipeline))