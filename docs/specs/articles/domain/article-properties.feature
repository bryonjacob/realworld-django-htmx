Feature: Article and pagination invariants
  As the article domain
  I want slug identity and pagination to hold under all inputs
  So that URLs never break and paging never errors

  These are universal truths the article and feed machinery must satisfy for
  every input, not illustrative examples.

  Rule: A slug, once assigned, never changes through later edits

    @property-based @RID-ARTICLES-SLUG-003
    Scenario Outline: Any number of edits to any fields leaves the slug fixed
      Given an article whose slug was assigned at creation
      When its title is changed to "<new_title>" and it is saved
      Then its slug is identical to the slug assigned at creation

      Examples:
        | new_title               |
        | Totally Different Title |
        | Hello World             |
        | A                       |
        | Edited Again And Again  |

  Rule: Pagination always resolves to a valid page and never errors

    @property-based @RID-ARTICLES-PAGINATION-003
    Scenario Outline: Any page request resolves to a page of one or more
      Given any collection of articles
      When the feed is requested with a page value of "<requested>"
      Then the feed responds successfully
      And the resolved page number is at least 1

      Examples:
        | requested |
        | bogus     |
        | 0         |
        | -1        |
        | -999      |
        |           |
        | 1         |
        | 3         |

    @property-based @RID-ARTICLES-PAGINATION-004
    Scenario: A page never holds more articles than the page size
      Given any collection of articles
      When any page of the feed is requested
      Then the page holds at most ten articles

    @property-based @RID-ARTICLES-PAGINATION-005
    Scenario: The reported page range always contains at least one page
      Given any collection of articles, including none at all
      When the feed is paginated
      Then the reported range of pages contains at least one page
