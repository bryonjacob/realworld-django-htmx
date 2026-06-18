Feature: Authentication
  As a visitor to the application
  I want to register, sign in, manage my settings, and sign out
  So that I can establish and control my identity within the community

  Background:
    Given the application supports a custom user identity where the email address is the credential used to sign in and the username is a separate display handle

  Rule: A user signs in with their email address and password

    @RID-ACCOUNTS-LOGIN-001
    Scenario: Sign-in succeeds with valid credentials
      Given a registered user with a known email and password
      When the user signs in with that email and password
      Then the user becomes authenticated
      And the user is taken to the home page

    @RID-ACCOUNTS-LOGIN-002
    Scenario: The username is not a sign-in credential
      Given a registered user whose display handle differs from their email
      When the user attempts to sign in using their display handle as the credential
      Then sign-in does not succeed

    @RID-ACCOUNTS-LOGIN-003
    Scenario: Sign-in is rejected when the password is wrong
      Given a registered user with a known email and password
      When the user signs in with that email but an incorrect password
      Then sign-in fails with the message "Invalid email or password."
      And the sign-in page is shown again so the user can retry
      And the user remains unauthenticated

    @RID-ACCOUNTS-LOGIN-004
    Scenario: Sign-in is rejected when the email is unknown
      Given no user is registered with a particular email
      When someone attempts to sign in with that email and any password
      Then sign-in fails with the message "Invalid email or password."
      And the sign-in page is shown again

    @RID-ACCOUNTS-LOGIN-005
    Scenario: A malformed sign-in submission re-displays the form
      When someone submits a sign-in attempt with an email that is not a valid email address
      Then the sign-in page is re-displayed for correction
      And the system does not error out

  Rule: Registration creates an account, signs the new user in, and is all-or-nothing

    @RID-ACCOUNTS-REGISTER-001
    Scenario: Registration succeeds and signs the new user in
      Given no user exists with a chosen email or username
      When a visitor registers with that email, username, and a password
      Then a new user account is created
      And the new user becomes authenticated immediately
      And the new user is taken to the home page

    @RID-ACCOUNTS-REGISTER-002
    Scenario: A malformed registration submission re-displays the form
      When a visitor submits a registration with an invalid email, a blank username, and a blank password
      Then the registration page is re-displayed for correction
      And no account is created

  Rule: Each uniqueness conflict during registration reports the specific field at fault

    @RID-ACCOUNTS-REGISTER-CONFLICT-001
    Scenario: Registering with an already-taken email reports the email
      Given a user is already registered with a given email
      When a visitor registers with that same email but a different username
      Then registration fails with the message "This email has already been taken."
      And the failure is attributed to the email field

    @RID-ACCOUNTS-REGISTER-CONFLICT-002
    Scenario: Registering with an already-taken username reports the username
      Given a user is already registered with a given username
      When a visitor registers with that same username but a different email
      Then registration fails with the message "This username has already been taken."
      And the failure is attributed to the username field

    # @unverified-intent: any uniqueness conflict the system cannot attribute to a
    # specific field collapses to a generic message; stakeholders may want to confirm
    # whether a silent catch-all is the intended behavior for unforeseen conflicts.
    @RID-ACCOUNTS-REGISTER-CONFLICT-003
    Scenario: An unattributable uniqueness conflict reports a generic failure
      When a visitor registers and the account creation hits a uniqueness conflict that cannot be attributed to either the email or the username
      Then registration fails with the generic message "Registration failed."

  Rule: Updating settings requires being signed in and preserves the active session

    @RID-ACCOUNTS-SETTINGS-001
    Scenario: An anonymous visitor cannot reach settings
      Given the visitor is not signed in
      When the visitor tries to open the settings page
      Then the visitor is redirected to the sign-in page

    @RID-ACCOUNTS-SETTINGS-002
    Scenario: A signed-in user can view their settings
      Given a signed-in user
      When the user opens the settings page
      Then the user's current settings are displayed for editing

    @RID-ACCOUNTS-SETTINGS-003
    Scenario: Updating profile fields without changing the password keeps the password
      Given a signed-in user with an existing password
      When the user updates their bio and saves settings without supplying a new password
      Then the updated profile is saved
      And the user's existing password still works
      And the user is taken to their profile page

    @RID-ACCOUNTS-SETTINGS-004
    Scenario: Changing the password keeps the user signed in
      Given a signed-in user
      When the user saves settings with a new password
      Then the new password takes effect
      And the user remains signed in rather than being logged out by the password change
      And the user is taken to their profile page

    @RID-ACCOUNTS-SETTINGS-005
    Scenario: A malformed settings submission re-displays the form
      Given a signed-in user
      When the user saves settings with an invalid email and a blank username
      Then the settings page is re-displayed for correction

  Rule: Signing out is only performed through an explicit submission

    @RID-ACCOUNTS-LOGOUT-001
    Scenario: Signing out ends the session
      Given a signed-in user
      When the user submits a sign-out request
      Then the user becomes unauthenticated
      And the user is taken to the home page

    @RID-ACCOUNTS-LOGOUT-002
    Scenario: A sign-out cannot be triggered by mere navigation
      When a sign-out is requested by simple navigation rather than an explicit submission
      Then the request is not allowed
