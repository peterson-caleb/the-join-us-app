# app/models/user.py
from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime

class User(UserMixin):
    def __init__(self, username, email, password_hash, is_admin=False, registration_method=None, _id=None, active_group_id=None, group_memberships=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.registration_method = registration_method
        self.created_at = datetime.utcnow()
        self._id = _id if _id else ObjectId()
        # --- NEW: Fields for multi-tenancy ---
        self.active_group_id = active_group_id
        self.group_memberships = group_memberships or [] # e.g., [{'group_id': ObjectId(...), 'role': 'owner'}]

    @property
    def id(self):
        return str(self._id)

    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            is_admin=data.get('is_admin', False),
            registration_method=data.get('registration_method'),
            _id=data.get('_id'),
            # --- NEW: Fields for multi-tenancy ---
            active_group_id=data.get('active_group_id'),
            group_memberships=data.get('group_memberships', [])
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
            # --- NEW: Fields for multi-tenancy ---
            "active_group_id": self.active_group_id,
            "group_memberships": self.group_memberships
        }