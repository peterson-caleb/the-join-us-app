# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import atexit
import os
from logging.handlers import RotatingFileHandler

class TaskScheduler:
    _instance = None

    def __init__(self):
        # This constructor should only contain one-time setup logic.
        self.scheduler = BackgroundScheduler(daemon=True)
        self.is_running = False
        self.app = None
        self.event_service = None
        self._setup_logging()
        atexit.register(self.shutdown)
        self.logger.info("TaskScheduler instance created.")

    def _setup_logging(self):
        """Sets up a dedicated logger for the scheduler."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        self.logger = logging.getLogger('scheduler')
        # Prevent duplicate handlers if this is called more than once
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler
        file_handler = RotatingFileHandler('logs/scheduler.log', maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    @classmethod
    def get_instance(cls):
        """Gets the singleton instance of the TaskScheduler."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init_app(self, app, event_service):
        """Initializes the scheduler with the Flask app and services."""
        self.logger.info("Initializing scheduler with Flask app context.")
        self.app = app
        self.event_service = event_service
        
        if not self.is_running:
            self.start()

    def start(self):
        """Adds jobs and starts the scheduler if not already running."""
        if self.is_running:
            self.logger.warning("Scheduler is already running. Start ignored.")
            return

        try:
            with self.app.app_context():
                expiry_interval = self.app.config.get('EXPIRY_CHECK_INTERVAL', 1)
                capacity_interval = self.app.config.get('CAPACITY_CHECK_INTERVAL', 1)
                reminder_interval = self.app.config.get('REMINDER_CHECK_INTERVAL', 30)
            
            self.logger.info(f"Configuring jobs - Expiry: {expiry_interval}m, Capacity: {capacity_interval}m, Reminder: {reminder_interval}m")

            self.scheduler.add_job(
                func=self._run_expiry_check, trigger='interval', minutes=expiry_interval,
                id='expiry_check_job', name='Check for expired invitations', replace_existing=True
            )
            self.scheduler.add_job(
                func=self._run_capacity_check, trigger='interval', minutes=capacity_interval,
                id='capacity_check_job', name='Manage event capacity', replace_existing=True
            )
            self.scheduler.add_job(
                func=self._run_reminder_check, trigger='interval', minutes=reminder_interval,
                id='reminder_check_job', name='Send pending reminders', replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            self.logger.info("Scheduler started successfully.")
            self._log_next_run_times()

        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            self.is_running = False

    def _run_job(self, job_func, job_name):
        """Wrapper to execute and log a job function."""
        try:
            with self.app.app_context():
                self.logger.info(f"Running job: '{job_name}'...")
                job_func()
                self.logger.info(f"Job '{job_name}' finished.")
        except Exception as e:
            self.logger.error(f"Error in job '{job_name}': {e}", exc_info=True)

    def _run_expiry_check(self):
        self._run_job(self.event_service.process_expired_invitations, "Check for expired invitations")

    def _run_capacity_check(self):
        # CORRECTED THIS LINE
        self._run_job(self.event_service.manage_event_capacity, "Manage event capacity")
        
    def _run_reminder_check(self):
        if hasattr(self.event_service, 'send_pending_reminders'):
            self._run_job(self.event_service.send_pending_reminders, "Send pending reminders")
        else:
            self.logger.warning("Job 'Send pending reminders' skipped: 'send_pending_reminders' method not found in EventService.")

    def _log_next_run_times(self):
        """Logs the next scheduled run time for all jobs."""
        if not self.is_running: return
        for job in self.scheduler.get_jobs():
            self.logger.info(f"Job '{job.name}' next scheduled run: {job.next_run_time}")

    def shutdown(self):
        """Shuts down the scheduler gracefully."""
        if self.is_running:
            self.logger.info("Shutting down scheduler...")
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("Scheduler shutdown complete.")