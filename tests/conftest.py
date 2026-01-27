"""Shared test fixtures for personal-assistant tests."""

import shutil
from pathlib import Path

import pytest

from personal_assistant import storage
from personal_assistant.schemas import CalendarNotionMapping, Person, Team


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


# --- Additional fixtures for integration tests ---


@pytest.fixture
def sample_person_with_team(temp_data_dir: Path, sample_team: Team):
    """Person assigned to sample_team."""
    person = Person(id="alice", name="Alice Smith", team_ids=["engineering"], role="Developer")
    storage.add_person(person)
    return person


@pytest.fixture
def sample_mapping(temp_data_dir: Path, sample_person: Person):
    """Pre-created mapping for sample_person."""
    mapping = CalendarNotionMapping(
        id="john-1on1",
        calendar_pattern="1:1 John",
        entity_id="john-doe",
        entity_type="person",
    )
    storage.add_mapping(mapping)
    return mapping


@pytest.fixture
def multiple_people(temp_data_dir: Path, sample_team: Team):
    """Multiple people for list/search tests."""
    people = [
        Person(id="alice", name="Alice Smith", team_ids=["engineering"]),
        Person(id="bob", name="Bob Jones", role="Manager"),
        Person(id="charlie", name="Charlie Brown", tags=["contractor"]),
    ]
    for p in people:
        storage.add_person(p)
    return people


@pytest.fixture
def multiple_teams(temp_data_dir: Path):
    """Multiple teams for list tests."""
    teams = [
        Team(id="engineering", name="Engineering", team_type="product"),
        Team(id="design", name="Design Team", team_type="creative"),
        Team(id="sales", name="Sales", team_type="revenue"),
    ]
    for t in teams:
        storage.add_team(t)
    return teams


@pytest.fixture
def person_with_memory(temp_data_dir: Path, sample_person: Person):
    """Person with existing memory entries."""
    storage.save_memory_entry("person", "john-doe", "First observation", "2026-01-01")
    storage.save_memory_entry(
        "person", "john-doe", "Second note", "2026-01-15", entry_type="note"
    )
    return sample_person
