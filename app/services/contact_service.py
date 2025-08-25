# app/services/contact_service.py
from bson import ObjectId
from ..models.contact import Contact
import phonenumbers

class ContactService:
    def __init__(self, db):
        self.db = db
        self.contacts_collection = db['contacts']

    def _validate_and_format_phone(self, phone_number_str):
        """
        Validates and formats a phone number to E.164 format for US numbers.
        Returns the formatted number or raises a ValueError.
        """
        if not phone_number_str:
            raise ValueError("Phone number cannot be empty.")
        try:
            # Parse the number, assuming "US" as the default region.
            # This helps correctly interpret numbers without a country code.
            parsed_number = phonenumbers.parse(phone_number_str, "US")

            # Check if the number is valid for the US region.
            if not phonenumbers.is_valid_number_for_region(parsed_number, "US"):
                raise ValueError(f"'{phone_number_str}' is not a valid US phone number.")

            # Format to the E.164 standard (e.g., +15551234567)
            formatted_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
            return formatted_number
        except phonenumbers.NumberParseException as e:
            # This catches numbers that are fundamentally malformed.
            raise ValueError(f"Could not parse the phone number '{phone_number_str}'. Please check the format.") from e

    def create_contact(self, contact_data, owner_id):
        contact_data['owner_id'] = ObjectId(owner_id)
        
        # Validate and format the phone number before any other checks.
        contact_data['phone'] = self._validate_and_format_phone(contact_data.get('phone'))
        
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
        # Validate and format the phone number if it's being updated.
        if 'phone' in contact_data:
            contact_data['phone'] = self._validate_and_format_phone(contact_data.get('phone'))

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