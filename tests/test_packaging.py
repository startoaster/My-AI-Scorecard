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
