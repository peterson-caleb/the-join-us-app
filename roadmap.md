# Join Us: Product Roadmap

This document outlines the planned features and strategic direction for the Join Us application. The roadmap is organized into phases: foundational work that enables future growth, high-impact features that improve the core user experience, and long-term ideas for future expansion.

---
## ✅ Phase 1: Multi-Tenant Foundation (Completed)

This phase focused on evolving the application from a single-user system into a scalable, multi-tenant platform. These changes are foundational for all future growth and have been completed.

---
## 🚀 Phase 2: Core Experience & Admin Tools (In Progress / Next Up)

With the multi-tenant foundation in place, the focus now shifts to adding high-value features that dramatically improve the workflow for organizers, guests, and administrators.

### ⚠️ Immediate Fixes & Quality of Life
<<<<<<< HEAD
* ~**Fix Contact Editing**: The "Edit" functionality on the main contact list is not working and needs to be repaired.~
=======
* ~ **Fix Contact Editing**: The "Edit" functionality on the main contact list is not working and needs to be repaired.~ 
>>>>>>> origin/main

### Guest Experience Improvements
* **"Plus One" / Guest Count Support**: Allow invitees to RSVP for more than one person, with the confirmed count accurately deducted from the event's capacity.
* **"Add to Calendar" Button**: After a guest confirms, provide a one-click button on the confirmation page to add the event to their Google, Apple, or other calendar via an `.ics` file.
* **RSVP Modification & Cancellation**: Give guests a simple way to change their RSVP from "YES" to "NO", which would automatically free up a spot and trigger an invitation for the next person on the waitlist.
* **See Who's Coming**: On the RSVP page, give organizers the option to show guests a list of others who have confirmed their attendance.

### Organizer Tooling
<<<<<<< HEAD
* ~ **Event Time & Location Fields**: Add dedicated "Start Time" and "Address" fields to events for more complete invitation details. ~
=======
* ~**Event Time & Location Fields**: Add dedicated "Start Time" and "Address" fields to events for more complete invitation details.~
>>>>>>> origin/main
* **Find contacts with tags in the manage invitees window**:Make use of the contact tags we created.
* **Adjustable Invitation Expiry**: Allow organizers to set a custom expiration timeout for invitations on a per-event basis. Include a setting to allow expired guests to RSVP if capacity is still available.
* **Explicit Waitlist Management**: When an event is full, automatically place new "YES" RSVPs onto a waitlist. If a spot opens, the system will automatically promote the first person from the waitlist.
* **Guest List Export (for Check-in)**: Allow hosts to export the final list of confirmed attendees as a CSV or PDF for use at the event.
* **Bulk Contact Import (CSV)**: A crucial time-saver that will allow hosts to upload their entire contact list from a CSV file instead of adding them one by one.

### Admin & Platform Improvements
* **Clickable Global Dashboard Stats**: Make the numbers on the global admin dashboard clickable to show a detailed list of the corresponding items (e.g., click on "Total Users" to go to the user management page).
* **Admin Management of Users & Groups**: Provide a UI for administrators to directly edit and manage user details (e.g., grant admin status) and group settings from the admin panel.

---
## 🔭 Phase 3: Advanced Features & Scalability (Future Vision)

These are larger features that can be explored once the core application is mature and stable.

* **Recurring Events**: Create a system for hosts to set up events that repeat on a schedule (e.g., weekly, monthly), automatically creating new instances of the event and its invitation list.
* **Contact Portability**: Give group owners a tool to move or copy contacts from one of their groups to another, streamlining management for users with multiple projects.
* **Email as an Invitation Channel**: Add email as an alternative to SMS for sending invitations and confirmations, allowing for more detailed messages.
* **Advanced Reporting**: A more detailed analytics page showing trends over time, response rates by contact tag, and other key performance indicators for event hosts.
* **Customizable Message Templates**: Allow hosts to edit the content of the invitation, confirmation, and reminder messages on a per-event basis.