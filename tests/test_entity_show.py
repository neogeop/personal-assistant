"""Integration tests for 'pa entity show' command."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team

runner = CliRunner()


@pytest.fixture
def sample_person_with_team(temp_data_dir, sample_team):
    """Person assigned to sample_team."""
    person = Person(id="alice", name="Alice Smith", team_ids=["engineering"], role="Developer")
    storage.add_person(person)
    return person


@pytest.fixture
def person_with_memory(temp_data_dir, sample_person):
    """Person with existing memory entries."""
    storage.save_memory_entry("person", "john-doe", "First observation", "2026-01-01")
    storage.save_memory_entry(
        "person", "john-doe", "Second note", "2026-01-15", entry_type="note"
    )
    return sample_person


@pytest.fixture
def team_with_members(temp_data_dir, sample_team):
    """Team with multiple members."""
    people = [
        Person(id="member-1", name="Member One", team_ids=["engineering"]),
        Person(id="member-2", name="Member Two", team_ids=["engineering"]),
        Person(id="member-3", name="Member Three", team_ids=["engineering"]),
    ]
    for p in people:
        storage.add_person(p)
    return sample_team, people


class TestShowEntity:
    """Tests for showing entity details."""

    def test_show_person_basic(self, sample_person):
        """Show basic person details."""
        result = runner.invoke(app, ["entity", "show", "john-doe"])

        assert result.exit_code == 0
        assert "Person:" in result.output
        assert "John Doe" in result.output
        assert "john-doe" in result.output
        assert "Engineer" in result.output  # Role

    def test_show_person_with_team(self, sample_person_with_team, sample_team):
        """Show person with team displays team name."""
        result = runner.invoke(app, ["entity", "show", "alice"])

        assert result.exit_code == 0
        assert "Alice Smith" in result.output
        assert "Teams:" in result.output
        assert "Engineering Team" in result.output  # Team name, not just ID

    def test_show_person_with_memory(self, person_with_memory):
        """Show person with memory entries lists files."""
        result = runner.invoke(app, ["entity", "show", "john-doe"])

        assert result.exit_code == 0
        assert "Memory entries:" in result.output
        assert "2026-01-01" in result.output
        assert "2026-01-15" in result.output

    def test_show_person_no_memory(self, sample_person):
        """Show person without memory entries."""
        result = runner.invoke(app, ["entity", "show", "john-doe"])

        assert result.exit_code == 0
        # No memory entries section when empty
        assert "Memory entries:" not in result.output

    def test_show_team_basic(self, sample_team):
        """Show basic team details."""
        result = runner.invoke(app, ["entity", "show", "engineering"])

        assert result.exit_code == 0
        assert "Team:" in result.output
        assert "Engineering Team" in result.output
        assert "engineering" in result.output
        assert "product" in result.output  # Team type

    def test_show_team_with_members(self, team_with_members):
        """Show team with members lists them."""
        team, members = team_with_members
        result = runner.invoke(app, ["entity", "show", "engineering"])

        assert result.exit_code == 0
        assert "Members:" in result.output
        assert "Member One" in result.output
        assert "Member Two" in result.output
        assert "Member Three" in result.output
        assert "(3)" in result.output  # Member count

    def test_show_nonexistent_entity(self, temp_data_dir):
        """Error when showing non-existent entity."""
        result = runner.invoke(app, ["entity", "show", "ghost"])

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_show_person_with_all_fields(self, sample_team):
        """Show person with all optional fields populated."""
        person = Person(
            id="full-person",
            name="Full Person",
            role="Manager",
            team_ids=["engineering"],
            tags=["python", "leadership"],
            calendar_patterns=["1:1 Full", "Full sync"],
            notion_page="https://notion.so/full",
        )
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "show", "full-person"])

        assert result.exit_code == 0
        assert "Full Person" in result.output
        assert "Manager" in result.output
        assert "Engineering Team" in result.output
        assert "python" in result.output
        assert "leadership" in result.output
        assert "1:1 Full" in result.output
        assert "https://notion.so/full" in result.output

    def test_show_person_minimal(self, temp_data_dir):
        """Show person with only required fields."""
        person = Person(id="minimal", name="Minimal Person")
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "show", "minimal"])

        assert result.exit_code == 0
        assert "Minimal Person" in result.output
        # No errors on None fields

    def test_show_team_with_all_fields(self, temp_data_dir):
        """Show team with all optional fields populated."""
        team = Team(
            id="full-team",
            name="Full Team",
            team_type="platform",
            calendar_patterns=["Full standup", "Full sync"],
            notion_page="https://notion.so/full-team",
        )
        storage.add_team(team)

        result = runner.invoke(app, ["entity", "show", "full-team"])

        assert result.exit_code == 0
        assert "Full Team" in result.output
        assert "platform" in result.output
        assert "Full standup" in result.output
        assert "https://notion.so/full-team" in result.output

    def test_show_team_no_members(self, sample_team):
        """Show team without members doesn't show Members section."""
        result = runner.invoke(app, ["entity", "show", "engineering"])

        assert result.exit_code == 0
        # No members section when empty
        assert "Members:" not in result.output

    def test_show_person_with_orphaned_team_reference(self, temp_data_dir):
        """Show person with invalid team_ids handles gracefully."""
        person = Person(id="orphan", name="Orphan User", team_ids=["ghost-team"])
        storage.add_person(person)

        result = runner.invoke(app, ["entity", "show", "orphan"])

        assert result.exit_code == 0
        # Shows the team ID even if team doesn't exist
        assert "ghost-team" in result.output

    def test_show_team_with_memory(self, sample_team):
        """Show team with memory entries."""
        storage.save_memory_entry("team", "engineering", "Team observation", "2026-01-10")

        result = runner.invoke(app, ["entity", "show", "engineering"])

        assert result.exit_code == 0
        assert "Memory entries:" in result.output
        assert "2026-01-10" in result.output
