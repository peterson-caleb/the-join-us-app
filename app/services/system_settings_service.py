# app/services/system_settings_service.py
from pymongo.database import Database
from flask import current_app

class SystemSettingsService:
    """
    Manages platform-wide settings stored in the database.
    Includes a simple in-memory cache to reduce database queries.
    """
    def __init__(self, db: Database):
        self.db = db
        self.settings_collection = db['system_settings']
        self._cache = {}
        self._defaults = {
            'sms_hourly_limit': current_app.config.get('SMS_HOURLY_LIMIT', 1000),
            'sms_daily_limit': current_app.config.get('SMS_DAILY_LIMIT', 5000),
        }
        self.load_settings_into_cache()

    def load_settings_into_cache(self):
        """Loads all settings from the database into the local cache."""
        settings = self.settings_collection.find({})
        for setting in settings:
            self._cache[setting['_id']] = setting['value']
        print("System settings loaded into cache.")

    def get_setting(self, key: str):
        """
        Retrieves a setting value, first from cache, then from the database.
        Falls back to a default value if not found anywhere.
        """
        # 1. Try cache first
        if key in self._cache:
            return self._cache[key]
        
        # 2. If not in cache, try database
        setting = self.settings_collection.find_one({'_id': key})
        if setting:
            self._cache[key] = setting['value']
            return setting['value']
            
        # 3. If not in DB, use the hardcoded default
        return self._defaults.get(key)

    def get_all_settings(self):
        """Returns a dictionary of all settings, combining DB values and defaults."""
        all_settings = self._defaults.copy()
        # Update with cached (database) values
        all_settings.update(self._cache)
        return all_settings

    def update_setting(self, key: str, value):
        """
        Updates a setting in the database and refreshes the cache.
        The `_id` of the document is the setting key.
        """
        # Coerce value to the correct type based on the default
        default_value = self._defaults.get(key)
        if default_value is not None:
            try:
                value = type(default_value)(value)
            except (ValueError, TypeError):
                # If coercion fails, fall back to string
                pass

        self.settings_collection.update_one(
            {'_id': key},
            {'$set': {'value': value}},
            upsert=True
        )
        # Update cache immediately
        self._cache[key] = value
        return True
