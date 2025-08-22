# app/services/group_service.py
from bson import ObjectId
from ..models.group import Group

class GroupService:
    def __init__(self, db):
        self.db = db
        self.groups_collection = db['groups']
        # --- REMOVED: self.users_collection is no longer needed here ---

    def create_group(self, name, owner_id):
        """Creates a new group and returns its ID."""
        group = Group(name=name, owner_id=owner_id)
        result = self.groups_collection.insert_one(group.to_dict())
        return result.inserted_id

    def get_group(self, group_id):
        """Retrieves a single group by its ID."""
        group_data = self.groups_collection.find_one({"_id": ObjectId(group_id)})
        return Group.from_dict(group_data) if group_data else None

    # --- MOVED: The get_all_groups_with_owners method has been moved to UserService ---
        
    def get_pending_invitations_for_user(self, user):
        """Fetches full group details for a user's pending invitations."""
        if not user or not user.group_invitations:
            return []
        
        group_ids = user.group_invitations
        return list(self.groups_collection.find({'_id': {'$in': group_ids}}))