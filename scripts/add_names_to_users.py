# add_names_to_users.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

def add_missing_names():
    """
    Finds all users missing the 'name' field and sets it to their username
    as a default.
    """
    print("Starting script to add missing names to users...")
    
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
    
    # Find users where the 'name' field does not exist
    users_to_update = list(users_collection.find({"name": {"$exists": False}}))
    
    if not users_to_update:
        print("\nNo users found missing the 'name' field. Your system is up to date!")
        client.close()
        return

    print(f"\nFound {len(users_to_update)} user(s) that need a name.")
    
    updated_count = 0
    for user in users_to_update:
        # Set the name to the user's username by default
        name_to_set = user.get('username', 'Default Name')
        result = users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'name': name_to_set}}
        )
        if result.modified_count > 0:
            print(f"  - Set name for user '{user['username']}' to '{name_to_set}'")
            updated_count += 1
            
    if updated_count > 0:
        print(f"\nSuccessfully updated {updated_count} user(s).")
    
    print("\nScript finished!")
    client.close()

if __name__ == "__main__":
    add_missing_names()