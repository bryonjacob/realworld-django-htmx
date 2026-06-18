"""pytest-bdd-property wiring for the @property-based spec scenarios.

This conftest registers the plugin hooks and the catch-all pytest-bdd steps that
pytest-bdd-property uses to intercept ``Given any ...`` / ``When <...>`` /
``Then <...>`` lines. Concrete strategies and When/Then property callbacks live
in the per-feature test modules alongside their ``scenarios(...)`` call.
"""

import pytest
import pytest_bdd_property.plugin  # noqa: F401  (registers pytest hooks)
from pytest_bdd import given, parsers, then, when
from pytest_bdd_property.plugin import (
    handle_given_step,
    handle_then_step,
    handle_when_step,
)


@pytest.fixture(autouse=True)
def _enable_db_for_property_specs(request, django_db_setup, django_db_blocker):
    """Some property scenarios (slug stability) hit the ORM. Hypothesis drives
    many examples inside one generated test, so we unblock DB access for the
    whole property package rather than rely on a per-test django_db mark (which
    pytest-bdd's generated scenario functions don't carry). Depending on
    django_db_setup ensures the test database (schema) actually exists before
    we unblock access."""
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)


# Catch-all steps. pytest-bdd-property's handlers match the step text against
# the property_given/when/then patterns registered in the per-feature modules.
# Our scenarios phrase When/Then as prose (not just <var> placeholders), so the
# catch-alls must match ANY step text and defer the real matching to the plugin.
@given(parsers.re(r"(?P<text>.+)"))
def property_given_step(text):
    handle_given_step(text)


@when(parsers.re(r"(?P<text>.+)"))
def property_when_step(text):
    handle_when_step(text)


@then(parsers.re(r"(?P<text>.+)"))
def property_then_step(text):
    handle_then_step(text)
