# app/__init__.py
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_required
from .config import Config
import logging
from datetime import datetime
import os

mongo = PyMongo()
login_manager = LoginManager()
event_service = None
contact_service = None
sms_service = None
user_service = None
registration_code_service = None
task_scheduler = None
message_log_service = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Setup basic app logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MongoDB
    mongo.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Initialize services
    global event_service, contact_service, sms_service, user_service, registration_code_service, task_scheduler, message_log_service
    from .services.event_service import EventService
    from .services.contact_service import ContactService
    from .services.sms_service import SMSService
    from .services.user_service import UserService
    from .services.registration_code_service import RegistrationCodeService
    from .services.message_log_service import MessageLogService
    from .scheduler import TaskScheduler
    
    # Initialize services that don't depend on others first
    message_log_service = MessageLogService(mongo.db)
    
    # Initialize SMS service with the new guardrail configuration
    sms_service = SMSService(
        sid=app.config['TWILIO_SID'],
        auth_token=app.config['TWILIO_AUTH_TOKEN'],
        twilio_phone=app.config['TWILIO_PHONE'],
        message_log_service=message_log_service,
        base_url=app.config['BASE_URL'],
        enabled=app.config['SMS_ENABLED'],
        hourly_limit=app.config['SMS_HOURLY_LIMIT'],
        daily_limit=app.config['SMS_DAILY_LIMIT']
    )
    
    # Initialize other services that depend on the SMS service
    event_service = EventService(
        db=mongo.db,
        sms_service=sms_service,
        invitation_expiry_hours=app.config['INVITATION_EXPIRY_HOURS']
    )
    contact_service = ContactService(mongo.db)
    user_service = UserService(mongo.db)
    registration_code_service = RegistrationCodeService(mongo.db)

    # Initialize scheduler with app context
    if app.config.get('SCHEDULER_ENABLED', True):
        # This check prevents the scheduler from starting twice in debug mode
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            task_scheduler = TaskScheduler.get_instance()
            task_scheduler.init_app(app, event_service) 
            app.logger.info('Task scheduler initialized and started.')

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return user_service.get_user(user_id)

    @app.context_processor
    def inject_current_year():
        # Corrected this line
        return {'current_year': datetime.utcnow().year}

    # Register blueprints
    from .routes.event_routes import bp as event_bp
    from .routes.contact_routes import bp as contact_bp
    from .routes.sms_routes import bp as sms_bp
    from .routes.auth_routes import bp as auth_bp
    
    app.register_blueprint(event_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(sms_bp)
    app.register_blueprint(auth_bp)

    @app.route('/')
    @login_required
    def home():
        return render_template('home.html')

    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    with app.app_context():
        # Auto-create admin user from env vars if no users exist
        if user_service.is_first_run():
            admin_username = os.getenv('ADMIN_USERNAME')
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            if admin_username and admin_email and admin_password:
                try:
                    user_service.create_user(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password,
                        is_admin=True,
                        registration_method='auto_created'
                    )
                    app.logger.info(f"Admin user '{admin_username}' created automatically.")
                except ValueError as e:
                    app.logger.error(f"Could not auto-create admin user: {e}")

    return app