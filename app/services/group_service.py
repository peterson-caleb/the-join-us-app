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

    def get_groups_by_owner(self, owner_id):
        """Retrieves all groups owned by a specific user."""
        return list(self.groups_collection.find({'owner_id': ObjectId(owner_id)}))

    def update_group(self, group_id, owner_id, data):
        """Updates a group's data after verifying ownership."""
        result = self.groups_collection.update_one(
            {'_id': ObjectId(group_id), 'owner_id': ObjectId(owner_id)},
            {'$set': data}
        )
        return result.modified_count > 0

    def delete_group(self, group_id, owner_id):
        """Deletes a group after verifying ownership."""
        result = self.groups_collection.delete_one(
            {'_id': ObjectId(group_id), 'owner_id': ObjectId(owner_id)}
        )
        return result.deleted_count > 0
