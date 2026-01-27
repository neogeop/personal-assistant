"""Integration tests for cross-command workflows."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team, CalendarNotionMapping

runner = CliRunner()


class TestEntityLifecycle:
    """Tests for complete entity lifecycle workflows."""

    def test_team_then_person_workflow(self, temp_data_dir):
        """Create team, then add person to team, list shows relationship."""
        # Step 1: Create team
        result = runner.invoke(
            app, ["entity", "add", "team", "--name", "Platform", "--type", "engineering"]
        )
        assert result.exit_code == 0
        assert "Added team:" in result.output

        # Step 2: Add person to team
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Jane Doe",
                "--team",
                "platform",
                "--role",
                "Engineer",
            ],
        )
        assert result.exit_code == 0
        assert "Added person:" in result.output

        # Step 3: List shows relationship
        result = runner.invoke(app, ["entity", "list", "people"])
        assert result.exit_code == 0
        assert "jane-doe" in result.output
        assert "platform" in result.output

        # Step 4: Show team shows member
        result = runner.invoke(app, ["entity", "show", "platform"])
        assert result.exit_code == 0
        assert "Jane Doe" in result.output
        assert "Members:" in result.output

    def test_person_memory_workflow(self, temp_data_dir):
        """Create person, add memory, search, show memory."""
        # Step 1: Create person
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Alice Smith"]
        )
        assert result.exit_code == 0

        # Step 2: Add memory entries
        result = runner.invoke(
            app, ["remember", "alice-smith", "Excellent Python skills"]
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app, ["remember", "alice-smith", "Interested in ML projects"]
        )
        assert result.exit_code == 0

        # Step 3: Search memory
        result = runner.invoke(app, ["memory", "search", "Python"])
        assert result.exit_code == 0
        assert "alice-smith" in result.output
        assert "Found" in result.output

        # Step 4: Show entity shows memory count
        result = runner.invoke(app, ["entity", "show", "alice-smith"])
        assert result.exit_code == 0
        assert "Memory entries:" in result.output
        assert "(2)" in result.output

        # Step 5: Memory show lists all entries
        result = runner.invoke(app, ["memory", "show", "alice-smith"])
        assert result.exit_code == 0
        assert "Excellent Python skills" in result.output
        assert "Interested in ML projects" in result.output

    def test_update_preserves_relationships(self, temp_data_dir):
        """Update person preserves team relationship."""
        # Setup
        runner.invoke(app, ["entity", "add", "team", "--name", "Engineering"])
        runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Bob", "--team", "engineering"],
        )

        # Verify initial state
        person = storage.get_person("bob")
        assert person.team_ids == ["engineering"]

        # Update name
        result = runner.invoke(
            app, ["entity", "update", "bob", "--name", "Robert", "--role", "Lead"]
        )
        assert result.exit_code == 0

        # Verify relationship preserved
        person = storage.get_person("bob")
        assert person.team_ids == ["engineering"]
        assert person.name == "Robert"
        assert person.role == "Lead"

    def test_delete_then_recreate(self, temp_data_dir):
        """Delete person, then recreate with same ID."""
        # Create
        runner.invoke(app, ["entity", "add", "person", "--name", "Charlie"])
        assert storage.get_person("charlie") is not None

        # Delete
        runner.invoke(app, ["entity", "delete", "charlie", "--force"])
        assert storage.get_person("charlie") is None

        # Recreate with same ID but different data
        result = runner.invoke(
            app,
            [
                "entity",
                "add",
                "person",
                "--name",
                "Charlie Brown",
                "--id",
                "charlie",
                "--role",
                "Designer",
            ],
        )
        assert result.exit_code == 0

        person = storage.get_person("charlie")
        assert person.name == "Charlie Brown"
        assert person.role == "Designer"


class TestMappingWorkflows:
    """Tests for mapping-related workflows."""

    def test_entity_mapping_workflow(self, temp_data_dir):
        """Create person, create mapping, list mappings."""
        # Create person
        runner.invoke(app, ["entity", "add", "person", "--name", "Dave"])

        # Create mapping
        result = runner.invoke(
            app,
            [
                "map",
                "add",
                "--calendar-pattern",
                "1:1 Dave",
                "--entity",
                "dave",
                "--notion",
                "https://notion.so/dave",
            ],
        )
        assert result.exit_code == 0

        # List mappings
        result = runner.invoke(app, ["map", "list"])
        assert result.exit_code == 0
        assert "1:1 Dave" in result.output
        assert "dave" in result.output
        assert "person" in result.output

    def test_delete_entity_orphans_mapping(self, temp_data_dir):
        """Deleting entity leaves mapping orphaned."""
        # Setup
        runner.invoke(app, ["entity", "add", "person", "--name", "Eve"])
        runner.invoke(
            app,
            ["map", "add", "--calendar-pattern", "Eve sync", "--entity", "eve"],
        )

        # Verify mapping exists
        mappings = storage.load_mappings()
        assert len(mappings) == 1

        # Delete person
        runner.invoke(app, ["entity", "delete", "eve", "--force"])

        # Mapping still exists (orphaned)
        mappings = storage.load_mappings()
        assert len(mappings) == 1
        assert mappings[0].entity_id == "eve"

        # List mappings still works
        result = runner.invoke(app, ["map", "list"])
        assert result.exit_code == 0
        assert "eve" in result.output

    def test_multiple_mappings_per_entity(self, temp_data_dir):
        """Create multiple mappings for same entity."""
        runner.invoke(app, ["entity", "add", "person", "--name", "Frank"])

        # Add multiple mappings
        for pattern in ["1:1 Frank", "Frank sync", "Team meeting with Frank"]:
            result = runner.invoke(
                app,
                ["map", "add", "--calendar-pattern", pattern, "--entity", "frank"],
            )
            assert result.exit_code == 0

        mappings = storage.load_mappings()
        assert len(mappings) == 3

        frank_mappings = [m for m in mappings if m.entity_id == "frank"]
        assert len(frank_mappings) == 3


class TestMultiEntityOperations:
    """Tests for operations with many entities."""

    def test_bulk_entity_creation(self, temp_data_dir):
        """Create many entities and list them."""
        # Create 50 people
        for i in range(50):
            result = runner.invoke(
                app, ["entity", "add", "person", "--name", f"Person {i:03d}"]
            )
            assert result.exit_code == 0

        # List shows all
        result = runner.invoke(app, ["entity", "list", "people"])
        assert result.exit_code == 0
        assert "person-000" in result.output
        assert "person-049" in result.output

        # Verify count
        people = storage.load_people()
        assert len(people) == 50

    def test_team_with_many_members(self, temp_data_dir):
        """Team with many members blocks deletion."""
        # Create team
        runner.invoke(app, ["entity", "add", "team", "--name", "Big Team"])

        # Add 20 members
        for i in range(20):
            runner.invoke(
                app,
                [
                    "entity",
                    "add",
                    "person",
                    "--name",
                    f"Member {i}",
                    "--team",
                    "big-team",
                ],
            )

        # Try to delete team
        result = runner.invoke(app, ["entity", "delete", "big-team", "--force"])
        assert result.exit_code == 1
        assert "Cannot delete team" in result.output
        assert "has members" in result.output

    def test_memory_across_many_entities(self, temp_data_dir):
        """Search memory across many entities."""
        # Create 10 entities with 5 memories each
        for i in range(10):
            person = Person(id=f"person-{i}", name=f"Person {i}")
            storage.add_person(person)
            for j in range(5):
                storage.save_memory_entry(
                    "person",
                    f"person-{i}",
                    f"Memory {j} for person {i} about Python",
                    f"2026-01-{(i+1):02d}",
                )

        # Search should find matches across entities
        result = runner.invoke(app, ["memory", "search", "Python"])
        assert result.exit_code == 0
        assert "Found" in result.output
        # Should find in all 10 entities * 5 memories = 50 results
        # (output might be truncated but should find many)


class TestDataConsistency:
    """Tests for data consistency and error recovery."""

    def test_yaml_file_corruption_recovery(self, temp_data_dir):
        """Graceful handling of corrupted YAML."""
        # Create valid data
        runner.invoke(app, ["entity", "add", "person", "--name", "Grace"])

        # Corrupt the YAML file
        people_file = temp_data_dir / "entities" / "people.yaml"
        people_file.write_text("invalid: yaml: [content")

        # Operations should fail gracefully
        result = runner.invoke(app, ["entity", "list", "people"])
        # Should either show error or empty list, not crash
        assert result.exit_code in [0, 1]

    def test_partial_data_state(self, temp_data_dir):
        """Handle case where some data files are missing."""
        # Create team but no people
        runner.invoke(app, ["entity", "add", "team", "--name", "Solo Team"])

        # Delete people.yaml manually
        people_file = temp_data_dir / "entities" / "people.yaml"
        if people_file.exists():
            people_file.unlink()

        # List should handle gracefully
        result = runner.invoke(app, ["entity", "list"])
        assert result.exit_code == 0
        assert "Solo Team" in result.output

    def test_empty_yaml_files(self, temp_data_dir):
        """Handle empty YAML files."""
        # Create and then empty the file
        runner.invoke(app, ["entity", "add", "person", "--name", "Henry"])

        people_file = temp_data_dir / "entities" / "people.yaml"
        people_file.write_text("")

        # List should return empty, not error
        result = runner.invoke(app, ["entity", "list", "people"])
        assert result.exit_code == 0
        assert "No people found" in result.output


class TestCrossCommandDependencies:
    """Tests for commands that depend on each other."""

    def test_config_affects_nothing_yet(self, temp_data_dir):
        """Config values are stored but not used by other commands yet."""
        # Set config
        runner.invoke(app, ["config", "set", "default_team", "default"])

        # Create person without team - default_team not auto-applied
        runner.invoke(app, ["entity", "add", "person", "--name", "Ivy"])

        person = storage.get_person("ivy")
        # default_team config is not used by entity add
        assert person.team_ids == []

    def test_remember_requires_entity(self, temp_data_dir):
        """Remember command requires existing entity."""
        result = runner.invoke(app, ["remember", "nonexistent", "Some memory"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_map_requires_entity(self, temp_data_dir):
        """Map add requires existing entity."""
        result = runner.invoke(
            app,
            ["map", "add", "--calendar-pattern", "Ghost meeting", "--entity", "ghost"],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_person_team_reference_validated(self, temp_data_dir):
        """Person team reference is validated on add."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Jack", "--team", "nonexistent"],
        )
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_update_team_reference_validated(self, temp_data_dir):
        """Person team reference is validated on update."""
        runner.invoke(app, ["entity", "add", "person", "--name", "Kate"])

        result = runner.invoke(
            app, ["entity", "update", "kate", "--team", "nonexistent"]
        )
        assert result.exit_code == 1
        assert "does not exist" in result.output
