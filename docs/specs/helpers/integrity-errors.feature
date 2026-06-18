Feature: Integrity error classification
  As a developer turning a database constraint violation into a form error
  I want a database IntegrityError reduced to the name of the offending field
  So that I can attach a friendly message to the right form field, or fall back
     gracefully when the violation cannot be identified.

  The classifier inspects the IntegrityError's underlying cause (its __cause__)
  and parses the driver-specific message — SQLite or psycopg2 — to extract the
  unique-constraint field name. Anything it cannot confidently parse resolves to
  no field rather than raising.

  Rule: A SQLite unique-constraint violation yields the offending field name

    @RID-HELPERS-INTEGRITY-001
    Scenario Outline: The field name is extracted from the SQLite message
      Given an integrity error caused by a SQLite unique violation on "accounts_user.<field>"
      When the developer classifies the integrity error
      Then the classified field is "<field>"

      Examples:
        | field    |
        | email    |
        | username |

  Rule: A psycopg2 unique-constraint violation yields the offending field name

    @RID-HELPERS-INTEGRITY-002
    Scenario: The field name is extracted from the psycopg2 message
      Given an integrity error caused by a psycopg2 unique violation naming key "email"
      When the developer classifies the integrity error
      Then the classified field is "email"

  Rule: An unidentifiable violation resolves to no field

    @RID-HELPERS-INTEGRITY-003
    Scenario: An integrity error with no underlying cause yields no field
      Given an integrity error with no underlying cause
      When the developer classifies the integrity error
      Then no field is classified

    @RID-HELPERS-INTEGRITY-004
    Scenario: An underlying cause of an unrecognized type yields no field
      Given an integrity error caused by an unrelated error type
      When the developer classifies the integrity error
      Then no field is classified

    @RID-HELPERS-INTEGRITY-005
    Scenario: A malformed SQLite message yields no field
      Given an integrity error caused by a SQLite violation with an unparseable message
      When the developer classifies the integrity error
      Then no field is classified

    @RID-HELPERS-INTEGRITY-006
    Scenario: A malformed psycopg2 message yields no field
      Given an integrity error caused by a psycopg2 violation with an unparseable message
      When the developer classifies the integrity error
      Then no field is classified
