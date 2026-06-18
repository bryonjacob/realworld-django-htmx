Feature: Conduit template context
  As a developer rendering any page in the app
  I want the current user's identity injected into every template context
  So that the client-side debug interface can read who is signed in, with a
     consistent shape whether or not anyone is authenticated.

  The context processor exposes two keys on every template: a JSON string
  describing the user and an authentication flag. For an anonymous visitor the
  JSON is the literal "null"; for an authenticated user it is a JSON object of
  their username, email, bio, and image, where empty bio or image values are
  normalized to null.

  Rule: An anonymous visitor produces a null user and an unauthenticated flag

    @RID-HELPERS-CONTEXT-001
    Scenario: Context for an anonymous visitor
      Given an anonymous visitor
      When the conduit context is built
      Then the user JSON is "null"
      And the authenticated flag is false

  Rule: An authenticated user produces their profile JSON and an authenticated flag

    @RID-HELPERS-CONTEXT-002
    Scenario: Context for an authenticated user with bio and image
      Given an authenticated user with username "alice", a non-empty bio, and an image
      When the conduit context is built
      Then the authenticated flag is true
      And the user JSON includes the username and the bio

    @RID-HELPERS-CONTEXT-003
    Scenario: Empty bio and image are normalized to null in the user JSON
      Given an authenticated user with an empty bio and an empty image
      When the conduit context is built
      Then the user JSON reports the bio as null
      And the user JSON reports the image as null
