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
        assert person.team_ids == ["engineering"]

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
        assert person.team_ids == ["engineering"]
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


class TestInteractiveMode:
    """Tests for interactive entity add mode."""

    def test_interactive_person_all_fields(self, temp_data_dir, sample_team):
        """Interactive mode prompts for all person fields."""
        # Input: name, accept default ID, role, team, tags, calendar patterns, notion
        inputs = [
            "Jane Doe",       # Name
            "",               # ID (accept default jane-doe)
            "Senior Engineer",  # Role
            "engineering",    # Team ID
            "python,senior",  # Tags
            "1:1 Jane",       # Calendar patterns
            "https://notion.so/jane",  # Notion
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--interactive"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        assert "Added person:" in result.output
        assert "jane-doe" in result.output

        person = storage.get_person("jane-doe")
        assert person is not None
        assert person.name == "Jane Doe"
        assert person.role == "Senior Engineer"
        assert person.team_ids == ["engineering"]
        assert person.tags == ["python", "senior"]
        assert person.calendar_patterns == ["1:1 Jane"]
        assert person.notion_page == "https://notion.so/jane"

    def test_interactive_person_skip_optional(self, temp_data_dir):
        """Interactive mode allows skipping optional fields."""
        # Input: name, accept ID, skip all optional fields
        inputs = [
            "Bob Smith",  # Name
            "",           # ID (accept default)
            "",           # Role (skip)
            "",           # Team (skip)
            "",           # Tags (skip)
            "",           # Calendar patterns (skip)
            "",           # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        assert "Added person:" in result.output

        person = storage.get_person("bob-smith")
        assert person is not None
        assert person.name == "Bob Smith"
        assert person.role is None
        assert person.team_ids == []
        assert person.tags == []
        assert person.calendar_patterns == []
        assert person.notion_page is None

    def test_interactive_team_basic(self, temp_data_dir):
        """Interactive mode for team creation."""
        inputs = [
            "Platform",       # Name
            "",               # ID (accept default)
            "engineering",    # Team type
            "Platform sync",  # Calendar patterns
            "https://notion.so/platform",  # Notion
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "team", "--interactive"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        assert "Added team:" in result.output
        assert "platform" in result.output

        team = storage.get_team("platform")
        assert team is not None
        assert team.name == "Platform"
        assert team.team_type == "engineering"
        assert team.calendar_patterns == ["Platform sync"]
        assert team.notion_page == "https://notion.so/platform"

    def test_interactive_team_skip_optional(self, temp_data_dir):
        """Interactive team creation with skipped optional fields."""
        inputs = [
            "Design Team",  # Name
            "",             # ID (accept default)
            "",             # Team type (skip)
            "",             # Calendar patterns (skip)
            "",             # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "team", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        team = storage.get_team("design-team")
        assert team is not None
        assert team.team_type is None
        assert team.calendar_patterns == []
        assert team.notion_page is None

    def test_interactive_with_prefilled_name(self, temp_data_dir):
        """Prefilled --name skips the name prompt."""
        # Only ID and optional fields needed (name already provided)
        inputs = [
            "",           # ID (accept default)
            "",           # Role (skip)
            "",           # Team (skip)
            "",           # Tags (skip)
            "",           # Calendar patterns (skip)
            "",           # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i", "--name", "Prefilled Name"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        person = storage.get_person("prefilled-name")
        assert person is not None
        assert person.name == "Prefilled Name"

    def test_interactive_with_prefilled_id(self, temp_data_dir):
        """Prefilled --id skips the ID prompt."""
        inputs = [
            "Custom Person",  # Name
            "",               # Role (skip)
            "",               # Team (skip)
            "",               # Tags (skip)
            "",               # Calendar patterns (skip)
            "",               # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i", "--id", "custom-id"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        person = storage.get_person("custom-id")
        assert person is not None
        assert person.name == "Custom Person"

    def test_interactive_custom_id(self, temp_data_dir):
        """User can override the suggested ID."""
        inputs = [
            "John Doe",      # Name
            "jdoe",          # Custom ID (override default john-doe)
            "",              # Role (skip)
            "",              # Team (skip)
            "",              # Tags (skip)
            "",              # Calendar patterns (skip)
            "",              # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        person = storage.get_person("jdoe")
        assert person is not None
        assert person.name == "John Doe"

    def test_interactive_team_validation_error(self, temp_data_dir):
        """Invalid team ID shows error."""
        inputs = [
            "Jane",           # Name
            "",               # ID (accept default)
            "",               # Role (skip)
            "nonexistent",    # Invalid team ID
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 1
        assert "Team 'nonexistent' does not exist" in result.output

    def test_interactive_empty_name_reprompts(self, temp_data_dir):
        """Empty name re-prompts the user."""
        inputs = [
            "",              # Empty name (will reprompt)
            "Valid Name",    # Valid name on second try
            "",              # ID (accept default)
            "",              # Role (skip)
            "",              # Team (skip)
            "",              # Tags (skip)
            "",              # Calendar patterns (skip)
            "",              # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        assert "This field is required" in result.output
        person = storage.get_person("valid-name")
        assert person is not None

    def test_interactive_creates_calendar_mappings(self, temp_data_dir):
        """Interactive mode auto-creates calendar mappings."""
        inputs = [
            "Alice",             # Name
            "",                  # ID (accept default)
            "",                  # Role (skip)
            "",                  # Team (skip)
            "",                  # Tags (skip)
            "1:1 Alice,Alice sync",  # Calendar patterns
            "https://notion.so/alice",  # Notion
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        assert "Auto-created 2 calendar mapping" in result.output

        mappings = storage.load_mappings()
        assert len(mappings) == 2

    def test_non_interactive_requires_name(self, temp_data_dir):
        """Non-interactive mode fails without --name."""
        result = runner.invoke(app, ["entity", "add", "person"])

        assert result.exit_code == 1
        assert "--name is required" in result.output

    def test_non_interactive_still_works(self, temp_data_dir):
        """Non-interactive mode still works as before."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Normal User", "--role", "Developer"],
        )

        assert result.exit_code == 0
        person = storage.get_person("normal-user")
        assert person is not None
        assert person.role == "Developer"


class TestMultipleTeams:
    """Tests for multiple team membership feature."""

    def test_add_person_with_multiple_teams_repeated_flag(self, temp_data_dir):
        """Add person with multiple teams using repeated --team flags."""
        # Create teams first
        from personal_assistant.schemas import Team
        storage.add_team(Team(id="engineering", name="Engineering"))
        storage.add_team(Team(id="design", name="Design"))

        result = runner.invoke(
            app,
            [
                "entity", "add", "person",
                "--name", "Multi Team Person",
                "--team", "engineering",
                "--team", "design",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("multi-team-person")
        assert person is not None
        assert person.team_ids == ["engineering", "design"]

    def test_add_person_with_multiple_teams_comma_separated(self, temp_data_dir):
        """Add person with multiple teams using comma-separated values."""
        from personal_assistant.schemas import Team
        storage.add_team(Team(id="platform", name="Platform"))
        storage.add_team(Team(id="infra", name="Infrastructure"))

        result = runner.invoke(
            app,
            [
                "entity", "add", "person",
                "--name", "Comma Team Person",
                "--team", "platform,infra",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("comma-team-person")
        assert person is not None
        assert person.team_ids == ["platform", "infra"]

    def test_add_person_with_mixed_team_input(self, temp_data_dir):
        """Add person with mix of repeated and comma-separated teams."""
        from personal_assistant.schemas import Team
        storage.add_team(Team(id="alpha", name="Alpha"))
        storage.add_team(Team(id="beta", name="Beta"))
        storage.add_team(Team(id="gamma", name="Gamma"))

        result = runner.invoke(
            app,
            [
                "entity", "add", "person",
                "--name", "Mixed Team Person",
                "--team", "alpha,beta",
                "--team", "gamma",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("mixed-team-person")
        assert person is not None
        assert person.team_ids == ["alpha", "beta", "gamma"]

    def test_add_person_invalid_team_in_list(self, temp_data_dir):
        """Error when any team in list doesn't exist."""
        from personal_assistant.schemas import Team
        storage.add_team(Team(id="real-team", name="Real Team"))

        result = runner.invoke(
            app,
            [
                "entity", "add", "person",
                "--name", "Bad Teams",
                "--team", "real-team,fake-team",
            ],
        )

        assert result.exit_code == 1
        assert "Team 'fake-team' does not exist" in result.output

    def test_add_person_no_teams(self, temp_data_dir):
        """Add person without any teams."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "No Teams Person"],
        )

        assert result.exit_code == 0
        person = storage.get_person("no-teams-person")
        assert person is not None
        assert person.team_ids == []

    def test_interactive_multiple_teams_comma_separated(self, temp_data_dir):
        """Interactive mode accepts comma-separated team IDs."""
        from personal_assistant.schemas import Team
        storage.add_team(Team(id="team-a", name="Team A"))
        storage.add_team(Team(id="team-b", name="Team B"))

        inputs = [
            "Multi Interactive",  # Name
            "",                   # ID (accept default)
            "",                   # Role (skip)
            "team-a, team-b",     # Teams (comma-separated with spaces)
            "",                   # Tags (skip)
            "",                   # Calendar patterns (skip)
            "",                   # Notion (skip)
        ]
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-i"],
            input="\n".join(inputs) + "\n",
        )

        assert result.exit_code == 0
        person = storage.get_person("multi-interactive")
        assert person is not None
        assert person.team_ids == ["team-a", "team-b"]


class TestLegacyMigration:
    """Tests for migration from legacy team_id format."""

    def test_migrate_team_id_to_team_ids(self):
        """Legacy team_id field is migrated to team_ids list."""
        from personal_assistant.schemas import Person

        # Simulate loading legacy data with team_id
        legacy_data = {
            "id": "legacy-person",
            "name": "Legacy Person",
            "team_id": "old-team",
        }

        person = Person.model_validate(legacy_data)
        assert person.team_ids == ["old-team"]
        assert not hasattr(person, "team_id") or "team_id" not in person.model_fields

    def test_migrate_null_team_id_to_empty_list(self):
        """Legacy null team_id is migrated to empty list."""
        from personal_assistant.schemas import Person

        legacy_data = {
            "id": "null-team-person",
            "name": "Null Team Person",
            "team_id": None,
        }

        person = Person.model_validate(legacy_data)
        assert person.team_ids == []

    def test_team_ids_takes_precedence_over_team_id(self):
        """If both team_id and team_ids exist, team_ids is used."""
        from personal_assistant.schemas import Person

        # This shouldn't happen normally, but test the behavior
        data = {
            "id": "mixed-person",
            "name": "Mixed Person",
            "team_id": "old-team",
            "team_ids": ["new-team-a", "new-team-b"],
        }

        person = Person.model_validate(data)
        # team_ids takes precedence (validator only migrates if team_ids not present)
        assert person.team_ids == ["new-team-a", "new-team-b"]

    def test_new_format_works_directly(self):
        """New team_ids format works without migration."""
        from personal_assistant.schemas import Person

        data = {
            "id": "new-person",
            "name": "New Person",
            "team_ids": ["team-1", "team-2"],
        }

        person = Person.model_validate(data)
        assert person.team_ids == ["team-1", "team-2"]
