# app/services/user_service.py
from bson import ObjectId
import bcrypt
from ..models.user import User
from .group_service import GroupService

class UserService:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.groups_collection = db['groups']
        self.group_service = GroupService(db)
        self.users_collection.create_index('email', unique=True)
        self.users_collection.create_index('username', unique=True)

    # --- NEW METHOD (Moved from GroupService) ---
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

    def create_user(self, username, email, password, is_admin=False, registration_method=None):
        if self.users_collection.find_one({'$or': [{'email': email}, {'username': username}]}):
            raise ValueError('Username or email already exists')
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        temp_user_id = ObjectId()
        default_group_name = f"{username}'s Group"
        group_id = self.group_service.create_group(name=default_group_name, owner_id=temp_user_id)
        
        user = User(
            _id=temp_user_id,
            username=username, 
            email=email, 
            password_hash=password_hash,
            is_admin=is_admin,
            registration_method=registration_method,
            active_group_id=group_id,
            group_memberships=[{'group_id': group_id, 'role': 'owner'}]
        )
        
        self.users_collection.insert_one(user.to_dict())
        return user
    
    def create_group_for_user(self, user_id, group_name):
        group_id = self.group_service.create_group(name=group_name, owner_id=ObjectId(user_id))
        if not group_id:
            raise Exception("Failed to create the group document.")

        new_membership = {'group_id': group_id, 'role': 'owner'}
        result = self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$push': {'group_memberships': new_membership},
                '$set': {'active_group_id': group_id}
            }
        )
        return result.modified_count > 0

    def add_admin_to_group(self, admin_user_id, group_id_to_join):
        admin_user = self.get_user(admin_user_id)
        if not admin_user or not admin_user.is_admin:
            raise PermissionError("Only administrators can perform this action.")
        
        is_member = any(gm['group_id'] == ObjectId(group_id_to_join) for gm in admin_user.group_memberships)
        if is_member:
            return True

        new_membership = {'group_id': ObjectId(group_id_to_join), 'role': 'member'}
        result = self.users_collection.update_one(
            {'_id': admin_user._id},
            {'$push': {'group_memberships': new_membership}}
        )
        return result.modified_count > 0

    def invite_user_to_group(self, inviter_user, invited_email, group_id):
        is_owner = any(gm['group_id'] == ObjectId(group_id) and gm['role'] == 'owner' for gm in inviter_user.group_memberships)
        
        if not is_owner and not inviter_user.is_admin:
            raise PermissionError("Only group owners or administrators can invite new members.")

        invited_user = self.get_user_by_email(invited_email)
        if not invited_user:
            raise ValueError(f"No user found with the email: {invited_email}")

        is_member = any(gm['group_id'] == ObjectId(group_id) for gm in invited_user.group_memberships)
        if is_member:
            raise ValueError("This user is already a member of the group.")
        
        if ObjectId(group_id) in invited_user.group_invitations:
            raise ValueError("This user has already been invited to the group.")

        self.users_collection.update_one(
            {'_id': invited_user._id},
            {'$push': {'group_invitations': ObjectId(group_id)}}
        )
        return True

    def accept_group_invitation(self, user_id, group_id):
        user = self.get_user(user_id)
        if ObjectId(group_id) not in user.group_invitations:
            raise ValueError("No pending invitation found for this group.")
        
        new_membership = {'group_id': ObjectId(group_id), 'role': 'member'}
        self.users_collection.update_one(
            {'_id': user._id},
            {
                '$pull': {'group_invitations': ObjectId(group_id)},
                '$push': {'group_memberships': new_membership},
                '$set': {'active_group_id': ObjectId(group_id)}
            }
        )
        return True

    def decline_group_invitation(self, user_id, group_id):
        self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$pull': {'group_invitations': ObjectId(group_id)}}
        )
        return True

    def get_user(self, user_id):
        user_data = self.users_collection.find_one({'_id': ObjectId(user_id)})
        return User.from_dict(user_data) if user_data else None

    def get_user_by_email(self, email):
        user_data = self.users_collection.find_one({'email': email})
        return User.from_dict(user_data) if user_data else None

    def get_user_groups_with_details(self, user):
        if not user or not user.group_memberships:
            return []
        group_ids = [gm['group_id'] for gm in user.group_memberships]
        groups_cursor = self.groups_collection.find({'_id': {'$in': group_ids}})
        return list(groups_cursor)

    def switch_active_group(self, user_id, group_id):
        user = self.get_user(user_id)
        is_member = any(gm['group_id'] == ObjectId(group_id) for gm in user.group_memberships)
        if not is_member:
            raise PermissionError("User is not a member of this group.")

        if str(user.active_group_id) == group_id:
            return True

        result = self.users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'active_group_id': ObjectId(group_id)}}
        )
        return result.modified_count > 0

    def verify_password(self, user, password):
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash)