# 🗺️ Hybrid Guest Account Feature Roadmap

This document outlines the plan for implementing an optional guest account system. The goal is to enhance the experience for repeat guests by giving them a dashboard to track their event invitations, without sacrificing the simplicity and high response rate of the current SMS-based RSVP system for one-time guests.

---

## 1. Update the Data Model: Link Contacts to Users

The core of this feature is creating a clear link between a `Contact` (who receives an SMS) and a `User` (who can log in).

* **Action**: Add a new, optional field `user_id` to the `contacts` collection schema.
* **Default State**: This field will be `null` or absent for all existing contacts and for any new contacts who sign up via the public "Join List" page.
* **Population**: The `user_id` will only be set when a guest who has received an invitation completes the new guest registration process.

---

## 2. Modify the RSVP Confirmation Page

The connection between a passive contact and an active user will be made on the RSVP confirmation page (`rsvp_confirmation.html`). This is the point of conversion.

* **Action**: After a guest successfully RSVPs, the confirmation page will display the "Thank You" message as it does now.
* **New Element**: A new call-to-action will be added below the success message.
    > "Want to keep track of your events in one place? **Create a free account.**"

---

## 3. Create a Guest Registration Flow

The "Create a free account" link will trigger a new, specialized registration process designed specifically for guests.

* **Trigger**: The link will pass the guest's unique `rsvp_token` to a new registration page (e.g., `/register-guest?token=...`).
* **UI**: The new page will use the token to look up and pre-fill the guest's name and phone number. The guest will only need to provide an **email** and create a **password**.
* **Backend Logic**: Upon form submission, the system will:
    1.  Create a new non-admin entry in the **`users` collection**.
    2.  Find the guest's record in the **`contacts` collection** (using the token) and update it with their new `user_id`.
    3.  Automatically log the new user into their account.

---

## 4. Build the Guest Dashboard

Once registered, the guest will be redirected to their personal dashboard, a new, central hub for their event activity.

* **Route**: Create a new, login-protected route (e.g., `/dashboard`).
* **Backend Logic**: The dashboard will:
    1.  Use the logged-in user's ID to find their linked `contact` record.
    2.  Use the contact's phone number to find all event invitations associated with them across all events.
* **UI**: The page will display a clean list of the user's invitations, likely separated into "Upcoming" and "Past" events, showing their RSVP status for each.