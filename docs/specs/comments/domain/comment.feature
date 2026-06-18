Feature: Comment

  As the platform
  I want each comment to be anchored to an article and an author
  So that discussion is attributed correctly and cleaned up with its article

  Rule: A comment belongs to exactly one article and one author

    @RID-COMMENTS-MODEL-001
    Scenario: A comment records its article and author
      Given an article
      And a reader
      When a comment is created on the article by the reader
      Then the comment belongs to that article
      And the comment is attributed to that reader

  Rule: A comment carries content and tracks its timestamps

    @RID-COMMENTS-MODEL-002
    Scenario: A comment records when it was created and last updated
      When a comment is created
      Then it has the content it was given
      And it records when it was created
      And it records when it was last updated

  Rule: Comments are presented newest first

    @RID-COMMENTS-ORDERING-001
    Scenario: Listing the comments on an article
      Given an article with comments created at different times
      When the comments on the article are listed
      Then they appear ordered from newest to oldest

  Rule: Deleting an article deletes its comments

    @RID-COMMENTS-CASCADE-001
    Scenario: Comments are removed when their article is removed
      Given an article with one or more comments
      When the article is deleted
      Then all of its comments are deleted as well

  Rule: Deleting an author deletes their comments

    @RID-COMMENTS-CASCADE-002
    Scenario: Comments are removed when their author is removed
      Given a reader who has written comments
      When the reader's account is deleted
      Then all of that reader's comments are deleted as well
