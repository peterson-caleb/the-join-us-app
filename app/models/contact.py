# app/models/contact.py
from bson import ObjectId

class Contact:
    def __init__(self, name, phone, group_id, tags=None):
        self.name = name
        self.phone = phone
        self.tags = tags or []
        # --- NEW: Field for multi-tenancy ---
        self.group_id = group_id

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            phone=data['phone'],
            tags=data.get('tags', []),
            # --- NEW: Field for multi-tenancy ---
            group_id=data.get('group_id')
        )

    def to_dict(self):
        return {
            "name": self.name,
            "phone": self.phone,
            "tags": self.tags,
            # --- NEW: Field for multi-tenancy ---
            "group_id": self.group_id
        }