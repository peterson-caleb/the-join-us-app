# app/services/group_service.py
from bson import ObjectId
from ..models.group import Group

class GroupService:
    def __init__(self, db):
        self.db = db
        self.groups_collection = db['groups']

    def create_group(self, name, owner_id):
        """Creates a new group and returns its ID."""
        group = Group(name=name, owner_id=owner_id)
        result = self.groups_collection.insert_one(group.to_dict())
        return result.inserted_id

    def get_group(self, group_id):
        """Retrieves a single group by its ID."""
        group_data = self.groups_collection.find_one({"_id": ObjectId(group_id)})
        return Group.from_dict(group_data) if group_data else None

    def get_groups_for_user(self, user_id):
        """Retrieves all groups a user is a member of."""
        user_object_id = ObjectId(user_id)
        
        pipeline = [
            {
                '$match': {
                    'group_memberships.user_id': user_object_id
                }
            },
            {
                '$lookup': {
                    'from': 'groups',
                    'localField': 'group_memberships.group_id',
                    'foreignField': '_id',
                    'as': 'group_details'
                }
            },
            {
                '$unwind': '$group_details'
            },
            {
                '$replaceRoot': {
                    'newRoot': '$group_details'
                }
            }
        ]
        # This is a conceptual pipeline. For now, we query the user document directly.
        # This will be simpler once group memberships are on the user object.
        # The logic will be updated in UserService.
        return [] # Placeholder, real logic will be in UserService