Feature: User identity and following relationships
  As the steward of the user model
  I want the identity and following rules to hold as invariants
  So that authentication and the social graph behave consistently everywhere

  Background:
    Given a user has an email address, a username display handle, an optional bio, and an optional profile image

  Rule: The email address is the identity credential and the username is a display handle

    @RID-ACCOUNTS-USER-IDENTITY-001
    Scenario: The email is the field used to identify a user for authentication
      Given a user account
      Then the user is identified for authentication by their email address
      And the username serves as a separate display and URL handle

    @RID-ACCOUNTS-USER-IDENTITY-002
    Scenario: A user's display names resolve to the username
      Given a user with a username
      Then both the user's full name and short name resolve to that username

  Rule: A user created without a password cannot authenticate with a password

    @RID-ACCOUNTS-USER-PASSWORD-001
    Scenario: Creating a user with a password yields a usable password
      When a user is created with a password
      Then that password can be verified for the user
      And the user has a usable password

    @RID-ACCOUNTS-USER-PASSWORD-002
    Scenario: Creating a user without a password yields an unusable password
      When a user is created without a password
      Then the user has an unusable password
      And no password can be used to authenticate that user until one is set

  Rule: Superusers must have the administrative flags set

    @RID-ACCOUNTS-SUPERUSER-001
    Scenario: Creating a superuser sets the administrative flags
      When a superuser is created
      Then the account is a staff member
      And the account is a superuser
      And the account is active

    @RID-ACCOUNTS-SUPERUSER-002
    Scenario Outline: Creating a superuser without a required flag is rejected
      When a superuser is created with <flag> turned off
      Then the creation is rejected

      Examples:
        | flag         |
        | staff status |
        | superuser status |

  Rule: Following is a directional relationship between users

    @RID-ACCOUNTS-FOLLOW-GRAPH-001
    Scenario: A user is not following another by default
      Given two distinct users
      Then neither user is following the other

    @RID-ACCOUNTS-FOLLOW-GRAPH-002
    Scenario: Adding a follower makes the relationship hold in one direction only
      Given two distinct users
      When the first user begins following the second
      Then the first user is following the second
      And the second user is not thereby following the first

  Rule: Following oneself is never recorded

    # @unverified-intent: a self-follow submission is silently accepted as a no-op rather
    # than rejected with an error; stakeholders may want to confirm whether silently
    # ignoring it is preferable to surfacing an explicit "cannot follow yourself" response.
    @RID-ACCOUNTS-FOLLOW-GRAPH-003
    Scenario: A user cannot follow themselves
      Given a signed-in user
      When the user submits a request to follow themselves
      Then the user is not recorded as following themselves
      And the request completes without error
