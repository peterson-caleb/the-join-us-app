# app/services/dashboard_service.py
from datetime import datetime, timedelta
from pymongo.database import Database

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

        message_stats = self._get_message_stats(start_date, end_date)
        rsvp_stats = self._get_rsvp_stats(start_date, end_date)

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

    def _get_message_stats(self, start_date: datetime, end_date: datetime):
        """Counts sent messages within a date range."""
        query = {
            'status': 'sent',
            'timestamp': {'$gte': start_date, '$lte': end_date}
        }
        return self.logs_collection.count_documents(query)

    def _get_rsvp_stats(self, start_date: datetime, end_date: datetime):
        """Counts YES/NO RSVPs within a date range using an aggregation pipeline."""
        pipeline = [
            # Deconstruct the invitees array into separate documents
            {'$unwind': '$invitees'},
            # Filter for invitees who responded within the date range
            {
                '$match': {
                    'invitees.status': {'$in': ['YES', 'NO']},
                    'invitees.responded_at': {'$gte': start_date, '$lte': end_date}
                }
            },
            # Group by status (YES/NO) and count them
            {
                '$group': {
                    '_id': '$invitees.status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        results = list(self.events_collection.aggregate(pipeline))
        
        # Format the results into a simple dictionary
        stats_dict = {}
        for item in results:
            stats_dict[item['_id']] = item['count']
            
        return stats_dict