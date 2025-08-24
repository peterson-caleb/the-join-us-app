# app/models/contact.py
from bson import ObjectId

class Contact:
    def __init__(self, name, phone, owner_id, tags=None, _id=None):
        self._id = _id or ObjectId()
        self.name = name
        self.phone = phone
        self.tags = tags or []
        # A contact is now owned by a user, not a group.
        self.owner_id = owner_id

    @classmethod
    def from_dict(cls, data):
        return cls(
            _id=data.get('_id'),
            name=data.get('name'),
            phone=data.get('phone'),
            tags=data.get('tags', []),
            owner_id=data.get('owner_id')
        )

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "phone": self.phone,
            "tags": self.tags,
            "owner_id": self.owner_id
        }