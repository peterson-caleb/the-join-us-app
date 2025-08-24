# Join Us: Automated RSVP & Event Management System 💌

Join Us is a web application designed to streamline event management for individual organizers.
It features an intelligent, automated system for sending out RSVP invitations via SMS in prioritized batches, ensuring events fill up efficiently without manual intervention.

Organize your work in isolated **Groups**. Each group you create allows you to manage a distinct set of events and draw from your personal contact list.
[cite_start]The system automatically builds event-specific invitee lists from your "My Contacts" list and then sends out invitations based on event capacity and a user-defined priority queue. [cite: 4, 66]
[cite_start]As guests respond or invitations expire, the system intelligently sends out the next batch of invitations until the event is full. [cite: 5]

## ✨ Key Features

-   [cite_start]**Multi-Tenancy with Groups**: Create and manage isolated workspaces ("Groups") for different projects or organizations under a single user account. [cite: 6] [cite_start]All events are scoped per group. [cite: 7]
-   **User-Owned Contacts**: Maintain a central "My Contacts" list for your user account, which can be used across all your groups.
-   [cite_start]**Automated Invitation System**: Automatically sends SMS invitations based on event capacity and guest priority. [cite: 8]
-   [cite_start]**Priority Queue**: Manage invitees in a prioritized, drag-and-drop list for each event. [cite: 9]
-   [cite_start]**SMS Integration**: Uses Twilio to send invitations with unique RSVP links, confirmations, and automated reminders. [cite: 10]
-   [cite_start]**Per-Group SMS Quotas**: Each group has its own SMS sending limits, with a platform-wide safety net. [cite: 11]
-   **Admin System Panel**: A dashboard for site administrators to view all groups and users on the platform.
-   **Secure User Management**: Features a secure login system. [cite_start]New user registration is controlled via admin-generated invitation codes. [cite: 14]
-   [cite_start]**Deployment Ready**: Comes with a Dockerfile and render.yaml for quick and easy deployment to cloud services like Render. [cite: 15]

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
-   [cite_start]A Twilio account with an active phone number, Account SID, and Auth Token. [cite: 17]

### 1. Clone the Repository
*(Instructions remain the same)*

### 2. Set Up a Virtual Environment
*(Instructions remain the same)*

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```