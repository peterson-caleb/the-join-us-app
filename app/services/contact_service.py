# app/services/contact_service.py
from bson import ObjectId
from ..models.contact import Contact

class ContactService:
    def __init__(self, db):
        self.db = db
        self.contacts_collection = db['master_list']

    def create_contact(self, contact_data, group_id):
        # Check for duplicate phone number within the same group
        if self.contacts_collection.find_one({"phone": contact_data['phone'], "group_id": ObjectId(group_id)}):
            raise ValueError("A contact with this phone number already exists in this group.")
        
        contact_data['group_id'] = ObjectId(group_id)
        contact = Contact.from_dict(contact_data)
        result = self.contacts_collection.insert_one(contact.to_dict())
        return str(result.inserted_id)

    def get_contacts(self, group_id, filters=None):
        query = filters or {}
        query['group_id'] = ObjectId(group_id)
        contacts = list(self.contacts_collection.find(query))
        for contact in contacts:
            contact['_id'] = str(contact['_id'])
        return contacts

    def get_contact(self, group_id, contact_id):
        return self.contacts_collection.find_one({"_id": ObjectId(contact_id), "group_id": ObjectId(group_id)})

    def update_contact(self, group_id, contact_id, contact_data):
        self.contacts_collection.update_one(
            {"_id": ObjectId(contact_id), "group_id": ObjectId(group_id)},
            {"$set": contact_data}
        )
        return self.get_contact(group_id, contact_id)

    def delete_contact(self, group_id, contact_id):
        return self.contacts_collection.delete_one({"_id": ObjectId(contact_id), "group_id": ObjectId(group_id)})

    def filter_by_tags(self, group_id, tags):
        if not tags:
            return self.get_contacts(group_id)
        
        query = {
            "tags": {"$in": tags},
            "group_id": ObjectId(group_id)
        }
        return list(self.contacts_collection.find(query))
    
    def get_all_tags(self, group_id):
        tags = self.contacts_collection.distinct('tags', {"group_id": ObjectId(group_id)})
        return sorted(filter(None, tags))