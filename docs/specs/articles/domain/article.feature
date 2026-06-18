Feature: The Article entity
  As the article domain
  I want articles to carry a stable identity, faithful content, and favorite counts
  So that every reading surface presents the same consistent article

  An article is identified by a human-readable slug derived from its title. It
  records the author's title, a short summary, and a full body. When read in
  the context of a viewer, an article also knows how many readers have favorited
  it and whether the current viewer is one of them.

  Rule: An article's slug is derived from its title when first created

    @RID-ARTICLES-SLUG-001
    Scenario: A new article's slug is the slugified title
      When an author creates an article titled "Hello World"
      Then the article's slug is "hello-world"

  Rule: An article's slug is stable once created

    # @unverified-intent: editing the title deliberately does not change the
    # slug, so the article's URL stays stable; documenting the current contract.
    @RID-ARTICLES-SLUG-002
    Scenario: Editing the title leaves the slug unchanged
      Given an article titled "Hello World" with slug "hello-world"
      When its title is changed to "Totally Different Title" and saved
      Then its slug remains "hello-world"

  Rule: An article records a summary and a full body

    @RID-ARTICLES-CONTENT-001
    Scenario: An author's summary and body are stored faithfully
      When an author publishes an article with a summary and a body
      Then the article's summary holds what the author entered as the description
      And the article's body holds what the author entered as the article text

  Rule: Read in a viewer's context, an article knows its favorite standing

    @RID-ARTICLES-FAVORITE-STANDING-001
    Scenario: An anonymous viewer never sees an article as their favorite
      Given an article exists
      When the article is read by an anonymous viewer
      Then the article is not marked as the viewer's favorite

    @RID-ARTICLES-FAVORITE-STANDING-002
    Scenario: A signed-in viewer sees their own favorite reflected
      Given an article that a reader has favorited
      When the article is read in that reader's context
      Then the article is marked as the reader's favorite
      And the article reports a favorite count of 1
