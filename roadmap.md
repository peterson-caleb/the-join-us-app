# Join Us: Product Roadmap

This document outlines the planned features and strategic direction for the Join Us application. The roadmap is organized into phases: foundational work that enables future growth, high-impact features that improve the core user experience, and long-term ideas for future expansion.

---
## ✅ Completed: Foundational Work

This phase focused on evolving the application from a single-user system into a scalable, multi-tenant platform. These changes are foundational for all future growth.

### 1. Multi-Tenancy with "Groups"
Allowed different users or organizations to use the app in complete isolation from one another.

* **Data Scoping**: Introduced a `group_id` to the `events` and `contacts` collections.
* **User & Group Management**: Created a `groups` collection and updated the `users` model so that users can create, own, and be invited to different groups. Implemented a group invitation system.
* **"Group-Aware" Logic**: Updated all service-layer queries to only fetch and modify data for the user's currently active group.
* **Admin Oversight**: Added a system panel for admins to view all groups and join them for support.
* **UI Group Switcher**: Added a dropdown menu to the main navigation for switching between groups.

### 2. Per-Group SMS Quotas & Guardrails
Implemented intelligent, group-specific limits to ensure fair use and platform stability.

* **Per-Group Quotas**: Each `group` document now has its own configurable SMS limits.
* **Recipient Spam Protection**: A new system-wide guardrail prevents any single phone number from receiving an excessive number of messages in a short period.

---
## 🚀 Now: Enhancing the Core Experience

With the multi-tenant foundation in place, the focus now shifts to adding high-value features that dramatically improve the workflow for both event hosts and their guests.

### Guest Experience Improvements
* **"Plus One" / Guest Count Support**: Allow invitees to RSVP for more than one person, with the confirmed count accurately deducted from the event's capacity.
* **"Add to Calendar" Button**: After a guest confirms, provide a one-click button on the confirmation page to add the event to their Google, Apple, or other calendar via an `.ics` file.
* **RSVP Modification & Cancellation**: Give guests a simple way to change their RSVP from "YES" to "NO", which would automatically free up a spot and trigger an invitation for the next person on the waitlist.

### Organizer Tooling
* **Explicit Waitlist Management**: When an event is full, automatically place new "YES" RSVPs onto a waitlist. If a spot opens, the system will automatically promote the first person from the waitlist.
* **Guest List Export (for Check-in)**: Allow hosts to export the final list of confirmed attendees as a CSV or PDF for use at the event.
* **Bulk Contact Import (CSV)**: A crucial time-saver that will allow hosts to upload their entire contact list from a CSV file instead of adding them one by one.

---
## 🔭 Later: Future Vision

These are larger features that can be explored once the core application is mature and stable.

* **QR Code Check-in System**: Generate a unique QR code for each confirmed guest. The host can then use a simple web interface on their phone to scan guests in at the door for a seamless check-in experience.
* **Email as an Invitation Channel**: Add email as an alternative to SMS for sending invitations and confirmations, allowing for more detailed messages.
* **Advanced Reporting**: A more detailed analytics page showing trends over time, response rates by contact tag, and other key performance indicators for event hosts.
* **Customizable Message Templates**: Allow hosts to edit the content of the invitation, confirmation, and reminder messages on a per-event basis.