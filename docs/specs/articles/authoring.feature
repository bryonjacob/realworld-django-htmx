Feature: Authoring and favoriting articles
  As an author
  I want to create, edit, and delete my own articles, and favorite others' work
  So that I can publish my writing and signal which articles I value

  Authoring is restricted to the article's own author. Favoriting is open to
  any signed-in reader and toggles on each action. Both demand authentication;
  an anonymous visitor is always sent to sign in first.

  Rule: Only a signed-in user may reach the article editor

    @RID-ARTICLES-EDITOR-ACCESS-001
    Scenario: An anonymous visitor is redirected away from the new-article editor
      When an anonymous visitor opens the new-article editor
      Then they are redirected to the sign-in page

    @RID-ARTICLES-EDITOR-ACCESS-002
    Scenario: A signed-in author opens the new-article editor
      Given a signed-in author
      When they open the new-article editor
      Then the article editor is presented

  Rule: Publishing an article records its title, summary, body, tags, and author

    @RID-ARTICLES-CREATE-001
    Scenario: An author publishes an article with tags
      Given a signed-in author
      When they publish an article titled "New Title" with a summary, a body, and the tags "python,  django  , "
      Then the article is created with that author
      And its summary and body are recorded as entered
      And it carries the tags "django" and "python"

    @RID-ARTICLES-CREATE-002
    Scenario: Tag entries are trimmed and blank entries discarded
      Given a signed-in author
      When they publish an article with the tags "python,  django  , "
      Then the article carries exactly the tags "django" and "python"

    @RID-ARTICLES-CREATE-003
    Scenario: An author publishes an article with no tags
      Given a signed-in author
      When they publish an article with an empty tag list
      Then the article is created with no tags

    @RID-ARTICLES-CREATE-004
    Scenario: After publishing, the author lands on the new article
      Given a signed-in author
      When they publish a valid article
      Then they are taken to that article's detail page

    @RID-ARTICLES-CREATE-005
    Scenario: An article cannot be published without a title
      Given a signed-in author
      When they submit the editor with an empty title
      Then the editor is shown again for correction

  Rule: Only the author may edit their own article

    @RID-ARTICLES-EDIT-001
    Scenario: A reader who is not the author cannot edit the article
      Given an article authored by someone else
      And a different signed-in reader
      When the reader tries to open the edit editor for that article
      Then the article is reported as not found

    @RID-ARTICLES-EDIT-002
    Scenario: The author's editor is pre-filled with the current article
      Given a signed-in author with an article titled "Edit Me" tagged "python"
      When they open the edit editor for that article
      Then the editor is pre-filled with "Edit Me"
      And the editor is pre-filled with the tag "python"

    @RID-ARTICLES-EDIT-003
    Scenario: An author edits the summary, body, and tags of their article
      Given a signed-in author with an existing article
      When they save the editor with a new summary, a new body, and the tags "rust"
      Then the article's summary and body are updated
      And the article carries exactly the tag "rust"
      And they are taken to that article's detail page

    @RID-ARTICLES-EDIT-004
    Scenario: A saved edit cannot leave the title empty
      Given a signed-in author with an existing article
      When they save the editor with an empty title
      Then the editor is shown again for correction

  Rule: Only the author may delete their own article

    @RID-ARTICLES-DELETE-001
    Scenario: A reader who is not the author cannot delete the article
      Given an article authored by someone else
      And a different signed-in reader
      When the reader tries to delete that article
      Then the article is reported as not found

    @RID-ARTICLES-DELETE-002
    Scenario: An author deletes their own article
      Given a signed-in author with an article
      When they delete that article
      Then the article no longer exists
      And they are returned to the home feed

  Rule: Favoriting requires sign-in and toggles on each action

    @RID-ARTICLES-FAVORITE-001
    Scenario: An anonymous visitor cannot favorite an article
      When an anonymous visitor tries to favorite an article
      Then they are redirected to the sign-in page

    @RID-ARTICLES-FAVORITE-002
    Scenario: Favoriting then favoriting again removes the favorite
      Given a signed-in reader and an article they have not favorited
      When the reader favorites the article
      Then the article counts the reader among its favorites
      When the reader favorites the article again
      Then the article no longer counts the reader among its favorites

    @RID-ARTICLES-FAVORITE-003
    Scenario: After a non-HTMX favorite the reader returns to the article
      Given a signed-in reader and an article
      When the reader favorites the article through a full request
      Then they are returned to that article's detail page

    @RID-ARTICLES-FAVORITE-004
    Scenario: An HTMX favorite returns only the favorite control
      Given a signed-in reader and an article
      When the reader favorites the article via HTMX
      Then only the favorite control fragment is returned

    @RID-ARTICLES-FAVORITE-005
    Scenario: Favoriting a non-existent article is reported as not found
      Given a signed-in reader
      When the reader tries to favorite an article that does not exist
      Then the article is reported as not found

  Rule: A profile page lists a user's own articles or their favorites by tab

    @RID-ARTICLES-PROFILE-001
    Scenario: The profile's article tab lists articles written by that user
      Given a user who has written several articles
      When a reader opens that user's profile on the articles tab
      Then the user's own articles are listed newest first

    @RID-ARTICLES-PROFILE-002
    Scenario: The profile's favorites tab lists articles that user has favorited
      Given a user who has favorited several articles
      When a reader opens that user's profile on the favorites tab
      Then the articles that user has favorited are listed newest first

    @RID-ARTICLES-PROFILE-003
    Scenario: A profile for an unknown user is reported as not found
      When a reader opens a profile for a username that does not exist
      Then the profile is reported as not found
