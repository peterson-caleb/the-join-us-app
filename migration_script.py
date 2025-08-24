# migration_script.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

def run_migration():
    """
    Executes a one-time migration of the database to support the new
    single-owner group model and user-owned contacts.
    """
    print("Starting database migration...")
    
    # --- 1. Connect to the database ---
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("ERROR: MONGO_URI not found in .env file. Aborting.")
        return

    try:
        client = MongoClient(mongo_uri)
        # Assumes the database name is the last part of the URI path
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        print(f"Successfully connected to database: '{db_name}'")
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB. {e}")
        return

    # --- 2. Migrate the 'users' collection ---
    print("\n--- Migrating Users ---")
    users_collection = db['users']
    users_to_migrate = users_collection.find({
        "$or": [
            {"group_memberships": {"$exists": True}},
            {"group_invitations": {"$exists": True}}
        ]
    })
    
    migrated_users_count = 0
    for user in users_to_migrate:
        update_result = users_collection.update_one(
            {'_id': user['_id']},
            {'$unset': {'group_memberships': "", 'group_invitations': ""}}
        )
        if update_result.modified_count > 0:
            migrated_users_count += 1
            
    if migrated_users_count > 0:
        print(f"Successfully migrated {migrated_users_count} user documents.")
    else:
        print("No users required migration (fields already removed).")

    # --- 3. Migrate the 'master_list' to 'contacts' ---
    print("\n--- Migrating Contacts ---")
    
    # Check if migration is needed
    if "master_list" in db.list_collection_names() and "contacts" not in db.list_collection_names():
        print("Found 'master_list'. Renaming to 'contacts'...")
        db['master_list'].rename('contacts')
        print("Collection renamed successfully.")
    elif "contacts" in db.list_collection_names():
        print("'contacts' collection already exists. Proceeding to update documents.")
    else:
        print("No 'master_list' or 'contacts' collection found. Skipping contact migration.")
        print("\nMigration complete!")
        client.close()
        return

    contacts_collection = db['contacts']
    groups_collection = db['groups']
    
    # Cache group owners to reduce database calls
    group_owners = {str(g['_id']): g['owner_id'] for g in groups_collection.find({}, {'owner_id': 1})}
    
    contacts_to_migrate = contacts_collection.find({"group_id": {"$exists": True}})
    
    migrated_contacts_count = 0
    contacts_with_missing_groups = 0
    
    for contact in contacts_to_migrate:
        group_id_str = str(contact.get('group_id'))
        
        if group_id_str in group_owners:
            owner_id = group_owners[group_id_str]
            update_result = contacts_collection.update_one(
                {'_id': contact['_id']},
                {
                    '$set': {'owner_id': owner_id},
                    '$unset': {'group_id': ""}
                }
            )
            if update_result.modified_count > 0:
                migrated_contacts_count += 1
        else:
            contacts_with_missing_groups += 1
            print(f"  - WARNING: Could not find owner for contact '{contact['name']}' (group_id: {group_id_str}). Skipping.")

    if migrated_contacts_count > 0:
        print(f"Successfully migrated {migrated_contacts_count} contact documents.")
    else:
        print("No contacts required migration (documents already up to date).")
        
    if contacts_with_missing_groups > 0:
        print(f"WARNING: Skipped {contacts_with_missing_groups} contacts due to missing group references.")

    print("\nMigration complete!")
    client.close()

if __name__ == "__main__":
    run_migration()
