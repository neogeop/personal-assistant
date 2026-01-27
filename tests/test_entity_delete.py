"""Integration tests for 'pa entity delete' command."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team, CalendarNotionMapping

runner = CliRunner()


@pytest.fixture
def person_with_memory(temp_data_dir, sample_person):
    """Person with existing memory entries."""
    storage.save_memory_entry("person", "john-doe", "Observation 1", "2026-01-01")
    storage.save_memory_entry("person", "john-doe", "Observation 2", "2026-01-15")
    return sample_person


@pytest.fixture
def team_with_members(temp_data_dir, sample_team):
    """Team with multiple members."""
    people = [
        Person(id="member-1", name="Member One", team_ids=["engineering"]),
        Person(id="member-2", name="Member Two", team_ids=["engineering"]),
    ]
    for p in people:
        storage.add_person(p)
    return sample_team, people


@pytest.fixture
def person_with_mapping(temp_data_dir, sample_person):
    """Person with a calendar mapping."""
    mapping = CalendarNotionMapping(
        id="john-1on1",
        calendar_pattern="1:1 John",
        entity_id="john-doe",
        entity_type="person",
    )
    storage.add_mapping(mapping)
    return sample_person, mapping


class TestDeletePerson:
    """Tests for deleting person entities."""

    def test_delete_person_with_force(self, sample_person):
        """Delete person with --force flag."""
        result = runner.invoke(app, ["entity", "delete", "john-doe", "--force"])

        assert result.exit_code == 0
        assert "Deleted person:" in result.output
        assert "john-doe" in result.output

        # Verify person is gone
        person = storage.get_person("john-doe")
        assert person is None

    def test_delete_person_confirm_yes(self, sample_person):
        """Delete person with confirmation prompt (yes)."""
        result = runner.invoke(
            app, ["entity", "delete", "john-doe"], input="y\n"
        )

        assert result.exit_code == 0
        assert "Deleted person:" in result.output

        person = storage.get_person("john-doe")
        assert person is None

    def test_delete_person_confirm_no(self, sample_person):
        """Cancel deletion with confirmation prompt (no)."""
        result = runner.invoke(
            app, ["entity", "delete", "john-doe"], input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Person should still exist
        person = storage.get_person("john-doe")
        assert person is not None

    def test_delete_person_not_found(self, temp_data_dir):
        """Error when deleting non-existent person."""
        result = runner.invoke(app, ["entity", "delete", "ghost", "--force"])

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_delete_person_keeps_memory(self, person_with_memory):
        """Memory files remain after person deletion (no cascade)."""
        # Verify memory exists before deletion
        entries_before = storage.load_memory_entries("person", "john-doe")
        assert len(entries_before) == 2

        result = runner.invoke(app, ["entity", "delete", "john-doe", "--force"])

        assert result.exit_code == 0

        # Memory files should still exist (orphaned)
        entries_after = storage.load_memory_entries("person", "john-doe")
        assert len(entries_after) == 2


class TestDeleteTeam:
    """Tests for deleting team entities."""

    def test_delete_team_empty(self, sample_team):
        """Delete team with no members."""
        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])

        assert result.exit_code == 0
        assert "Deleted team:" in result.output

        team = storage.get_team("engineering")
        assert team is None

    def test_delete_team_with_members_error(self, team_with_members):
        """Error when deleting team with members."""
        team, members = team_with_members
        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])

        assert result.exit_code == 1
        assert "Cannot delete team" in result.output
        assert "has members" in result.output
        # Should list member names
        assert "Member One" in result.output
        assert "Member Two" in result.output

        # Team should still exist
        team = storage.get_team("engineering")
        assert team is not None

    def test_delete_team_not_found(self, temp_data_dir):
        """Error when deleting non-existent team."""
        result = runner.invoke(app, ["entity", "delete", "ghost", "--force"])

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_delete_team_confirm_yes(self, sample_team):
        """Delete team with confirmation prompt (yes)."""
        result = runner.invoke(
            app, ["entity", "delete", "engineering"], input="y\n"
        )

        assert result.exit_code == 0
        assert "Deleted team:" in result.output

        team = storage.get_team("engineering")
        assert team is None

    def test_delete_team_confirm_no(self, sample_team):
        """Cancel team deletion with confirmation prompt (no)."""
        result = runner.invoke(
            app, ["entity", "delete", "engineering"], input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        team = storage.get_team("engineering")
        assert team is not None


class TestDeleteCascadeGaps:
    """Tests for cascade gaps (orphaned data after deletion)."""

    def test_delete_person_orphans_mapping(self, person_with_mapping):
        """Mapping becomes orphaned after person deletion."""
        person, mapping = person_with_mapping

        result = runner.invoke(app, ["entity", "delete", "john-doe", "--force"])

        assert result.exit_code == 0

        # Mapping should still exist (orphaned)
        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].id == "john-1on1"
        assert mappings[0].entity_id == "john-doe"  # Points to deleted entity

    def test_delete_team_orphans_memory(self, sample_team):
        """Memory files remain after team deletion (orphaned)."""
        storage.save_memory_entry("team", "engineering", "Team observation", "2026-01-10")

        # Verify memory exists
        entries_before = storage.load_memory_entries("team", "engineering")
        assert len(entries_before) == 1

        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])

        assert result.exit_code == 0

        # Memory should still exist (orphaned)
        entries_after = storage.load_memory_entries("team", "engineering")
        assert len(entries_after) == 1

    def test_show_orphaned_person_team_reference(self, sample_team):
        """Person with deleted team shows gracefully."""
        # Create person with team
        person = Person(id="orphan", name="Orphan", team_ids=["engineering"])
        storage.add_person(person)

        # Delete team directly (bypassing CLI constraint by manual file edit)
        # Actually need to first remove the person from team
        storage.update_person("orphan", {"team_ids": []})

        # Now delete team
        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])
        assert result.exit_code == 0

        # Manually set team_ids back to simulate orphaned reference
        # This simulates data corruption or external modification
        people = storage.load_people()
        for i, p in enumerate(people):
            if p.id == "orphan":
                people[i] = Person(
                    id="orphan", name="Orphan", team_ids=["engineering"]
                )
        storage.save_people(people)

        # Show should handle gracefully
        result = runner.invoke(app, ["entity", "show", "orphan"])
        assert result.exit_code == 0
        # Shows the team ID even though team doesn't exist
        assert "engineering" in result.output


class TestDeleteMultipleEntities:
    """Tests for deleting multiple entities in sequence."""

    def test_delete_multiple_people(self, temp_data_dir):
        """Delete multiple people in sequence."""
        for i in range(3):
            person = Person(id=f"person-{i}", name=f"Person {i}")
            storage.add_person(person)

        for i in range(3):
            result = runner.invoke(
                app, ["entity", "delete", f"person-{i}", "--force"]
            )
            assert result.exit_code == 0

        # All should be gone
        for i in range(3):
            assert storage.get_person(f"person-{i}") is None

    def test_delete_team_after_removing_members(self, team_with_members):
        """Delete team after removing all members."""
        team, members = team_with_members

        # First try to delete fails
        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])
        assert result.exit_code == 1

        # Remove members
        for member in members:
            storage.delete_person(member.id)

        # Now deletion succeeds
        result = runner.invoke(app, ["entity", "delete", "engineering", "--force"])
        assert result.exit_code == 0

        team = storage.get_team("engineering")
        assert team is None
