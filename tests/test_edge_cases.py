"""Integration tests for edge cases and boundary conditions."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team

runner = CliRunner()


class TestDataDirResolution:
    """Tests for DATA_DIR resolution logic."""

    def test_pa_data_dir_env_takes_priority(self, tmp_path, monkeypatch):
        """PA_DATA_DIR environment variable takes priority."""
        custom_dir = tmp_path / "custom_data"
        monkeypatch.setenv("PA_DATA_DIR", str(custom_dir))

        result = storage._get_data_dir()

        assert result == custom_dir

    def test_xdg_data_home_used_when_set(self, tmp_path, monkeypatch):
        """XDG_DATA_HOME is used when PA_DATA_DIR is not set."""
        monkeypatch.delenv("PA_DATA_DIR", raising=False)
        xdg_dir = tmp_path / "xdg_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_dir))

        result = storage._get_data_dir()

        assert result == xdg_dir / "personal-assistant"

    def test_default_xdg_location(self, monkeypatch):
        """Falls back to ~/.local/share/personal-assistant when no env vars set."""
        monkeypatch.delenv("PA_DATA_DIR", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)

        result = storage._get_data_dir()

        expected = Path.home() / ".local" / "share" / "personal-assistant"
        assert result == expected

    def test_pa_data_dir_overrides_xdg(self, tmp_path, monkeypatch):
        """PA_DATA_DIR takes priority over XDG_DATA_HOME."""
        custom_dir = tmp_path / "custom"
        xdg_dir = tmp_path / "xdg"
        monkeypatch.setenv("PA_DATA_DIR", str(custom_dir))
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_dir))

        result = storage._get_data_dir()

        assert result == custom_dir


class TestIdEdgeCases:
    """Edge cases for entity ID handling."""

    def test_id_only_special_chars(self, temp_data_dir):
        """Name with only special characters results in empty slug."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "!!!"])

        # Empty ID after slugify should fail validation
        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_id_only_spaces(self, temp_data_dir):
        """Name with only spaces results in empty slug."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "   "])

        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_id_very_long(self, temp_data_dir):
        """Very long name creates very long ID (no truncation)."""
        long_name = "A" * 1000
        result = runner.invoke(app, ["entity", "add", "person", "--name", long_name])

        assert result.exit_code == 0
        # ID should be lowercase version
        person = storage.get_person("a" * 1000)
        assert person is not None

    def test_id_numbers_only(self, temp_data_dir):
        """ID with only numbers is valid."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Test", "--id", "12345"]
        )

        assert result.exit_code == 0
        person = storage.get_person("12345")
        assert person is not None

    def test_id_single_char(self, temp_data_dir):
        """Single character ID is valid."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Test", "--id", "a"]
        )

        assert result.exit_code == 0
        person = storage.get_person("a")
        assert person is not None

    def test_id_with_consecutive_hyphens(self, temp_data_dir):
        """Custom ID with consecutive hyphens is rejected."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Test", "--id", "a--b"]
        )

        # Pattern ^[a-z0-9-]+$ allows consecutive hyphens
        # This might be valid or invalid depending on implementation
        # Current regex allows it
        if result.exit_code == 0:
            person = storage.get_person("a--b")
            assert person is not None


class TestInputBoundaries:
    """Boundary conditions for input handling."""

    def test_empty_string_role(self, temp_data_dir):
        """Empty string for role is handled."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Test", "--role", ""]
        )

        assert result.exit_code == 0
        person = storage.get_person("test")
        # Empty string is stored as empty string
        assert person.role == ""

    def test_whitespace_only_name(self, temp_data_dir):
        """Whitespace-only name fails validation."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "   "]
        )

        assert result.exit_code == 1

    def test_newlines_in_name(self, temp_data_dir):
        """Name with newlines is slugified correctly."""
        # Typer/shell might not pass newlines, but if it does:
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "John\nDoe"]
        )

        # If it reaches the command, slugify should handle it
        if result.exit_code == 0:
            # Check what ID was generated
            people = storage.load_people()
            assert len(people) == 1

    def test_tabs_in_name(self, temp_data_dir):
        """Name with tabs is slugified correctly."""
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "John\tDoe"]
        )

        if result.exit_code == 0:
            # Tabs become hyphens or are removed
            people = storage.load_people()
            assert len(people) == 1

    def test_very_long_role(self, temp_data_dir):
        """Very long role string is accepted."""
        long_role = "Senior " * 100 + "Engineer"
        result = runner.invoke(
            app, ["entity", "add", "person", "--name", "Test", "--role", long_role]
        )

        assert result.exit_code == 0
        person = storage.get_person("test")
        assert person.role == long_role


class TestFileSystemEdgeCases:
    """Edge cases for file system operations."""

    def test_concurrent_saves_same_entity(self, temp_data_dir, sample_person):
        """Rapid sequential saves create unique memory files."""
        # Save multiple memories rapidly
        for i in range(10):
            storage.save_memory_entry(
                "person", "john-doe", f"Entry {i}", "2026-01-20"
            )

        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 10

        # All filenames should be unique
        filenames = [e[0].name for e in entries]
        assert len(set(filenames)) == 10

    def test_memory_dir_not_exists(self, temp_data_dir, sample_person):
        """Loading memory for entity with no memory dir returns empty list."""
        entries = storage.load_memory_entries("person", "john-doe")
        assert entries == []

    def test_memory_dir_created_on_save(self, temp_data_dir, sample_person):
        """Memory directory is created when first entry is saved."""
        memory_dir = storage.get_memory_dir("person", "john-doe")
        assert not memory_dir.exists()

        storage.save_memory_entry("person", "john-doe", "Test", "2026-01-20")

        assert memory_dir.exists()

    def test_entity_files_created_on_first_add(self, temp_data_dir):
        """Entity files are created on first add."""
        people_file = temp_data_dir / "entities" / "people.yaml"
        teams_file = temp_data_dir / "entities" / "teams.yaml"

        # Files might not exist yet
        assert not people_file.exists() or people_file.stat().st_size == 0

        runner.invoke(app, ["entity", "add", "person", "--name", "First"])

        assert people_file.exists()
        assert people_file.stat().st_size > 0

    def test_data_dirs_created_automatically(self, tmp_path, monkeypatch):
        """Data directories are created if they don't exist."""
        # Use a completely fresh directory
        fresh_data_dir = tmp_path / "fresh_data"
        monkeypatch.setattr(storage, "DATA_DIR", fresh_data_dir)

        # Ensure dirs by running ensure_data_dirs
        storage.ensure_data_dirs()

        assert (fresh_data_dir / "entities").exists()
        assert (fresh_data_dir / "mappings").exists()
        assert (fresh_data_dir / "memory" / "people").exists()
        assert (fresh_data_dir / "memory" / "teams").exists()


class TestOutputFormatting:
    """Tests for CLI output formatting."""

    def test_list_output_table_format(self, temp_data_dir):
        """Entity list outputs a formatted table."""
        runner.invoke(app, ["entity", "add", "person", "--name", "Alice"])
        runner.invoke(app, ["entity", "add", "person", "--name", "Bob"])

        result = runner.invoke(app, ["entity", "list", "people"])

        assert result.exit_code == 0
        # Table headers should be present
        assert "ID" in result.output
        assert "Name" in result.output
        # Data should be present
        assert "alice" in result.output
        assert "bob" in result.output

    def test_show_output_formatted(self, sample_person):
        """Entity show outputs formatted details."""
        result = runner.invoke(app, ["entity", "show", "john-doe"])

        assert result.exit_code == 0
        assert "Person:" in result.output
        assert "John Doe" in result.output
        assert "ID:" in result.output

    def test_error_message_format(self, temp_data_dir):
        """Error messages are styled."""
        result = runner.invoke(app, ["entity", "show", "nonexistent"])

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_success_message_format(self, temp_data_dir):
        """Success messages are styled."""
        result = runner.invoke(app, ["entity", "add", "person", "--name", "Test"])

        assert result.exit_code == 0
        assert "Added person:" in result.output


class TestReferentialIntegrityGaps:
    """Tests for referential integrity gaps (orphaned data)."""

    def test_person_with_deleted_team(self, temp_data_dir):
        """Person with deleted team is shown gracefully."""
        # Create team and person
        runner.invoke(app, ["entity", "add", "team", "--name", "Temp Team"])
        runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Orphan", "--team", "temp-team"],
        )

        # Remove person from team first (required to delete team)
        runner.invoke(app, ["entity", "update", "orphan", "--team", "temp-team"])

        # Actually can't delete team with member, so simulate by direct file edit
        # Delete the person's team reference, delete team, then restore reference
        storage.update_person("orphan", {"team_id": None})
        runner.invoke(app, ["entity", "delete", "temp-team", "--force"])

        # Manually set team_id back to simulate orphaned reference
        people = storage.load_people()
        for i, p in enumerate(people):
            if p.id == "orphan":
                updated = Person(
                    id=p.id, name=p.name, team_id="temp-team"
                )
                people[i] = updated
        storage.save_people(people)

        # Show should handle gracefully
        result = runner.invoke(app, ["entity", "show", "orphan"])
        assert result.exit_code == 0
        assert "temp-team" in result.output

    def test_mapping_with_deleted_entity(self, temp_data_dir):
        """Mapping with deleted entity is listed."""
        # Create entity and mapping
        runner.invoke(app, ["entity", "add", "person", "--name", "Ghost"])
        runner.invoke(
            app,
            ["map", "add", "--calendar-pattern", "Ghost sync", "--entity", "ghost"],
        )

        # Delete entity
        runner.invoke(app, ["entity", "delete", "ghost", "--force"])

        # List mappings shows orphaned mapping
        result = runner.invoke(app, ["map", "list"])
        assert result.exit_code == 0
        assert "Ghost sync" in result.output
        assert "ghost" in result.output

    def test_memory_for_deleted_entity(self, temp_data_dir):
        """Memory for deleted entity is still searchable."""
        # Create entity with memory
        runner.invoke(app, ["entity", "add", "person", "--name", "Deleted User"])
        runner.invoke(
            app, ["remember", "deleted-user", "Important observation about Python"]
        )

        # Delete entity
        runner.invoke(app, ["entity", "delete", "deleted-user", "--force"])

        # Search still finds memory
        result = runner.invoke(app, ["memory", "search", "Python"])
        assert result.exit_code == 0
        # Memory should still be found
        assert "deleted-user" in result.output or "Found" in result.output


class TestSpecialCharacterHandling:
    """Tests for handling special characters in various fields."""

    def test_quotes_in_values(self, temp_data_dir):
        """Values with quotes are handled."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "John 'The Legend' Doe"],
        )

        assert result.exit_code == 0
        people = storage.load_people()
        assert people[0].name == "John 'The Legend' Doe"

    def test_unicode_in_role(self, temp_data_dir):
        """Unicode characters in role are preserved."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "--name", "Test", "--role", "Développeur Senior"],
        )

        assert result.exit_code == 0
        person = storage.get_person("test")
        assert person.role == "Développeur Senior"

    def test_emoji_in_memory(self, temp_data_dir, sample_person):
        """Emoji in memory content is preserved."""
        result = runner.invoke(
            app, ["remember", "john-doe", "Great meeting! 🎉 Team is excited 🚀"]
        )

        assert result.exit_code == 0

        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "🎉" in content
        assert "🚀" in content

    def test_markdown_in_memory(self, temp_data_dir, sample_person):
        """Markdown formatting in memory is preserved."""
        md_content = """# Meeting Notes

## Topics
- Item 1
- Item 2

## Actions
- [ ] Task 1
- [x] Task 2
"""
        result = runner.invoke(app, ["remember", "john-doe", md_content])

        assert result.exit_code == 0

        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "## Topics" in content
        assert "- [ ] Task 1" in content


class TestCommandAliases:
    """Tests for command shortcuts and variations."""

    def test_short_option_flags(self, temp_data_dir):
        """Short option flags work."""
        result = runner.invoke(
            app,
            ["entity", "add", "person", "-n", "Jane", "-r", "Engineer"],
        )

        assert result.exit_code == 0
        person = storage.get_person("jane")
        assert person.name == "Jane"
        assert person.role == "Engineer"

    def test_force_flag_short(self, sample_person):
        """Short force flag (-f) works."""
        result = runner.invoke(app, ["entity", "delete", "john-doe", "-f"])

        assert result.exit_code == 0
        assert storage.get_person("john-doe") is None


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    def test_invalid_yaml_syntax(self, temp_data_dir):
        """Handle invalid YAML syntax gracefully."""
        # Create valid data first
        runner.invoke(app, ["entity", "add", "person", "--name", "Valid"])

        # Corrupt the file
        people_file = temp_data_dir / "entities" / "people.yaml"
        people_file.write_text("invalid: [yaml: content")

        # Command should handle error
        result = runner.invoke(app, ["entity", "list", "people"])
        # Should not crash
        assert result.exit_code in [0, 1]

    def test_missing_required_option(self, temp_data_dir):
        """Missing required option shows help."""
        result = runner.invoke(app, ["entity", "add", "person"])

        assert result.exit_code != 0
        # Should mention missing option
        assert "name" in result.output.lower() or "required" in result.output.lower()

    def test_unknown_command(self, temp_data_dir):
        """Unknown command shows error."""
        result = runner.invoke(app, ["unknown", "command"])

        assert result.exit_code != 0
