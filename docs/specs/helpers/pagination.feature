Feature: Queryset pagination
  As a developer rendering a list of records across pages
  I want a forgiving paginator driven by the ?page= query parameter
  So that any page request — including hostile or malformed input — yields a
     renderable page instead of an error.

  The helper deliberately does NOT use Django's built-in Paginator, which raises
  on invalid input. Instead it parses ?page=, defaults unparseable or
  non-positive values to page 1, slices the queryset directly, and always
  reports at least one page so templates can render a page strip even when the
  queryset is empty. The slice window defaults to 10 records per page.

  Rule: The requested page is read from the ?page= query parameter

    @RID-HELPERS-PAGINATE-001
    Scenario: A valid page number is used as the page to slice
      Given a queryset of 25 records ordered by title
      When the developer paginates with page "2"
      Then the reported page is 2
      And the page contains records 11 through 20

    @RID-HELPERS-PAGINATE-002
    Scenario: A missing page parameter defaults to page 1
      Given a queryset of 25 records ordered by title
      When the developer paginates with no page parameter
      Then the reported page is 1
      And the page contains the first 10 records

  Rule: Invalid or non-positive page input never raises and resolves to page 1

    @RID-HELPERS-PAGINATE-003
    Scenario: A non-numeric page value defaults to page 1
      Given a queryset of 25 records ordered by title
      When the developer paginates with page "abc"
      Then the reported page is 1
      And the page contains the first 10 records

    @RID-HELPERS-PAGINATE-004
    Scenario: A page of zero is clamped up to page 1
      Given a queryset of 25 records ordered by title
      When the developer paginates with page "0"
      Then the reported page is 1
      And the page contains the first 10 records

    @RID-HELPERS-PAGINATE-005
    Scenario Outline: Invalid and non-positive inputs collapse to page 1
      Given a queryset of 25 records ordered by title
      When the developer paginates with page "<input>"
      Then the reported page is 1

      Examples:
        | input |
        | abc   |
        | 0     |
        | -5    |
        |       |

  Rule: A page slice holds at most one window of records

    @RID-HELPERS-PAGINATE-006
    Scenario: A full page holds exactly the per-page count
      Given a queryset of 25 records ordered by title
      When the developer paginates with page "1"
      Then the page contains 10 records

    @RID-HELPERS-PAGINATE-007
    Scenario: A page beyond the available records is empty but still reported
      # @unverified-intent: requesting a page past the end echoes the requested
      # page number rather than clamping to the last valid page.
      Given a queryset of 5 records ordered by title
      When the developer paginates with page "99"
      Then the page contains no records
      And the reported page is 99
      And the page range spans 1 through 1

  Rule: The page range always covers at least one page

    @RID-HELPERS-PAGINATE-008
    Scenario: A populated queryset reports a range covering every page
      Given a queryset of 25 records ordered by title
      When the developer paginates with no page parameter
      Then the page range spans 1 through 3

    @RID-HELPERS-PAGINATE-009
    Scenario: An empty queryset still reports a single page
      Given an empty queryset
      When the developer paginates with no page parameter
      Then the page contains no records
      And the reported page is 1
      And the page range spans 1 through 1
