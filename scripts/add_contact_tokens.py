# add_contact_tokens.py
import os
import secrets
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

def add_missing_contact_tokens():
    """
    Finds all users missing the 'contact_collection_token' and adds one.
    """
    print("Starting script to add missing contact collection tokens...")
    
    # --- 1. Connect to the database ---
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("ERROR: MONGO_URI not found in .env file. Aborting.")
        return

    try:
        client = MongoClient(mongo_uri)
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        print(f"Successfully connected to database: '{db_name}'")
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB. {e}")
        return

    # --- 2. Find and update users ---
    users_collection = db['users']
    
    # Find users where the contact_collection_token field does not exist
    users_to_update = list(users_collection.find({
        "contact_collection_token": {"$exists": False}
    }))
    
    if not users_to_update:
        print("\nNo users found missing the token. Your system is already up to date!")
        client.close()
        return

    print(f"\nFound {len(users_to_update)} user(s) that need a contact collection token.")
    
    updated_count = 0
    for user in users_to_update:
        new_token = secrets.token_urlsafe(24)
        result = users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'contact_collection_token': new_token}}
        )
        if result.modified_count > 0:
            print(f"  - Added token for user: {user['username']}")
            updated_count += 1
            
    if updated_count > 0:
        print(f"\nSuccessfully updated {updated_count} user(s).")
    
    print("\nScript finished!")
    client.close()

if __name__ == "__main__":
    add_missing_contact_tokens()
