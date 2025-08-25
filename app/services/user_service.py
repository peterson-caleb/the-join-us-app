# app/services/user_service.py
from bson import ObjectId
import bcrypt
from ..models.user import User
from .group_service import GroupService
import secrets

class UserService:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.groups_collection = db['groups']
        self.group_service = GroupService(db)
        self.users_collection.create_index('email', unique=True)
        self.users_collection.create_index('username', unique=True)
        self.users_collection.create_index('contact_collection_token', unique=True, sparse=True)

    def switch_active_group(self, user_id, group_id):
        """Updates the user's active group."""
        user_oid = ObjectId(user_id)
        group_oid = ObjectId(group_id) if group_id else None

        if group_oid:
            group = self.groups_collection.find_one({"_id": group_oid})
            if not group or group.get('owner_id') != user_oid:
                raise PermissionError("User does not own this group.")

        result = self.users_collection.update_one(
            {'_id': user_oid},
            {'$set': {'active_group_id': group_oid}}
        )
        return result.modified_count > 0 or True

    def get_all_groups_with_owners(self):
        """Fetches all groups and enriches them with owner's username."""
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'owner_id',
                    'foreignField': '_id',
                    'as': 'owner_details'
                }
            },
            {
                '$unwind': {
                    'path': '$owner_details',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    'name': 1,
                    'created_at': 1,
                    'owner_id': 1,
                    'owner_username': '$owner_details.username'
                }
            },
            {
                '$sort': {'created_at': -1}
            }
        ]
        return list(self.groups_collection.aggregate(pipeline))

    def is_first_run(self):
        return self.users_collection.count_documents({}) == 0

    def create_user(self, username, email, password, name, is_admin=False, registration_method=None):
        if self.users_collection.find_one({'$or': [{'email': email}, {'username': username}]}):
            raise ValueError('Username or email already exists')
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        temp_user_id = ObjectId()
        default_group_name = f"{name}'s Personal Group"
        group_id = self.group_service.create_group(name=default_group_name, owner_id=temp_user_id)
        
        user = User(
            _id=temp_user_id,
            username=username, 
            email=email, 
            password_hash=password_hash,
            name=name,
            is_admin=is_admin,
            registration_method=registration_method,
            active_group_id=group_id,
            contact_collection_token=secrets.token_urlsafe(24)
        )
        
        self.users_collection.insert_one(user.to_dict())
        return user
    
    def create_group_for_user(self, user_id, group_name):
        user_oid = ObjectId(user_id)
        group_id = self.group_service.create_group(name=group_name, owner_id=user_oid)
        if not group_id:
            raise Exception("Failed to create the group document.")

        result = self.users_collection.update_one(
            {'_id': user_oid},
            {'$set': {'active_group_id': group_id}}
        )
        return result.modified_count > 0

    def get_user(self, user_id):
        user_data = self.users_collection.find_one({'_id': ObjectId(user_id)})
        return User.from_dict(user_data) if user_data else None

    def get_user_by_email(self, email):
        user_data = self.users_collection.find_one({'email': email})
        return User.from_dict(user_data) if user_data else None

    def get_user_by_contact_token(self, token):
        user_data = self.users_collection.find_one({'contact_collection_token': token})
        return User.from_dict(user_data) if user_data else None

    def verify_password(self, user, password):
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash)