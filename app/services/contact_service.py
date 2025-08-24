# app/services/contact_service.py
from bson import ObjectId
from ..models.contact import Contact

class ContactService:
    def __init__(self, db):
        self.db = db
        # RENAMED: Collection is now 'contacts'
        self.contacts_collection = db['contacts']

    def create_contact(self, contact_data, owner_id):
        contact_data['owner_id'] = ObjectId(owner_id)
        
        # UPDATED CHECK: Allow same phone number, but block duplicate name + phone combinations.
        existing = self.contacts_collection.find_one({
            "name": contact_data['name'],
            "phone": contact_data['phone'],
            "owner_id": contact_data['owner_id']
        })
        if existing:
            raise ValueError(f"A contact named '{contact_data['name']}' with the phone number {contact_data['phone']} already exists.")

        contact = Contact.from_dict(contact_data)
        result = self.contacts_collection.insert_one(contact.to_dict())
        return str(result.inserted_id)

    def get_contacts(self, owner_id, filters=None):
        query = filters or {}
        query['owner_id'] = ObjectId(owner_id)
        contacts = list(self.contacts_collection.find(query))
        for contact in contacts:
            contact['_id'] = str(contact['_id'])
            if 'owner_id' in contact:
                contact['owner_id'] = str(contact['owner_id'])
        return contacts

    def get_contact(self, owner_id, contact_id):
        return self.contacts_collection.find_one({"_id": ObjectId(contact_id), "owner_id": ObjectId(owner_id)})

    def update_contact(self, owner_id, contact_id, contact_data):
        # UPDATED CHECK: Prevent updating to a name + phone combination that already exists.
        if 'phone' in contact_data and 'name' in contact_data:
            existing = self.contacts_collection.find_one({
                "name": contact_data['name'],
                "phone": contact_data['phone'],
                "owner_id": ObjectId(owner_id),
                "_id": {"$ne": ObjectId(contact_id)}
            })
            if existing:
                raise ValueError(f"Another contact named '{contact_data['name']}' with the phone number {contact_data['phone']} already exists.")

        self.contacts_collection.update_one(
            {"_id": ObjectId(contact_id), "owner_id": ObjectId(owner_id)},
            {"$set": contact_data}
        )
        return self.get_contact(owner_id, contact_id)

    def delete_contact(self, owner_id, contact_id):
        return self.contacts_collection.delete_one({"_id": ObjectId(contact_id), "owner_id": ObjectId(owner_id)})

    def get_all_tags(self, owner_id):
        tags = self.contacts_collection.distinct('tags', {"owner_id": ObjectId(owner_id)})
        return sorted(filter(None, tags))