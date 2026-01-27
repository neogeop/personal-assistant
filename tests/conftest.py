"""Shared test fixtures for personal-assistant tests."""

import shutil
from pathlib import Path

import pytest

from personal_assistant import storage


@pytest.fixture
def temp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Override the DATA_DIR to use a temporary directory for tests."""
    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()
    monkeypatch.setattr(storage, "DATA_DIR", test_data_dir)
    storage.ensure_data_dirs()
    yield test_data_dir
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def sample_person(temp_data_dir: Path):
    """Create a sample person for testing."""
    from personal_assistant.schemas import Person

    person = Person(
        id="john-doe",
        name="John Doe",
        role="Engineer",
        tags=["python", "testing"],
    )
    storage.add_person(person)
    return person


@pytest.fixture
def sample_team(temp_data_dir: Path):
    """Create a sample team for testing."""
    from personal_assistant.schemas import Team

    team = Team(
        id="engineering",
        name="Engineering Team",
        team_type="product",
    )
    storage.add_team(team)
    return team


@pytest.fixture
def temp_markdown_file(tmp_path: Path):
    """Create a temporary markdown file with sample content."""
    md_file = tmp_path / "memory.md"
    md_file.write_text(
        """# Meeting Notes

## Discussion Points
- Discussed project timeline
- Reviewed sprint goals
- Identified blockers

## Action Items
- [ ] Follow up on design review
- [ ] Schedule technical deep-dive
"""
    )
    return md_file
