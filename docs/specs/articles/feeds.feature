Feature: Browsing article feeds
  As a reader
  I want to browse articles through the global feed, my personalised feed, and tag filters
  So that I can discover the writing that matters to me

  The feed is the home surface for articles. A reader can switch between the
  global feed (every article), their personal "following" feed (articles by
  authors they follow), and a tag-filtered view. All three share one feed
  rendering pipeline: the same composition, the same pagination, and the same
  choice between a full page and an in-place fragment refresh.

  Background:
    Given several published articles exist by various authors

  Rule: The global feed shows every article, newest first

    @RID-ARTICLES-FEED-001
    Scenario: An anonymous reader sees all articles in the global feed
      Given an article "Post One" and an article "Post Two" exist
      When an anonymous reader opens the home feed
      Then they see "Post One"
      And they see "Post Two"
      And the active tab is the global feed

    @RID-ARTICLES-FEED-002
    Scenario: Articles are ordered newest first
      When a reader opens the global feed
      Then articles appear in order of most recently created first

  Rule: The following feed shows only articles by authors the reader follows

    @RID-ARTICLES-FEED-FOLLOWING-001
    Scenario: A signed-in reader sees only followed authors' articles
      Given a reader who follows the author of "Post One"
      And the author of "Post Two" is not followed by that reader
      When the reader opens their following feed
      Then they see "Post One"
      And they do not see "Post Two"
      And the active tab is the following feed

    # @unverified-intent: anonymous access to the following feed is handled by a
    # server-side redirect to login rather than hiding the tab; documenting the
    # current contract.
    @RID-ARTICLES-FEED-FOLLOWING-002
    Scenario: An anonymous reader requesting the following feed is sent to sign in
      When an anonymous reader requests the following feed
      Then they are redirected to the sign-in page

  Rule: A tag filter narrows the feed to articles carrying that tag

    @RID-ARTICLES-TAG-001
    Scenario: Filtering the feed by a tag query
      Given "Post One" is tagged "python"
      And "Post Two" is tagged "django"
      When a reader filters the home feed by the tag "python"
      Then they see "Post One"
      And they do not see "Post Two"
      And the active tab is the tag feed

    @RID-ARTICLES-TAG-002
    Scenario: Visiting a tag's own page narrows the feed the same way
      Given "Post Two" is tagged "django"
      When a reader opens the page for the tag "django"
      Then they see "Post Two"
      And they do not see "Post One"

  Rule: The sidebar offers the set of all tags, refreshed on a short cycle

    @RID-ARTICLES-TAG-003
    Scenario: The feed presents the available tags
      Given articles tagged "python" and "django" exist
      When a reader opens the home feed
      Then the available tags are offered alongside the feed

    @RID-ARTICLES-TAG-004
    Scenario: Newly used tags become available after an article is saved
      Given the available tags have been listed and cached
      When an author publishes an article carrying a brand-new tag
      Then the new tag becomes available to readers immediately

  Rule: Feeds are paginated ten articles to a page

    @RID-ARTICLES-PAGINATION-001
    Scenario: The feed shows at most ten articles per page
      Given more than ten articles exist
      When a reader opens the global feed
      Then at most ten articles are shown on the page

    @RID-ARTICLES-PAGINATION-002
    Scenario Outline: A malformed or out-of-bounds page request falls back to the first page
      When a reader opens the feed with a page request of "<requested>"
      Then the feed responds successfully
      And the reader is shown page 1

      Examples:
        | requested |
        | bogus     |
        | 0         |
        | -5        |
        |           |

  Rule: HTMX fragment requests and full page loads share one feed code path

    @RID-ARTICLES-FEED-FRAGMENT-001
    Scenario: A full page load renders the complete feed page
      When a reader opens the home feed as a full page request
      Then the complete feed page is rendered

    @RID-ARTICLES-FEED-FRAGMENT-002
    Scenario: An HTMX request renders only the feed fragment
      When a reader requests the home feed via HTMX
      Then only the feed fragment is rendered
      And the fragment is composed from the same feed as a full page load
