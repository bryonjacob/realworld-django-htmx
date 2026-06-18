Feature: User identity and following properties
  As the steward of the user model
  I want certain truths to hold for all users and all inputs
  So that the identity and social-graph invariants cannot be violated by any case

  Rule: The is-following relationship is well defined for every viewer

    @property-based @RID-ACCOUNTS-FOLLOW-GRAPH-004
    Scenario: An unauthenticated viewer never follows anyone
      Given any viewer that is not authenticated
      And any target user
      Then the viewer is reported as not following the target

    @property-based @RID-ACCOUNTS-FOLLOW-GRAPH-005
    Scenario: A user is following a target exactly when they are among the target's followers
      Given any pair of users
      Then a user is reported as following a target if and only if that user is present in the target's set of followers

  Rule: Identity credentials are unambiguous for every user

    @property-based @RID-ACCOUNTS-USER-IDENTITY-003
    Scenario: Every user is always identified by email, never by username, for authentication
      Given any user account
      Then authentication always resolves the account by its email address
      And never by its username

  Rule: Self-following is impossible for any user

    @property-based @RID-ACCOUNTS-FOLLOW-GRAPH-006
    Scenario: No user ever appears in their own set of followers via the follow action
      Given any user
      When that user repeatedly submits follow requests targeting themselves
      Then the user never appears in their own set of followers
