# app/services/contact_service.py
from bson import ObjectId
from ..models.contact import Contact
from pymongo.errors import DuplicateKeyError

class ContactService:
    def __init__(self, db):
        self.db = db
        self.contacts_collection = db['master_list']
        # Ensure phone numbers are unique at the database level
        self.contacts_collection.create_index('phone', unique=True)

    def create_contact(self, contact_data):
        contact = Contact.from_dict(contact_data)
        try:
            # Attempt to insert the new contact
            result = self.contacts_collection.insert_one(contact.to_dict())
            return str(result.inserted_id)
        except DuplicateKeyError:
            # If the phone number is already taken, raise a friendly error
            raise ValueError(f"A contact with the phone number {contact_data['phone']} already exists.")

    def get_contacts(self, filters=None):
        query = filters or {}
        contacts = list(self.contacts_collection.find(query))
        for contact in contacts:
            contact['_id'] = str(contact['_id'])
        return contacts

    def get_contact(self, contact_id):
        return self.contacts_collection.find_one({"_id": ObjectId(contact_id)})

    def update_contact(self, contact_id, contact_data):
        self.contacts_collection.update_one(
            {"_id": ObjectId(contact_id)},
            {"$set": contact_data}
        )
        return self.get_contact(contact_id)

    def delete_contact(self, contact_id):
        return self.contacts_collection.delete_one({"_id": ObjectId(contact_id)})

    def filter_by_tags(self, tags):
        if not tags:
            return self.get_contacts()
        return list(self.contacts_collection.find({"tags": {"$in": tags}}))
    
    def get_all_tags(self):
        tags = self.contacts_collection.distinct('tags')
        return sorted(filter(None, tags))