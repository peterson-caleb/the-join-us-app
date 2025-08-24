# app/models/user.py
from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime
import secrets

class User(UserMixin):
    def __init__(self, username, email, password_hash, is_admin=False, registration_method=None, _id=None, active_group_id=None, created_at=None, contact_collection_token=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.registration_method = registration_method
        self.created_at = created_at or datetime.utcnow()
        self._id = _id or ObjectId()
        self.active_group_id = active_group_id
        self.contact_collection_token = contact_collection_token or secrets.token_urlsafe(24)
        
    @property
    def id(self):
        return str(self._id)

    @property
    def active_group_id_str(self):
        """Returns the active group ID as a string, or None if not set."""
        return str(self.active_group_id) if self.active_group_id else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            is_admin=data.get('is_admin', False),
            registration_method=data.get('registration_method'),
            _id=data.get('_id'),
            active_group_id=data.get('active_group_id'),
            created_at=data.get('created_at'),
            contact_collection_token=data.get('contact_collection_token')
        )

    def to_dict(self):
        return {
            "_id": self._id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_admin": self.is_admin,
            "registration_method": self.registration_method,
            "created_at": self.created_at,
            "active_group_id": self.active_group_id,
            "contact_collection_token": self.contact_collection_token
        }
