Feature: Article comments

  As a registered reader
  I want to leave and remove comments on articles
  So that I can discuss articles with the community and tidy up my own contributions

  Rule: Anyone can read the comments on an article

    @RID-COMMENTS-VIEW-001
    Scenario: Viewing the comments under an article
      Given an article with several comments
      When a reader opens the article
      Then they see every comment on that article
      And the comments are ordered newest first

    @RID-COMMENTS-VIEW-002
    Scenario: Viewing an article that has no comments yet
      Given an article with no comments
      When a reader opens the article
      Then they see no comments

  Rule: Adding a comment requires authentication

    @RID-COMMENTS-AUTHZ-001
    Scenario: An anonymous visitor tries to comment
      Given an article
      And the visitor is not signed in
      When the visitor tries to add a comment
      Then the comment is not added
      And the visitor is sent to sign in

    @RID-COMMENTS-ADD-001
    Scenario: A signed-in reader adds a comment
      Given an article
      And a signed-in reader
      When the reader adds a comment with content "great post"
      Then the comment is recorded on that article
      And the comment is attributed to the reader
      And the comment carries the content "great post"

  Rule: A comment must have non-empty content

    @RID-COMMENTS-CONTENT-001
    Scenario: Submitting blank content
      Given an article
      And a signed-in reader
      When the reader submits a comment whose content is only whitespace
      Then no comment is added

    # @unverified-intent: a blank submission is silently treated as a successful no-op (reader is returned to the article rather than shown an error) — characterizes current behavior, intent of the silent success is unconfirmed
    @RID-COMMENTS-CONTENT-002
    Scenario: A blank submission is accepted silently
      Given an article
      And a signed-in reader
      When the reader submits a comment whose content is only whitespace
      Then no comment is added
      And the reader is returned to the article

  Rule: Comment content is trimmed of surrounding whitespace

    @RID-COMMENTS-CONTENT-003
    Scenario: Surrounding whitespace is stripped before recording
      Given an article
      And a signed-in reader
      When the reader adds a comment with content surrounded by whitespace
      Then the recorded comment content has no leading or trailing whitespace

  Rule: A comment can only be deleted by its author or the article's author

    @RID-COMMENTS-DELETE-001
    Scenario: The comment's author deletes their own comment
      Given an article authored by Alice
      And a comment on that article authored by Bob
      And Bob is signed in
      When Bob deletes his comment
      Then the comment is removed

    @RID-COMMENTS-DELETE-002
    Scenario: The article's author deletes someone else's comment
      Given an article authored by Alice
      And a comment on that article authored by Bob
      And Alice is signed in
      When Alice deletes Bob's comment
      Then the comment is removed

    @RID-COMMENTS-AUTHZ-002
    Scenario: An unrelated reader is forbidden from deleting a comment
      Given an article authored by Alice
      And a comment on that article authored by Bob
      And Carol, who is neither author, is signed in
      When Carol tries to delete the comment
      Then the deletion is forbidden
      And the comment remains

    @RID-COMMENTS-AUTHZ-003
    Scenario: An anonymous visitor tries to delete a comment
      Given an article with a comment
      And the visitor is not signed in
      When the visitor tries to delete the comment
      Then the comment remains
      And the visitor is sent to sign in

  Rule: Comment actions are scoped to the named article

    @RID-COMMENTS-SCOPING-001
    Scenario: Commenting on an article that does not exist
      Given a signed-in reader
      When the reader tries to comment on an article that does not exist
      Then the request is reported as not found

    @RID-COMMENTS-SCOPING-002
    Scenario: Deleting against an article that does not exist
      Given a signed-in reader
      And an existing comment
      When the reader tries to delete the comment under an article that does not exist
      Then the request is reported as not found

    @RID-COMMENTS-SCOPING-003
    Scenario: A comment id that belongs to another article does not resolve
      Given a signed-in reader
      When the reader references a comment id that is not on the named article
      Then the request is reported as not found

  Rule: Comment changes are reflected immediately within the page when made inline

    @RID-COMMENTS-INLINE-001
    Scenario: Adding a comment inline returns the refreshed comment list
      Given an article
      And a signed-in reader
      When the reader adds a comment inline on the article page
      Then the refreshed list of comments is returned for the page
      And the new comment appears in it

    @RID-COMMENTS-INLINE-002
    Scenario: Deleting a comment inline returns the refreshed comment list
      Given an article with a comment authored by the signed-in reader
      When the reader deletes the comment inline on the article page
      Then the refreshed list of comments is returned for the page

    @RID-COMMENTS-INLINE-003
    Scenario: Adding a comment via a full page submission returns to the article
      Given an article
      And a signed-in reader
      When the reader adds a comment via a full page submission
      Then they are returned to the article

    @RID-COMMENTS-INLINE-004
    Scenario: Deleting a comment via a full page submission returns to the article
      Given an article with a comment authored by the signed-in reader
      When the reader deletes the comment via a full page submission
      Then they are returned to the article
