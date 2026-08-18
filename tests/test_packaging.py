"""Packaging metadata checks.

The version is stated in two places — `pyproject.toml` and
`ai_use_case_context.__version__` — and the release workflow tags from a
third (the git ref). Nothing reconciles them automatically, so a bump that
misses one ships a package whose reported version is wrong.
"""

import pathlib

import pytest

import ai_use_case_context

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10
    tomllib = None

PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"


@pytest.fixture(scope="module")
def project() -> dict:
    if tomllib is None:
        pytest.skip("tomllib requires Python 3.11+")
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)["project"]


def test_version_matches_pyproject(project):
    assert ai_use_case_context.__version__ == project["version"]


def test_readme_and_authors_are_declared(project):
    """Without these the built package has no description page."""
    assert project.get("readme")
    assert project.get("authors")


def test_project_urls_are_declared(project):
    urls = project.get("urls", {})
    assert {"Homepage", "Repository"} <= set(urls)


def test_declared_readme_exists(project):
    assert (PYPROJECT.parent / project["readme"]).is_file()


# ---------------------------------------------------------------------------
# Documented rule coverage
# ---------------------------------------------------------------------------
#
# The README publishes a per-dimension rule count and states that two
# dimensions have none. Both claims go stale silently the moment a rule is
# added or retargeted, so they are pinned here.

def _rules_by_dimension() -> dict:
    from collections import Counter
    import ai_use_case_context.capability as cap
    import ai_use_case_context.intake as intake
    import ai_use_case_context.operations as ops
    import ai_use_case_context.sourcing as sourcing
    import ai_use_case_context.provenance as prov
    import ai_use_case_context.vendor_scorecard as vendor

    sets = [
        cap.DEFAULT_CAPABILITY_RULES,
        intake.DEFAULT_INTAKE_RULES,
        ops.DEFAULT_OPERATIONAL_RULES,
        sourcing.DEFAULT_SOURCING_RULES,
        prov.DEFAULT_PROVENANCE_RULES,
        vendor.DEFAULT_VENDOR_RULES,
    ]
    return Counter(r.dimension.value for s in sets for r in s)


def test_documented_rule_counts_per_dimension():
    assert _rules_by_dimension() == {
        "Legal / IP Ownership": 29,
        "Security / Model Integrity": 8,
        "Technical Feasibility": 4,
        "Output Quality": 4,
    }


def test_bias_and_safety_have_no_default_rules():
    """The README says these two are empty slots. Keep that honest.

    If a rule is ever added here, the claim in the README and in
    RiskDimension's docstring must be updated in the same change.
    """
    counts = _rules_by_dimension()
    assert counts.get("Bias / Fairness", 0) == 0
    assert counts.get("Safety / Harmful Output", 0) == 0
