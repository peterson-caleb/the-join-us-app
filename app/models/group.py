# app/models/group.py
from datetime import datetime
from bson import ObjectId

class Group:
    """
    Represents a Group, which is the top-level container for a user's
    events and contacts, enabling multi-tenancy.
    """
    def __init__(self, name, owner_id, _id=None, created_at=None):
        self._id = _id or ObjectId()
        self.name = name
        self.owner_id = owner_id
        self.created_at = created_at or datetime.utcnow()
        # Per-group quotas will be added here in the next step
        self.sms_hourly_limit = 100 # Default value
        self.sms_daily_limit = 500  # Default value

    @classmethod
    def from_dict(cls, data):
        """Creates a Group instance from a dictionary."""
        return cls(
            name=data.get('name'),
            owner_id=data.get('owner_id'),
            _id=data.get('_id'),
            created_at=data.get('created_at')
        )

    def to_dict(self):
        """Converts the Group instance to a dictionary for database storage."""
        return {
            "_id": self._id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "sms_hourly_limit": self.sms_hourly_limit,
            "sms_daily_limit": self.sms_daily_limit
        }