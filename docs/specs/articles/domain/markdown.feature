Feature: Rendering article markdown
  As a reader
  I want article bodies written in markdown to render as formatted, safe HTML
  So that articles read well without exposing me to injected markup

  Article bodies are authored in markdown. When displayed, the markdown is
  rendered to HTML and then sanitised so that only safe markup survives.

  Rule: Markdown is rendered to formatted HTML

    @RID-ARTICLES-MARKDOWN-001
    Scenario: Headings and emphasis are rendered
      When an article body containing a markdown heading and bold text is rendered
      Then the result contains a rendered heading
      And the result contains rendered bold text

  Rule: Unsafe markup is stripped during sanitisation

    @RID-ARTICLES-MARKDOWN-002
    Scenario: Embedded scripts are removed
      When an article body containing a script tag followed by text is rendered
      Then the script tag is removed from the result
