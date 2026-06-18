Feature: Profiles and following
  As a member of the community
  I want to view other users' profiles and follow or unfollow them
  So that I can curate whose articles I care about

  Background:
    Given users have public profiles identified by their username
    And a profile shows the articles the user has authored or favorited

  Rule: A profile is addressed by username and only exists for a real user

    @RID-ACCOUNTS-PROFILE-001
    Scenario: Viewing an existing user's profile shows their authored articles
      Given a user who has authored an article
      When anyone views that user's profile
      Then the profile is shown
      And the user's authored articles appear on it

    @RID-ACCOUNTS-PROFILE-002
    Scenario: A profile's favorites view shows the articles that user has favorited
      Given a user who has favorited an article
      When anyone views the favorites tab of that user's profile
      Then the favorited articles appear

    @RID-ACCOUNTS-PROFILE-003
    Scenario: Viewing a profile for an unknown username is not found
      Given no user is registered with a given username
      When anyone tries to view a profile for that username
      Then the profile is reported as not found

  Rule: A profile view reflects the viewer's relationship to it

    @RID-ACCOUNTS-PROFILE-VIEWER-001
    Scenario: A user viewing their own profile is recognised as themselves
      Given a signed-in user
      When the user views their own profile
      Then the profile is marked as the viewer's own
      And the profile does not indicate that the viewer follows themselves

    @RID-ACCOUNTS-PROFILE-VIEWER-002
    Scenario: A profile indicates whether the viewer already follows it
      Given a signed-in user who follows another user
      When the follower views that other user's profile
      Then the profile indicates that the viewer is already following

  Rule: Following requires being signed in and is performed by explicit submission

    @RID-ACCOUNTS-FOLLOW-001
    Scenario: An anonymous visitor cannot follow
      Given the visitor is not signed in
      When the visitor submits a request to follow a user
      Then the visitor is redirected to the sign-in page

    @RID-ACCOUNTS-FOLLOW-002
    Scenario: Following a non-existent user is not found
      Given a signed-in user
      When the user submits a request to follow a username that does not exist
      Then the request is reported as not found

  Rule: Following toggles between following and not following the target user

    @RID-ACCOUNTS-FOLLOW-003
    Scenario: Following then following again unfollows
      Given a signed-in user who does not yet follow a target user
      When the user submits a follow request for that target
      Then the user is now following the target
      When the user submits a follow request for that same target again
      Then the user is no longer following the target

  Rule: The follow action responds in place for live interactions and otherwise redirects

    @RID-ACCOUNTS-FOLLOW-RESPONSE-001
    Scenario: A live follow toggle updates the follow control in place
      Given a signed-in user performing the follow action as a live page interaction
      When the user toggles following on a target user
      Then the follow control is returned for in-place update without a full page navigation

    @RID-ACCOUNTS-FOLLOW-RESPONSE-002
    Scenario: A plain follow submission redirects back to the profile
      Given a signed-in user performing the follow action as a plain submission
      When the user toggles following on a target user
      Then the user is redirected back to that user's profile
