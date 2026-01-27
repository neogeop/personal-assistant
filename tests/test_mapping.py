"""Integration tests for 'pa map' commands."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import CalendarNotionMapping

runner = CliRunner()


@pytest.fixture
def sample_mapping(temp_data_dir, sample_person):
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
def multiple_mappings(temp_data_dir, sample_person, sample_team):
    """Multiple mappings for list tests."""
    mappings = [
        CalendarNotionMapping(
            id="john-1on1",
            calendar_pattern="1:1 John",
            entity_id="john-doe",
            entity_type="person",
        ),
        CalendarNotionMapping(
            id="john-sync",
            calendar_pattern="John sync",
            entity_id="john-doe",
            entity_type="person",
            notion_page="https://notion.so/sync",
        ),
        CalendarNotionMapping(
            id="eng-standup",
            calendar_pattern="Engineering standup",
            entity_id="engineering",
            entity_type="team",
        ),
    ]
    for m in mappings:
        storage.add_mapping(m)
    return mappings


class TestAddMapping:
    """Tests for adding calendar-notion mappings."""

    def test_add_mapping_person(self, sample_person):
        """Add mapping to a person."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "1:1 John",
                "--entity",
                "john-doe",
            ],
        )

        assert result.exit_code == 0
        assert "Added mapping:" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].calendar_pattern == "1:1 John"
        assert mappings[0].entity_id == "john-doe"
        assert mappings[0].entity_type == "person"

    def test_add_mapping_team(self, sample_team):
        """Add mapping to a team."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "Engineering standup",
                "--entity",
                "engineering",
            ],
        )

        assert result.exit_code == 0
        assert "Added mapping:" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].entity_type == "team"

    def test_add_mapping_with_notion(self, sample_person):
        """Add mapping with Notion page."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "1:1 John",
                "--entity",
                "john-doe",
                "--notion",
                "https://notion.so/1on1",
            ],
        )

        assert result.exit_code == 0

        mappings = storage.load_mappings()
        assert mappings[0].notion_page == "https://notion.so/1on1"

    def test_add_mapping_custom_id(self, sample_person):
        """Add mapping with custom ID."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "1:1 John",
                "--entity",
                "john-doe",
                "--id",
                "custom-mapping-id",
            ],
        )

        assert result.exit_code == 0
        assert "custom-mapping-id" in result.output

        mappings = storage.load_mappings()
        assert mappings[0].id == "custom-mapping-id"

    def test_add_mapping_invalid_entity(self, temp_data_dir):
        """Error when entity doesn't exist."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "Ghost meeting",
                "--entity",
                "nonexistent",
            ],
        )

        assert result.exit_code == 1
        assert "Entity 'nonexistent' not found" in result.output

    def test_add_mapping_duplicate_id(self, sample_mapping, sample_person):
        """Error when mapping ID already exists."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "Another pattern",
                "--entity",
                "john-doe",
                "--id",
                "john-1on1",  # Same as sample_mapping
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_add_mapping_auto_id_from_pattern(self, sample_person):
        """ID is auto-generated from pattern when not specified."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "Weekly Sync Meeting",
                "--entity",
                "john-doe",
            ],
        )

        assert result.exit_code == 0
        assert "weekly-sync-meeting" in result.output

    def test_add_mapping_special_chars_in_pattern(self, sample_person):
        """Pattern with special characters is preserved."""
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "1:1 w/ John (weekly)",
                "--entity",
                "john-doe",
            ],
        )

        assert result.exit_code == 0

        mappings = storage.load_mappings()
        assert mappings[0].calendar_pattern == "1:1 w/ John (weekly)"


class TestListMappings:
    """Tests for listing mappings."""

    def test_list_mappings_empty(self, temp_data_dir):
        """List mappings when none exist."""
        result = runner.invoke(app, ["map", "list"])

        assert result.exit_code == 0
        assert "No mappings found" in result.output

    def test_list_mappings_with_data(self, multiple_mappings):
        """List mappings with data."""
        result = runner.invoke(app, ["map", "list"])

        assert result.exit_code == 0
        assert "Calendar-Notion Mappings" in result.output
        assert "john-1on1" in result.output
        assert "john-sync" in result.output
        assert "eng-standup" in result.output
        assert "1:1 John" in result.output
        # Rich table may wrap long text, so check for parts
        assert "Engineering" in result.output
        assert "standup" in result.output

    def test_list_mappings_shows_all_columns(self, multiple_mappings):
        """List shows all expected columns."""
        result = runner.invoke(app, ["map", "list"])

        assert result.exit_code == 0
        # Column headers (Rich may wrap headers, so check for key parts)
        assert "ID" in result.output
        # "Calendar Pattern" may be split across lines
        assert "Calendar" in result.output
        assert "Pattern" in result.output
        assert "Entity" in result.output  # Part of "Entity Type" and "Entity ID"
        assert "Notion" in result.output  # Part of "Notion Page"
        # Data values
        assert "person" in result.output
        assert "team" in result.output
        # URL is truncated with ellipsis in Rich table output
        assert "https://notion" in result.output or "notion" in result.output.lower()


class TestDeleteMapping:
    """Tests for deleting mappings."""

    def test_delete_mapping_force(self, sample_mapping):
        """Delete mapping with --force flag."""
        result = runner.invoke(app, ["map", "delete", "john-1on1", "--force"])

        assert result.exit_code == 0
        assert "Deleted mapping:" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 0

    def test_delete_mapping_confirm_yes(self, sample_mapping):
        """Delete mapping with confirmation (yes)."""
        result = runner.invoke(
            app, ["map", "delete", "john-1on1"], input="y\n"
        )

        assert result.exit_code == 0
        assert "Deleted mapping:" in result.output

    def test_delete_mapping_confirm_no(self, sample_mapping):
        """Cancel mapping deletion with confirmation (no)."""
        result = runner.invoke(
            app, ["map", "delete", "john-1on1"], input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Mapping should still exist
        mappings = storage.load_mappings()
        assert len(mappings) == 1

    def test_delete_mapping_not_found(self, temp_data_dir):
        """Error when deleting non-existent mapping."""
        result = runner.invoke(app, ["map", "delete", "ghost", "--force"])

        assert result.exit_code == 1
        assert "Mapping 'ghost' not found" in result.output

    def test_delete_one_of_many(self, multiple_mappings):
        """Delete one mapping, others remain."""
        result = runner.invoke(app, ["map", "delete", "john-sync", "--force"])

        assert result.exit_code == 0

        mappings = storage.load_mappings()
        assert len(mappings) == 2
        ids = [m.id for m in mappings]
        assert "john-sync" not in ids
        assert "john-1on1" in ids
        assert "eng-standup" in ids


class TestMappingEdgeCases:
    """Edge cases for mapping operations."""

    def test_mapping_to_person_vs_team_priority(self, temp_data_dir):
        """When both person and team have same ID, person takes priority."""
        # Create person with ID "shared"
        from personal_assistant.schemas import Person, Team

        person = Person(id="shared", name="Shared Person")
        storage.add_person(person)

        # Create team with ID "shared" - this would fail due to same storage
        # Actually, person and team are in separate files, so this is allowed
        team = Team(id="shared", name="Shared Team")
        storage.add_team(team)

        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "Shared meeting",
                "--entity",
                "shared",
            ],
        )

        assert result.exit_code == 0

        mappings = storage.load_mappings()
        # Person takes priority (checked first in CLI)
        assert mappings[0].entity_type == "person"

    def test_mapping_after_entity_deleted(self, sample_mapping, sample_person):
        """Mapping remains after entity is deleted (orphaned)."""
        # Delete the person
        storage.delete_person("john-doe")

        # List mappings still shows the orphaned mapping
        result = runner.invoke(app, ["map", "list"])

        assert result.exit_code == 0
        assert "john-1on1" in result.output
        assert "john-doe" in result.output

    def test_add_mapping_long_pattern(self, sample_person):
        """Mapping with very long pattern."""
        long_pattern = "A" * 500
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                long_pattern,
                "--entity",
                "john-doe",
            ],
        )

        assert result.exit_code == 0

        mappings = storage.load_mappings()
        assert mappings[0].calendar_pattern == long_pattern
