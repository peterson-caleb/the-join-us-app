# Join Us: Automated RSVP & Event Management System 💌

Join Us is a collaborative, multi-tenant web application designed to streamline event management. It features an intelligent, automated system for sending out RSVP invitations via SMS in prioritized batches, ensuring events fill up efficiently without manual intervention.

Organize your work in isolated **Groups**. Invite team members to collaborate on events and contact lists. The system automatically manages a master contact list per group, builds event-specific invitee lists, and then sends out invitations based on event capacity and a user-defined priority queue. As guests respond or invitations expire, the system intelligently sends out the next batch of invitations until the event is full.

## ✨ Key Features

-   **Multi-Tenancy with Groups**: Create and manage isolated workspaces ("Groups") for different teams, projects, or organizations. All events and contacts are scoped per group.
-   **Collaborative Tools**: Invite other registered users to become members of your groups, allowing teams to manage events together.
-   **Automated Invitation System**: Automatically sends SMS invitations based on event capacity and guest priority.
-   **Priority Queue**: Manage invitees in a prioritized, drag-and-drop list for each event.
-   **SMS Integration**: Uses Twilio to send invitations with unique RSVP links, confirmations, and automated reminders.
-   **Per-Group SMS Quotas**: Each group has its own SMS sending limits, with a platform-wide safety net.
-   **Admin System Panel**: A dashboard for site administrators to view all groups on the platform and join them for support purposes.
-   **Contact Management**: Maintain a master list of contacts with tagging for each group.
-   **Secure User Management**: Features a secure login system. New user registration is controlled via admin-generated invitation codes.
-   **Deployment Ready**: Comes with a Dockerfile and render.yaml for quick and easy deployment to cloud services like Render.

## ⚙️ Tech Stack

-   **Backend**: Python, Flask
-   **Database**: MongoDB (with Flask-PyMongo)
-   **SMS & Communication**: Twilio API
-   **Task Scheduling**: APScheduler
-   **Frontend**: HTML, Bootstrap 5, JavaScript, jQuery
-   **Deployment**: Gunicorn, Docker

## 🚀 Getting Started

Follow these instructions to get a local copy up and running for development and testing.

### Prerequisites

-   Python 3.12+
-   A running MongoDB instance (local or a free cloud instance like MongoDB Atlas)
-   A Twilio account with an active phone number, Account SID, and Auth Token.

### 1. Clone the Repository
*(Instructions remain the same)*

### 2. Set Up a Virtual Environment
*(Instructions remain the same)*

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root of the project and populate it with your credentials.

```ini
# .env file
# Flask Configuration
SECRET_KEY='a_very_long_and_random_secret_key'
BASE_URL='http://127.0.0.1:5000'

# MongoDB Configuration
MONGO_URI='your_mongodb_connection_string'

# Twilio Credentials
TWILIO_SID='your_twilio_account_sid'
TWILIO_AUTH_TOKEN='your_twilio_auth_token'
TWILIO_PHONE='+1234567890'

# --- SMS Guardrails ---
# Master switch for the entire SMS service.
SMS_ENABLED=false
# Global platform-wide limits (master safety net).
SMS_HOURLY_LIMIT=1000
SMS_DAILY_LIMIT=5000
# System-wide protection against sending too many messages to a single number.
RECIPIENT_SPAM_LIMIT=5
RECIPIENT_SPAM_WINDOW_MINUTES=10

# System & Scheduler Configuration
INVITATION_EXPIRY_HOURS=24
SCHEDULER_ENABLED=true
EXPIRY_CHECK_INTERVAL=1
CAPACITY_CHECK_INTERVAL=1
REMINDER_CHECK_INTERVAL=30
```

### 5. Create the First Admin User
Run the `create_admin.py` script from your terminal and follow the prompts. This will also create a default group for the admin user.
```bash
python create_admin.py
```

### 6. Run the Application
```bash
flask run
```
The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 📖 How to Use

1.  **Log In / Register**: Access the web interface. Log in with your credentials or register with an invitation code. Upon first login, a default "Personal Group" is created for you.

2.  **Manage Groups**: Navigate to the "Manage Groups" page from the group switcher dropdown in the navbar.
    * Create new groups for different teams or projects.
    * Invite existing users to your groups by email.
    * Switch your active group using the dropdown. All actions you take will be within the context of your active group.

3.  **Add Contacts**: Navigate to the Contacts page to build your master list of guests for the **active group**. You can add names, phone numbers, and tags.

4.  **Create an Event**: Go to the Events page to create a new event within the **active group**, specifying its name, date, and total capacity.

5.  **Manage Invitees**:
    * Click "Manage Invitees" for your new event.
    * Use the "Add Invitees" panel to select contacts from your group's master list.
    * Drag and drop the invitees to set their invitation priority.

6.  **Start Automation**: When you're ready, click "Start Automated Invites". The system will now manage the RSVP process for you within that event.


# 📦 Deployment
This application is configured for deployment using Docker.

Dockerfile: A Dockerfile is included to containerize the application.

Render: A render.yaml file is provided for one-click deployment on the Render platform. Simply connect your Git repository to Render and use this file as the blueprint.

# 🛠️ Scripts
This project includes a couple of helpful utility scripts:

create_admin.py: A command-line script to create the first administrative user. Necessary for the initial setup.

export_source.py: A developer utility to bundle all relevant source code into a single .txt file for easy inspection or sharing.

