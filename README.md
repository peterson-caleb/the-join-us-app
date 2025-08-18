You are absolutely right. My apologies, that's a mistake in the formatting I provided.

The issue is that I used the # symbol for the bullet points under "Prerequisites." In many Markdown renderers, like GitHub's, a # at the start of a line is strictly interpreted as a heading, which is why it made the text large and bold.

To fix this, those lines should use an asterisk * instead.

Here is the fully corrected version. This will render properly on GitHub. Please try pasting this into your README.md file.

Markdown

# Join Us: Automated RSVP & Event Management System 💌

Join Us is a web application designed to streamline event management. It features an intelligent, automated system for sending out RSVP invitations via SMS in prioritized batches, ensuring events fill up efficiently without manual intervention.

The system manages a master contact list, builds event-specific invitee lists, and then automatically sends out invitations based on event capacity and a user-defined priority queue. As guests respond or invitations expire, the system intelligently sends out the next batch of invitations until the event is full.

***

## ✨ Key Features

* **Automated Invitation System**: Automatically sends SMS invitations based on event capacity and guest priority.
* **Priority Queue**: Manage invitees in a prioritized, drag-and-drop list for each event.
* **SMS Integration**: Uses **Twilio** to send invitations with unique RSVP links, confirmations, and automated reminders.
* **Web-Based RSVP**: Guests receive a unique link to a simple, mobile-friendly webpage to confirm or decline their attendance.
* **Contact Management**: Maintain a master list of contacts with tagging for easy filtering and organization.
* **Background Task Scheduling**: A robust scheduler automatically handles expired invitations and sends new ones to fill available spots.
* **Secure User Management**: Features a secure login system and controls new user registration via admin-generated invitation codes.
* **Deployment Ready**: Comes with a `Dockerfile` and `render.yaml` for quick and easy deployment to cloud services like Render.

***

## ⚙️ Tech Stack

* **Backend**: Python, Flask
* **Database**: MongoDB (with Flask-PyMongo)
* **SMS & Communication**: Twilio API
* **Task Scheduling**: APScheduler
* **Frontend**: HTML, Bootstrap 5, JavaScript, jQuery
* **Deployment**: Gunicorn, Docker

***

## 🚀 Getting Started

Follow these instructions to get a local copy up and running for development and testing.

### Prerequisites

* Python 3.12+
* A running MongoDB instance (local or a free cloud instance like MongoDB Atlas)
* A Twilio account with an active phone number, Account SID, and Auth Token.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd rsvp-priority
2. Set Up a Virtual Environment
It's highly recommended to use a virtual environment.

Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
macOS / Linux:

Bash

python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Configure Environment Variables
Create a file named .env in the root of the project and populate it with your credentials and configuration.

Code snippet

# .env file
# Flask Configuration
SECRET_KEY='a_very_long_and_random_secret_key'
BASE_URL='[http://127.0.0.1:5000](http://127.0.0.1:5000)' # Change if running on a different port or domain

# MongoDB Configuration
MONGO_URI='your_mongodb_connection_string'

# Twilio Credentials
TWILIO_SID='your_twilio_account_sid'
TWILIO_AUTH_TOKEN='your_twilio_auth_token'
TWILIO_PHONE='+1234567890' # Your Twilio phone number in E.164 format

# System & Scheduler Configuration
INVITATION_EXPIRY_HOURS=24
SCHEDULER_ENABLED=true
EXPIRY_CHECK_INTERVAL=1      # Check for expired invitations every 1 minute
CAPACITY_CHECK_INTERVAL=1    # Check event capacity and send new invites every 1 minute
REMINDER_CHECK_INTERVAL=30   # Send reminders for pending RSVPs every 30 minutes
5. Create the First Admin User
Run the create_admin.py script from your terminal and follow the prompts to create your initial administrator account.

Bash

python create_admin.py
6. Run the Application
You can now start the Flask development server.

Bash

flask run
The application will be available at http://127.0.0.1:5000.

📖 How to Use
Log In: Access the web interface and log in with the admin credentials you created.

Add Contacts: Navigate to the Contacts page to build your master list of guests. You can add names, phone numbers, and tags (e.g., family, vip, work).

Create an Event: Go to the Events page and create a new event, specifying its name, date, and total capacity.

Manage Invitees:

Click "Manage Invitees" for your new event.

Use the "Add Invitees" panel to select contacts from your master list and add them to the event's invitee list.

Drag and drop the invitees in the "Current Invitees" list to set their invitation priority. The system sends invitations from the top of the list downwards.

Start Automation: When you're ready, click "Start Automated Invites". The system will now:

Send out the first batch of invitations to fill the event's capacity.

Automatically check for expired invitations.

Send new invitations from the priority list as spots open up from "NO" responses or expired invites.

📦 Deployment
This application is configured for deployment using Docker.

Dockerfile: A Dockerfile is included to containerize the application.

Render: A render.yaml file is provided for one-click deployment on the Render platform. Simply connect your Git repository to Render and use this file as the blueprint.

🛠️ Scripts
This project includes a couple of helpful utility scripts:

create_admin.py: A command-line script to create the first administrative user. Necessary for the initial setup.

export_source.py: A developer utility to bundle all relevant source code into a single .txt file for easy inspection or sharing.