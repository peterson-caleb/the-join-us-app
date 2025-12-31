# app/models/event.py
from datetime import datetime
from bson import ObjectId
import secrets
import string

class Event:
    """
    Event model representing a single event in the RSVP system.
    """
    def __init__(self, name, date, capacity, group_id, invitation_expiry_hours=None, details="", location=None, start_time=None, allow_rsvp_after_expiry=False, organizer_is_attending=False, show_attendee_list=False, is_archived=False, messages=None):
        self.name = name
        self.date = date
        self.capacity = capacity
        self.details = details
        self.location = location
        self.start_time = start_time
        self.invitees = []
        self.created_at = datetime.utcnow()
        self.event_code = self._generate_event_code()
        self.invitation_expiry_hours = invitation_expiry_hours
        self.allow_rsvp_after_expiry = allow_rsvp_after_expiry
        self.automation_status = 'paused'
        self._id = None
        self.group_id = group_id
        self.organizer_is_attending = organizer_is_attending
        self.show_attendee_list = show_attendee_list
        self.is_archived = is_archived
        self.messages = messages or []

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
        
        event_date = data.get('date')
        if isinstance(event_date, str):
            try:
                event_date = datetime.strptime(event_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                event_date = datetime.now()
        elif not isinstance(event_date, datetime):
                 event_date = datetime.now()

        # The global expiry is passed as a default, but the specific event's value takes precedence
        event_specific_expiry = data.get('invitation_expiry_hours', invitation_expiry_hours)

        event = cls(
            name=data['name'],
            date=event_date,
            capacity=data['capacity'],
            invitation_expiry_hours=event_specific_expiry,
            details=data.get('details', ""),
            location=data.get('location'),
            start_time=data.get('start_time'),
            allow_rsvp_after_expiry=data.get('allow_rsvp_after_expiry', False),
            group_id=data.get('group_id'),
            organizer_is_attending=data.get('organizer_is_attending', False),
            show_attendee_list=data.get('show_attendee_list', False),
            is_archived=data.get('is_archived', False),
            messages=data.get('messages', [])
        )
        event.invitees = data.get('invitees', [])
        event.created_at = data.get('created_at', datetime.utcnow())
        event.event_code = data.get('event_code', event._generate_event_code())
        event.automation_status = data.get('automation_status', 'paused')
        event._id = data.get('_id')
        return event

    def to_dict(self):
        """Convert event to dictionary for storage"""
        
        date_str = self.date.strftime('%Y-%m-%d') if isinstance(self.date, datetime) else self.date

        return {
            "name": self.name,
            "date": date_str,
            "capacity": self.capacity,
            "details": self.details,
            "location": self.location,
            "start_time": self.start_time,
            "invitees": self.invitees,
            "created_at": self.created_at,
            "event_code": self.event_code,
            "invitation_expiry_hours": self.invitation_expiry_hours,
            "allow_rsvp_after_expiry": self.allow_rsvp_after_expiry,
            "automation_status": self.automation_status,
            "group_id": self.group_id,
            "organizer_is_attending": self.organizer_is_attending,
            "show_attendee_list": self.show_attendee_list,
            "is_archived": self.is_archived,
            "messages": self.messages
        }