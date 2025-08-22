# app/services/user_service.py
from bson import ObjectId
import bcrypt
from ..models.user import User
from .group_service import GroupService

class UserService:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.groups_collection = db['groups'] # For fetching group names
        # Create a GroupService instance to use internally
        self.group_service = GroupService(db)
        # Create unique index for email and username
        self.users_collection.create_index('email', unique=True)
        self.users_collection.create_index('username', unique=True)

    def is_first_run(self):
        """
        Checks if there are any users in the database.
        Returns True if the users collection is empty, False otherwise.
        """
        return self.users_collection.count_documents({}) == 0

    def create_user(self, username, email, password, is_admin=False, registration_method=None):
        # Check if user already exists
        if self.users_collection.find_one({'$or': [{'email': email}, {'username': username}]}):
            raise ValueError('Username or email already exists')
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # --- NEW: Create a default group for the new user ---
        # First, we need a temporary user ID to be the owner
        temp_user_id = ObjectId()
        default_group_name = f"{username}'s Group"
        group_id = self.group_service.create_group(name=default_group_name, owner_id=temp_user_id)
        
        # Create user document
        user = User(
            _id=temp_user_id, # Use the same ID
            username=username, 
            email=email, 
            password_hash=password_hash,
            is_admin=is_admin,
            registration_method=registration_method,
            # Set the new group as active and add membership
            active_group_id=group_id,
            group_memberships=[{'group_id': group_id, 'role': 'owner'}]
        )
        
        # Insert into database
        self.users_collection.insert_one(user.to_dict())
        return user

    def get_user(self, user_id):
        user_data = self.users_collection.find_one({'_id': ObjectId(user_id)})
        return User.from_dict(user_data) if user_data else None

    def get_user_by_email(self, email):
        user_data = self.users_collection.find_one({'email': email})
        return User.from_dict(user_data) if user_data else None

    def get_user_groups_with_details(self, user):
        """Fetches the group objects for a user's memberships."""
        if not user or not user.group_memberships:
            return []
        group_ids = [gm['group_id'] for gm in user.group_memberships]
        groups_cursor = self.groups_collection.find({'_id': {'$in': group_ids}})
        return list(groups_cursor)

    def switch_active_group(self, user_id, group_id):
        """Updates the user's active group."""
        user = self.get_user(user_id)
        # Ensure the user is actually a member of the group they're switching to
        is_member = any(gm['group_id'] == ObjectId(group_id) for gm in user.group_memberships)
        if not is_member:
            raise PermissionError("User is not a member of this group.")

        result = self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'active_group_id': ObjectId(group_id)}}
        )
        return result.modified_count > 0

    def verify_password(self, user, password):
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash)

    def make_admin(self, user_id):
        result = self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_admin': True}}
        )
        return result.modified_count > 0

    def remove_admin(self, user_id):
        result = self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_admin': False}}
        )
        return result.modified_count > 0

    def list_users(self):
        return [User.from_dict(user_data) for user_data in self.users_collection.find()]