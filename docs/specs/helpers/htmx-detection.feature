Feature: HTMX request detection
  As a developer choosing between a full page and an HTMX partial
  I want to know whether a request originated from HTMX
  So that the same view can build one context and then render either the full
     page or just the partial fragment.

  Detection is based solely on the HX-Request header carried by HTMX requests;
  the header must equal the string "true" to count as an HTMX request.

  Rule: A request is an HTMX request only when HX-Request equals "true"

    @RID-HELPERS-HTMX-001
    Scenario: The HX-Request header is set to true
      Given a request whose HX-Request header is "true"
      When the developer checks whether the request is from HTMX
      Then the request is recognized as an HTMX request

    @RID-HELPERS-HTMX-002
    Scenario: The HX-Request header is absent
      Given a request with no HX-Request header
      When the developer checks whether the request is from HTMX
      Then the request is not recognized as an HTMX request

    @RID-HELPERS-HTMX-003
    Scenario: The HX-Request header carries any other value
      # @unverified-intent: only the exact string "true" counts; any other
      # value, including "false", is treated as a non-HTMX request.
      Given a request whose HX-Request header is "false"
      When the developer checks whether the request is from HTMX
      Then the request is not recognized as an HTMX request
