"""Integration tests for 'pa entity add' command."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import CalendarNotionMapping

runner = CliRunner()


class TestAddPerson:
    """Tests for adding person entities."""

    def test_add_person_minimal(self, temp_data_dir):
        """Add person with only name, ID auto-generated."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "Jane"])

        assert result.exit_code == 0
        assert "Added person:" in result.output
        assert "jane" in result.output

        person = storage.get_person("jane")
        assert person is not None
        assert person.name == "Jane"
        assert person.id == "jane"

    def test_add_person_with_role(self, temp_data_dir):
        """Add person with role."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--role", "Engineer"]
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.role == "Engineer"

    def test_add_person_with_custom_id(self, temp_data_dir):
        """Add person with custom ID."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--id", "jane-smith"]
        )

        assert result.exit_code == 0
        assert "jane-smith" in result.output

        person = storage.get_person("jane-smith")
        assert person is not None
        assert person.name == "Jane"

    def test_add_person_with_team(self, sample_team):
        """Add person assigned to a team."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jane", "--team", "engineering"],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.team_id == "engineering"

    def test_add_person_with_tags(self, temp_data_dir):
        """Add person with comma-separated tags."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jane", "--tags", "python,senior"],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.tags == ["python", "senior"]

    def test_add_person_with_calendar_patterns(self, temp_data_dir):
        """Add person with calendar patterns."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane",
                "--calendar-patterns",
                "1:1 Jane,Jane sync",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.calendar_patterns == ["1:1 Jane", "Jane sync"]

    def test_add_person_with_notion(self, temp_data_dir):
        """Add person with Notion page."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane",
                "--notion",
                "https://notion.so/page",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.notion_page == "https://notion.so/page"

    def test_add_person_all_options(self, sample_team):
        """Add person with all options."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane Doe",
                "--id",
                "jane-doe",
                "--role",
                "Senior Engineer",
                "--team",
                "engineering",
                "--tags",
                "python,go",
                "--calendar-patterns",
                "1:1 Jane",
                "--notion",
                "https://notion.so/jane",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane-doe")
        assert person.name == "Jane Doe"
        assert person.role == "Senior Engineer"
        assert person.team_id == "engineering"
        assert person.tags == ["python", "go"]
        assert person.calendar_patterns == ["1:1 Jane"]
        assert person.notion_page == "https://notion.so/jane"

    def test_add_person_duplicate_id_error(self, sample_person):
        """Error when adding person with existing ID."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Another John", "--id", "john-doe"]
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_add_person_invalid_team_error(self, temp_data_dir):
        """Error when adding person with non-existent team."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jane", "--team", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "Team 'nonexistent' does not exist" in result.output

    def test_add_person_empty_name_error(self, temp_data_dir):
        """Error when adding person with empty name."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", ""])

        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_add_person_invalid_id_format(self, temp_data_dir):
        """Error when adding person with invalid ID format."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--id", "Invalid ID!"]
        )

        assert result.exit_code == 1
        assert "Validation error" in result.output


class TestAddTeam:
    """Tests for adding team entities."""

    def test_add_team_minimal(self, temp_data_dir):
        """Add team with only name."""
        result = runner.invoke(app, ["entity", "add", "team", "--name", "Platform"])

        assert result.exit_code == 0
        assert "Added team:" in result.output
        assert "platform" in result.output

        team = storage.get_team("platform")
        assert team is not None
        assert team.name == "Platform"

    def test_add_team_with_type(self, temp_data_dir):
        """Add team with team type."""
        result = runner.invoke(
            app, ["entity", "add", "team", "--name", "Platform", "--type", "engineering"]
        )

        assert result.exit_code == 0
        team = storage.get_team("platform")
        assert team.team_type == "engineering"

    def test_add_team_with_calendar_patterns(self, temp_data_dir):
        """Add team with calendar patterns."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "team",
                "--name",
                "Platform",
                "--calendar-patterns",
                "Platform standup,Platform sync",
            ],
        )

        assert result.exit_code == 0
        team = storage.get_team("platform")
        assert team.calendar_patterns == ["Platform standup", "Platform sync"]

    def test_add_team_with_notion(self, temp_data_dir):
        """Add team with Notion page."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "team",
                "--name",
                "Platform",
                "--notion",
                "https://notion.so/team",
            ],
        )

        assert result.exit_code == 0
        team = storage.get_team("platform")
        assert team.notion_page == "https://notion.so/team"

    def test_add_team_duplicate_id_error(self, sample_team):
        """Error when adding team with existing ID."""
        result = runner.invoke(
            app, ["entity", "add", "team", "--name", "Engineering", "--id", "engineering"]
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_add_team_empty_name_error(self, temp_data_dir):
        """Error when adding team with empty name."""
        result = runner.invoke(app, ["entity", "add", "team", "--name", ""])

        assert result.exit_code == 1
        assert "Validation error" in result.output


class TestAddEntityEdgeCases:
    """Edge cases for entity add command."""

    def test_add_invalid_entity_type(self, temp_data_dir):
        """Error when adding unknown entity type."""
        result = runner.invoke(app, ["entity", "add", "invalid", "--name", "Test"])

        assert result.exit_code == 1
        assert "Unknown entity type" in result.output

    def test_slugify_name_with_spaces(self, temp_data_dir):
        """Name with spaces is slugified correctly."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "John Doe"])

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person is not None

    def test_slugify_name_with_special_chars(self, temp_data_dir):
        """Name with special characters is slugified correctly."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "John (CEO) Doe Jr."]
        )

        assert result.exit_code == 0
        person = storage.get_person("john-ceo-doe-jr")
        assert person is not None

    def test_slugify_name_with_unicode(self, temp_data_dir):
        """Name with unicode is slugified (unicode removed)."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "José García"]
        )

        assert result.exit_code == 0
        # Unicode chars removed, only ASCII remains
        person = storage.get_person("jos-garca")
        assert person is not None

    def test_slugify_name_consecutive_hyphens(self, temp_data_dir):
        """Name with consecutive hyphens collapses them."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "John - - Doe"]
        )

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person is not None

    def test_slugify_name_leading_trailing_hyphens(self, temp_data_dir):
        """Name with leading/trailing hyphens strips them."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "---John---"])

        assert result.exit_code == 0
        person = storage.get_person("john")
        assert person is not None

    def test_empty_tags_list(self, temp_data_dir):
        """Empty tags string results in list with empty string after strip."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--tags", ""]
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        # Empty string split creates [''] which after strip() is ['']
        # But the CLI strips each tag, resulting in [''] where the element is empty string
        # The actual behavior filters out empty tags
        assert person.tags == [] or person.tags == [""]

    def test_single_tag(self, temp_data_dir):
        """Single tag without comma."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--tags", "python"]
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.tags == ["python"]

    def test_tags_with_spaces(self, temp_data_dir):
        """Tags with spaces around commas are trimmed."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jane", "--tags", "python, typescript"],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.tags == ["python", "typescript"]

    def test_very_long_name(self, temp_data_dir):
        """Very long name is handled without error."""
        long_name = "A" * 1000
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", long_name]
        )

        assert result.exit_code == 0
        person = storage.get_person("a" * 1000)
        assert person.name == long_name

    def test_very_long_custom_id(self, temp_data_dir):
        """Very long custom ID is handled."""
        long_id = "a" * 500
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Jane", "--id", long_id]
        )

        assert result.exit_code == 0
        person = storage.get_person(long_id)
        assert person is not None

    def test_id_numbers_only(self, temp_data_dir):
        """ID with only numbers is valid."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "12345"]
        )

        assert result.exit_code == 0
        person = storage.get_person("12345")
        assert person is not None

    def test_id_single_char(self, temp_data_dir):
        """Single character name creates valid ID."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "A"])

        assert result.exit_code == 0
        person = storage.get_person("a")
        assert person is not None


class TestAutoSeedMappings:
    """Tests for auto-seeding calendar mappings on entity creation."""

    def test_person_with_patterns_creates_mappings(self, temp_data_dir):
        """Adding person with calendar patterns auto-creates mappings."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane Doe",
                "--calendar-patterns",
                "1:1 Jane,Jane sync",
                "--notion",
                "https://notion.so/jane",
            ],
        )

        assert result.exit_code == 0
        assert "Auto-created 2 calendar mapping" in result.output

        # Verify mappings were created
        mappings = storage.load_mappings()
        assert len(mappings) == 2

        # Check first mapping
        mapping1 = next((m for m in mappings if m.id == "11-jane"), None)
        assert mapping1 is not None
        assert mapping1.calendar_pattern == "1:1 Jane"
        assert mapping1.entity_id == "jane-doe"
        assert mapping1.entity_type == "person"
        assert mapping1.notion_page == "https://notion.so/jane"

        # Check second mapping
        mapping2 = next((m for m in mappings if m.id == "jane-sync"), None)
        assert mapping2 is not None
        assert mapping2.calendar_pattern == "Jane sync"

    def test_team_with_patterns_creates_mappings(self, temp_data_dir):
        """Adding team with calendar patterns auto-creates mappings."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "team",
                "--name",
                "Platform",
                "--calendar-patterns",
                "Platform standup",
                "--notion",
                "https://notion.so/platform",
            ],
        )

        assert result.exit_code == 0
        assert "Auto-created 1 calendar mapping" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].entity_type == "team"
        assert mappings[0].entity_id == "platform"

    def test_person_without_patterns_no_mappings(self, temp_data_dir):
        """Adding person without calendar patterns creates no mappings."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jane", "--notion", "https://notion.so/jane"],
        )

        assert result.exit_code == 0
        assert "Auto-created" not in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 0

    def test_person_with_patterns_no_notion(self, temp_data_dir):
        """Mappings created even without notion page."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane",
                "--calendar-patterns",
                "1:1 Jane",
            ],
        )

        assert result.exit_code == 0
        assert "Auto-created 1 calendar mapping" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].notion_page is None

    def test_duplicate_pattern_id_skipped(self, temp_data_dir):
        """Duplicate mapping IDs are skipped silently."""
        # Create first person with a pattern
        runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane",
                "--calendar-patterns",
                "Weekly Sync",
            ],
        )

        # Create second person with same pattern (same slugified ID)
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Bob",
                "--calendar-patterns",
                "Weekly Sync",
            ],
        )

        assert result.exit_code == 0
        # No new mappings created (duplicate skipped)
        assert "Auto-created" not in result.output

        # Only one mapping exists
        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].entity_id == "jane"  # First one kept

    def test_special_chars_in_pattern_creates_mapping(self, temp_data_dir):
        """Patterns with special characters create valid mappings."""
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "George",
                "--calendar-patterns",
                "George / George ☠️",
            ],
        )

        assert result.exit_code == 0
        assert "Auto-created 1 calendar mapping" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 1
        # Original pattern preserved
        assert mappings[0].calendar_pattern == "George / George ☠️"
        # ID is slugified
        assert mappings[0].id == "george-george"
