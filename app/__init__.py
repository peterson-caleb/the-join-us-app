# app/__init__.py
from flask import Flask, render_template, g
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_required, current_user, login_user
from .config import Config
import logging
from datetime import datetime
import os
import sys

mongo = PyMongo()
login_manager = LoginManager()
event_service = None
contact_service = None
sms_service = None
user_service = None
registration_code_service = None
task_scheduler = None
message_log_service = None
dashboard_service = None
group_service = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(level=logging.INFO)
    
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Initialize services
    global event_service, contact_service, sms_service, user_service, registration_code_service, task_scheduler, message_log_service, dashboard_service, group_service
    from .services.event_service import EventService
    from .services.contact_service import ContactService
    from .services.sms_service import SMSService
    from .services.user_service import UserService
    from .services.registration_code_service import RegistrationCodeService
    from .services.message_log_service import MessageLogService
    from .services.dashboard_service import DashboardService
    from .services.group_service import GroupService
    from .scheduler import TaskScheduler
    
    message_log_service = MessageLogService(mongo.db)
    dashboard_service = DashboardService(mongo.db)
    group_service = GroupService(mongo.db)
    
    sms_service = SMSService(
        sid=app.config['TWILIO_SID'],
        auth_token=app.config['TWILIO_AUTH_TOKEN'],
        twilio_phone=app.config['TWILIO_PHONE'],
        message_log_service=message_log_service,
        base_url=app.config['BASE_URL'],
        enabled=app.config['SMS_ENABLED']
    )
    
    event_service = EventService(
        db=mongo.db,
        invitation_expiry_hours=app.config['INVITATION_EXPIRY_HOURS']
    )
    contact_service = ContactService(mongo.db)
    user_service = UserService(mongo.db)
    registration_code_service = RegistrationCodeService(mongo.db)

    if app.config.get('SCHEDULER_ENABLED', True):
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            task_scheduler = TaskScheduler.get_instance()
            task_scheduler.init_app(app, event_service, sms_service) 
            app.logger.info('Task scheduler initialized and started.')

    @login_manager.user_loader
    def load_user(user_id):
        return user_service.get_user(user_id)
    
    @app.before_request
    def load_user_context():
        g.user_groups = []
        g.pending_invitations = []
        if current_user.is_authenticated:
            # Always get fresh data from database for the current request
            g.user_groups = user_service.get_user_groups_with_details(current_user)
            g.pending_invitations = group_service.get_pending_invitations_for_user(current_user)

            # Self-healing logic: Check if active_group_id is still valid
            if current_user.active_group_id:
                current_membership_ids = [str(group['_id']) for group in g.user_groups]
                if str(current_user.active_group_id) not in current_membership_ids:
                    # The active group is no longer valid, fix it
                    new_active_group_id = g.user_groups[0]['_id'] if g.user_groups else None
                    
                    # Update the database
                    user_service.switch_active_group(current_user.id, new_active_group_id)
                    
                    # Refresh the user object in the session
                    refreshed_user = user_service.get_user(current_user.id)
                    if refreshed_user:
                        # This updates the session with the fresh user object
                        login_user(refreshed_user, fresh=False)
                    
                    app.logger.warning(f"Corrected orphaned active_group_id for user {current_user.id}")

    @app.context_processor
    def inject_global_variables():
        return {
            'current_year': datetime.utcnow().year,
            'user_groups': g.get('user_groups', []),
            'pending_invitations': g.get('pending_invitations', [])
        }

    # Register blueprints
    from .routes.event_routes import bp as event_bp
    from .routes.contact_routes import bp as contact_bp
    from .routes.sms_routes import bp as sms_bp
    from .routes.auth_routes import bp as auth_bp
    from .routes.dashboard_routes import bp as dashboard_bp
    from .routes.group_routes import bp as group_bp
    from .routes.admin_routes import bp as admin_bp
    
    app.register_blueprint(event_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(sms_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    @login_required
    def home():
        return render_template('home.html')

    # Error handlers remain the same...
    
    return app