# app/models/event.py
from datetime import datetime
from bson import ObjectId
import secrets
import string

class Event:
    """
    Event model representing a single event in the RSVP system.
    """
    def __init__(self, name, date, capacity, invitation_expiry_hours=24, details=""):
        self.name = name
        self.date = date
        self.capacity = capacity
        self.details = details
        self.invitees = []
        self.created_at = datetime.utcnow()
        self.event_code = self._generate_event_code()
        self.invitation_expiry_hours = invitation_expiry_hours
        self.automation_status = 'paused'
        self._id = None

    def _generate_event_code(self):
        """Generate a unique event code based on event name"""
        prefix = ''.join(c for c in self.name.upper().split()[0] if c.isalpha())[:2]
        if not prefix:
            prefix = 'EV'
        numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
        return f"{prefix}{numbers}"

    @classmethod
    def from_dict(cls, data, invitation_expiry_hours=24):
        """Create an event instance from dictionary data"""
        
        # --- THIS IS THE FIX ---
        # Convert date string from database/form into a real datetime object
        event_date = data.get('date')
        if isinstance(event_date, str):
            try:
                # Assuming the date is in 'YYYY-MM-DD' format
                event_date = datetime.strptime(event_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                # Handle cases where the date might be invalid or already a datetime object
                event_date = datetime.now() # Fallback to now
        elif not isinstance(event_date, datetime):
             event_date = datetime.now() # Fallback for other invalid types
        # --- END OF FIX ---

        event = cls(
            name=data['name'],
            date=event_date, # Use the converted datetime object
            capacity=data['capacity'],
            invitation_expiry_hours=invitation_expiry_hours,
            details=data.get('details', "")
        )
        event.invitees = data.get('invitees', [])
        event.created_at = data.get('created_at', datetime.utcnow())
        event.event_code = data.get('event_code', event._generate_event_code())
        event.automation_status = data.get('automation_status', 'paused')
        event._id = data.get('_id')
        return event

    def to_dict(self):
        """Convert event to dictionary for storage"""
        
        # Ensure date is a string in 'YYYY-MM-DD' format for database storage
        date_str = self.date.strftime('%Y-%m-%d') if isinstance(self.date, datetime) else self.date

        return {
            "name": self.name,
            "date": date_str,
            "capacity": self.capacity,
            "details": self.details,
            "invitees": self.invitees,
            "created_at": self.created_at,
            "event_code": self.event_code,
            "invitation_expiry_hours": self.invitation_expiry_hours,
            "automation_status": self.automation_status
        }