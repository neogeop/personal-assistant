"""Integration tests for 'pa entity list' command."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team

runner = CliRunner()


@pytest.fixture
def multiple_people(temp_data_dir, sample_team):
    """Multiple people for list tests."""
    people = [
        Person(id="alice", name="Alice Smith", team_id="engineering"),
        Person(id="bob", name="Bob Jones", role="Manager"),
        Person(id="charlie", name="Charlie Brown", tags=["contractor"]),
    ]
    for p in people:
        storage.add_person(p)
    return people


@pytest.fixture
def multiple_teams(temp_data_dir):
    """Multiple teams for list tests (no overlap with other fixtures)."""
    teams = [
        Team(id="platform", name="Platform", team_type="product"),
        Team(id="design", name="Design Team", team_type="creative"),
        Team(id="sales", name="Sales", team_type="revenue"),
    ]
    for t in teams:
        storage.add_team(t)
    return teams


class TestListEntities:
    """Tests for listing entities."""

    def test_list_all_empty(self, temp_data_dir):
        """List all when no entities exist."""
        result = runner.invoke(app, ["entity", "list"])

        assert result.exit_code == 0
        assert "No people found" in result.output
        assert "No teams found" in result.output

    def test_list_people_only(self, multiple_people):
        """List only people."""
        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "People" in result.output
        assert "alice" in result.output
        assert "bob" in result.output
        assert "charlie" in result.output
        # Should NOT show teams table
        assert "Teams" not in result.output or "No teams found" in result.output

    def test_list_teams_only(self, multiple_teams):
        """List only teams."""
        result = runner.invoke(app, ["entity", "list", "teams"])

        assert result.exit_code == 0
        assert "Teams" in result.output
        assert "platform" in result.output
        assert "design" in result.output
        assert "sales" in result.output
        # Should NOT show people table
        assert "No people found" in result.output or "People" not in result.output

    def test_list_all_with_data(self, temp_data_dir):
        """List all with both people and teams."""
        # Create teams first
        team = Team(id="platform", name="Platform", team_type="product")
        storage.add_team(team)
        # Create people
        person = Person(id="alice", name="Alice", team_id="platform")
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "list"])

        assert result.exit_code == 0
        # People table
        assert "People" in result.output
        assert "alice" in result.output
        # Teams table
        assert "Teams" in result.output
        assert "platform" in result.output

    def test_list_people_shows_team_id(self, multiple_people):
        """People list shows team ID."""
        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        # Alice has team_id=engineering
        assert "engineering" in result.output

    def test_list_teams_shows_member_count(self, temp_data_dir):
        """Teams list shows member count."""
        # Create team
        team = Team(id="platform", name="Platform", team_type="product")
        storage.add_team(team)
        # Create members
        for i in range(3):
            person = Person(id=f"member-{i}", name=f"Member {i}", team_id="platform")
            storage.add_person(person)

        result = runner.invoke(app, ["entity", "list", "teams"])

        assert result.exit_code == 0
        # Platform team has 3 members
        assert "Platform" in result.output
        assert "3" in result.output  # Member count

    def test_list_with_orphaned_team_reference(self, temp_data_dir):
        """Person with invalid team_id is handled gracefully."""
        # Create person with non-existent team reference
        person = Person(id="orphan", name="Orphan User", team_id="ghost-team")
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "orphan" in result.output
        assert "ghost-team" in result.output  # Shows the ID even if team doesn't exist

    def test_list_invalid_entity_type(self, temp_data_dir):
        """Invalid entity type argument shows nothing (doesn't match people or teams)."""
        # Create some data
        team = Team(id="test-team", name="Test Team")
        storage.add_team(team)
        person = Person(id="test-person", name="Test Person")
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "list", "invalid"])

        # Current behavior: shows nothing for invalid type
        # The command doesn't match "people" or "teams" so shows neither
        assert result.exit_code == 0

    def test_list_people_empty(self, sample_team):
        """List people when only teams exist."""
        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "No people found" in result.output

    def test_list_teams_empty(self, sample_person):
        """List teams when only people exist."""
        result = runner.invoke(app, ["entity", "list", "teams"])

        assert result.exit_code == 0
        assert "No teams found" in result.output

    def test_list_shows_person_role(self, multiple_people):
        """People list shows role field."""
        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "Manager" in result.output  # Bob's role

    def test_list_shows_person_tags(self, multiple_people):
        """People list shows tags field."""
        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "contractor" in result.output  # Charlie's tag

    def test_list_shows_team_type(self, multiple_teams):
        """Teams list shows team type field."""
        result = runner.invoke(app, ["entity", "list", "teams"])

        assert result.exit_code == 0
        assert "product" in result.output  # Engineering team type
        assert "creative" in result.output  # Design team type

    def test_list_many_entities(self, temp_data_dir):
        """List with many entities for performance check."""
        # Create 50 people
        for i in range(50):
            person = Person(id=f"person-{i}", name=f"Person {i}")
            storage.add_person(person)

        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        assert "person-0" in result.output
        assert "person-49" in result.output
