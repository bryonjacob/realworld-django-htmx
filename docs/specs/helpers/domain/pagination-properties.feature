Feature: Pagination invariants
  As a developer relying on the paginator across many call sites
  I want the paginator to uphold the same guarantees for every possible input
  So that views and templates can trust its output without defensive checks.

  These are universal properties that hold for any queryset and any ?page=
  value, derived from the slicing and clamping logic in paginate().

  Rule: The reported page is always a positive integer

    @property-based @RID-HELPERS-PAGINATE-PROP-001
    Scenario Outline: Any page input yields a reported page of at least 1
      Given a queryset of <total> records
      When the developer paginates with page "<input>" at <per_page> per page
      Then the reported page is at least 1

      Examples:
        | total | input | per_page |
        | 25    | 2     | 10       |
        | 25    | abc   | 10       |
        | 25    | 0     | 10       |
        | 25    | -5    | 10       |
        | 0     |       | 10       |
        | 5     | 99    | 10       |

  Rule: A page never holds more records than the per-page window

    @property-based @RID-HELPERS-PAGINATE-PROP-002
    Scenario Outline: The returned record count never exceeds per_page
      Given a queryset of <total> records
      When the developer paginates with page "<input>" at <per_page> per page
      Then the page holds at most <per_page> records

      Examples:
        | total | input | per_page |
        | 25    | 1     | 10       |
        | 25    | 3     | 10       |
        | 25    | 99    | 10       |
        | 3     | 1     | 10       |
        | 0     | 1     | 10       |
        | 25    | 1     | 5        |

  Rule: The page range always begins at 1 and spans at least one page

    @property-based @RID-HELPERS-PAGINATE-PROP-003
    Scenario Outline: The page range is 1-based and never empty
      Given a queryset of <total> records
      When the developer paginates with page "<input>" at <per_page> per page
      Then the page range starts at 1
      And the page range spans at least one page
      And the page range covers ceil(total / per_page) pages, but never fewer than one

      Examples:
        | total | input | per_page |
        | 25    | 1     | 10       |
        | 0     | 1     | 10       |
        | 5     | 99    | 10       |
        | 10    | 1     | 10       |
        | 11    | 1     | 10       |
