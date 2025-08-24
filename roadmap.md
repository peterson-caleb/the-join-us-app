### ## Feature Upgrade Plan: Management, Experience & Analytics

This plan outlines a series of significant upgrades to the application. It is guided by a core strategic decision to simplify the group management model for the initial product, focusing on a robust experience for individual organizers while paving the way for future enhancements.

* * * * *

### ### Foundational Decision: Simplify to a "Single-Owner Group" Model

Before detailing the features, the entire plan will be based on a core architectural simplification:

-   Single Owner per Group: Each group will have exactly one owner. Only this owner can create and manage events and contacts within that group.

-   Collaboration Deferred: The concept of inviting multiple members to collaborate within a single group is deferred for a future version. This drastically simplifies permissions and workflows.

-   MVP Focus: This decision focuses development on perfecting the most critical use case: an individual organizer managing their own events.

* * * * *

### ## Part 1: Enhanced Group Management & Admin Experience

This section details foundational changes to the contact management system, adds full editing and onboarding capabilities for groups, and refines the administrator's workflow.

#### 1\. Implement User-Owned, Sharable Contacts (Contact Portability)

This is a foundational refactor to move from group-owned contacts to a more flexible user-owned model, creating a single source of truth for each contact and enhancing data privacy.

-   Terminology Update: As part of this refactor, all instances of "master contact list" or "master_list" will be removed due to negative connotations. The user interface will be updated to use "My Contacts." The underlying database collection will be renamed to contacts, and all related variable names in the codebase will be updated accordingly.

-   Implementation Phases: This will be a multi-phase process involving database schema changes, a one-time data migration script, and a full refactor of the service, API, and frontend layers that handle contacts.

#### 2\. Streamline User & Contact Onboarding

This feature replaces cumbersome invitation codes and manual contact entry with two new, streamlined, link-based workflows.

-   A. New User Registration Links (Admin Task)

-   Goal: Replace the awkward, manual invitation codes 1111 with a secure, user-friendly link system for registering new users on the platform.

-   Implementation: Admins will generate unique, single-use registration links from the admin panel. When a prospective user clicks this link, they are taken directly to a registration page where the invitation code field is no longer needed. A "Copy Link" button will be placed next to each generated registration link for ease of use.

-   B. Personal Contact Collection Links (Organizer Task)

-   Goal: Replace the laborious manual entry of contacts with a simple, shareable link that allows people to add themselves to an organizer's "My Contacts" list.

-   Implementation: Each registered user will be provided with a single, persistent "Contact Collection Link." When a person signs up through the link, a new Contact record is created and assigned to the organizer who shared the link. A "Copy Link" button will be added next to the user's link to facilitate easy sharing.

#### 3\. Implement Full Group Editing Capabilities

-   Goal: Allow group owners and administrators to edit a group's details after its creation.

-   Editable Fields: Group Name and SMS Quotas (for admins). The ability to transfer ownership is no longer needed with the single-owner model.

-   Implementation: New service methods and protected routes will be created to handle updates. The UI will be modified on the "Manage Groups" and "Admin System Panel" pages to include "Edit" buttons that open a form or modal for authorized users.

#### 4\. Add Group Deletion Functionality

-   Goal: Allow a group owner or an administrator to permanently delete a group and its associated data.

-   Implementation: A delete_group method will be added to the service layer, which will also handle the cascading deletion of all events associated with that group. The UI will feature a "Delete" option protected by a confirmation modal that requires the user to type the group's name to proceed.

#### 5\. Implement Admin "Contextual View Mode"

-   Goal: Allow administrators to access and manage any group's pages without needing to "join" it.

-   Implementation: This will be a session-based feature. New admin routes will be created to initiate and exit a "view mode" by setting a variable in the user's session. The application's core logic will be updated to check for this session variable and set the active group context accordingly for admins. The UI will feature a persistent banner indicating when view mode is active and providing a simple exit button.

#### 6\. Implement Editable Platform-Wide Settings

-   Goal: To move critical platform-wide settings, like global SMS limits, from static environment variables into the database, allowing administrators to manage them directly through the application UI.

-   Implementation: A new system_settings collection will be created in MongoDB. A new service and admin page will be created for administrators to edit these values. The SMSService will be modified to query these settings from the database at runtime. This will also include a new Max Invitees per Event setting.

* * * * *

### ## Part 2: Improved Event & Guest RSVP Experience

This section focuses on adding more context and useful information for both event organizers and guests, making the platform more interactive and informative.

#### 7\. Implement Event Archiving (Soft Deletes)

-   Goal: Preserve historical event data for accurate analytics by replacing permanent deletion with an archiving system.

-   Implementation: The "Delete" action for an event will be changed to an "Archive" action. This will set an is_archived flag on the Event model rather than removing the document from the database. The main events list will be updated to hide archived events by default, while all analytics and reporting queries will continue to include them.

#### 8\. "Plus One" / Guest Count Support

-   Goal: Enhance the RSVP experience by allowing a single invitee to RSVP for more than one person.

-   Implementation: The Event model will be updated to allow organizers to specify if an invitee can bring guests. The capacity calculation logic will be modified to sum the total number of attending guests, not just confirmed RSVPs. The public RSVP page will be updated to conditionally show an input for the guest to specify their party size.

#### 9\. Add "Add to Calendar" Button

-   Goal: Improve the post-RSVP experience by providing guests with a simple, one-click method to add the event to their personal calendar.

-   Implementation: A new backend route will be created to dynamically generate a standard .ics calendar file using the event's details. The RSVP confirmation view (after a guest RSVPs 'YES') will be updated to include a button that links to this new route.

#### 10\. Add Organizer Participation Toggle

-   Goal: Provide a simple way for an event organizer to include themselves in the event's capacity count.

-   Implementation: A new boolean field, organizer_is_attending, will be added to the Event model. The service logic that calculates available spots will be updated to account for this flag. The event creation and editing forms will be updated with a new checkbox to control this setting 2.

#### 11\. Add Public Attendee List Option

-   Goal: Allow organizers to optionally display a list of confirmed attendees on the public RSVP page.

-   Implementation: A new boolean field, show_attendee_list, will be added to the Event model. If this option is enabled for an event, the RSVP page route will fetch the names of all confirmed guests and pass them to the template for display.

#### 12\. Display Event Capacity on RSVP Page

-   Goal: After a guest RSVPs "YES," dynamically show them a progress bar indicating how full the event is.

-   Implementation: The API that processes an RSVP will be updated to return the event's current confirmed count and total capacity in its JSON response. The RSVP page's JavaScript will then use this data to dynamically render a progress bar 3.

#### 13\. Redesign Event Capacity Progress Bar

-   Goal: To replace the current, basic progress bar with a modern, visually appealing, and more informative component on both the events list and RSVP pages.

-   Implementation: The new component will be a pill-shaped, stacked bar with smooth, animated gradient fills. An interactive popover will be triggered on hover, displaying a detailed breakdown of confirmed, invited, and remaining spots.

* * * * *

### ## Part 3: Data & Engagement Analytics

This section introduces new reporting features to give users powerful insights into their contact list's engagement over time and the performance of their events.

#### 14\. Add "Non-Response" Metric to Group Dashboard

-   Goal: Provide organizers with clear insight into how many invited guests did not respond to an invitation.

-   Implementation: A new stat card for "No Response / Expired" will be added to the group dashboard. The DashboardService will be updated with a new query to count invitees with an EXPIRED status. This new card will also be clickable, leading to a detailed modal view listing the specific contacts who did not respond.

#### 15\. Implement Individual Contact Statistics

-   Goal: Provide contact owners with a detailed history of a single contact's engagement.

-   UI/UX: A "View Engagement Stats" option will be added to the actions dropdown menu on the "My Contacts" page, opening a modal displaying a contact's historical invitation and response data.

-   Backend: A new, secure API endpoint will be created to fetch stats for a single contact on demand using an efficient database aggregation query.

#### 16\. Create a Contact Engagement Report Page

-   Goal: Offer a comparative, high-level overview of engagement across all of a user's contacts.

-   UI/UX: A new "Engagement Report" page will be created, featuring a sortable table with columns like Contact Name, Total Invitations, response breakdowns, and Confirmation Rate (%).

-   Backend: A new route will power this page, triggering a single, comprehensive aggregation query to gather and process stats for all of a user's contacts at once.

* * * * *

### ### Ideas That Need Vetting

The following are ideas from the original product roadmap 4 that require further discussion and prioritization. They are not part of the immediate development plan but are captured here for future consideration.

-   Explicit Waitlist Management

-   Guest List Export (CSV/PDF)

-   Traditional Invite Method (Invite all at once)

-   "Maybe" RSVP Option

-   Recurring Events

-   Email as an Invitation Channel

-   Advanced Platform-Wide Reporting

-   Customizable Message Templates

-   Clickable Global Dashboard Stats

-   Admin Management UI for Users & Groups

* * * * *

### ### Deferred Features for Post-MVP

-   User Account Deletion: A user-facing feature to delete one's own account and all associated data will be deferred.

-   Multi-User Group Collaboration: The ability to invite other members to a group to co-manage events is deferred.

-   Verification Flow for Manually Added Contacts: A system where manually added contacts must verify their information and consent via an SMS link before they can be invited to events.