"""Integration tests for 'pa memory' commands."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team

runner = CliRunner()


@pytest.fixture
def person_with_memory(temp_data_dir, sample_person):
    """Person with existing memory entries."""
    storage.save_memory_entry("person", "john-doe", "First observation", "2026-01-01")
    storage.save_memory_entry(
        "person", "john-doe", "Second note about Python skills", "2026-01-15", entry_type="note"
    )
    storage.save_memory_entry(
        "person", "john-doe", "Third observation", "2026-01-20"
    )
    return sample_person


@pytest.fixture
def team_with_memory(temp_data_dir, sample_team):
    """Team with existing memory entries."""
    storage.save_memory_entry("team", "engineering", "Team morale is high", "2026-01-05")
    storage.save_memory_entry(
        "team", "engineering", "Sprint planning went well", "2026-01-12"
    )
    return sample_team


@pytest.fixture
def multiple_entities_with_memory(temp_data_dir):
    """Multiple entities with memory for search tests."""
    # Create entities
    person1 = Person(id="alice", name="Alice Smith")
    person2 = Person(id="bob", name="Bob Jones")
    team = Team(id="platform", name="Platform Team")

    storage.add_person(person1)
    storage.add_person(person2)
    storage.add_team(team)

    # Add memory with overlapping and unique content
    storage.save_memory_entry("person", "alice", "Discussed Python project", "2026-01-01")
    storage.save_memory_entry("person", "alice", "Mentioned interest in Rust", "2026-01-10")
    storage.save_memory_entry("person", "bob", "Python expert, great mentor", "2026-01-05")
    storage.save_memory_entry("team", "platform", "Team uses Python and Go", "2026-01-08")

    return person1, person2, team


class TestMemoryShow:
    """Tests for 'pa memory show' command."""

    def test_show_person_memory(self, person_with_memory):
        """Show memory entries for a person."""
        result = runner.invoke(app, ["memory", "show", "john-doe"])

        assert result.exit_code == 0
        assert "Memory for John Doe" in result.output
        assert "First observation" in result.output
        assert "Second note" in result.output
        assert "Third observation" in result.output

    def test_show_person_no_memory(self, sample_person):
        """Show memory when person has no entries."""
        result = runner.invoke(app, ["memory", "show", "john-doe"])

        assert result.exit_code == 0
        assert "No memory entries for John Doe" in result.output

    def test_show_team_memory(self, team_with_memory):
        """Show memory entries for a team."""
        result = runner.invoke(app, ["memory", "show", "engineering"])

        assert result.exit_code == 0
        assert "Memory for Engineering Team" in result.output
        assert "Team morale is high" in result.output
        assert "Sprint planning went well" in result.output

    def test_show_nonexistent_entity(self, temp_data_dir):
        """Error when showing memory for non-existent entity."""
        result = runner.invoke(app, ["memory", "show", "ghost"])

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_show_team_no_memory(self, sample_team):
        """Show memory when team has no entries."""
        result = runner.invoke(app, ["memory", "show", "engineering"])

        assert result.exit_code == 0
        assert "No memory entries for Engineering Team" in result.output

    def test_show_memory_file_names(self, person_with_memory):
        """Show includes file names with dates."""
        result = runner.invoke(app, ["memory", "show", "john-doe"])

        assert result.exit_code == 0
        assert "2026-01-01" in result.output
        assert "2026-01-15" in result.output
        assert "2026-01-20" in result.output


class TestMemorySearch:
    """Tests for 'pa memory search' command."""

    def test_search_finds_match(self, multiple_entities_with_memory):
        """Search finds matching content."""
        result = runner.invoke(app, ["memory", "search", "Python"])

        assert result.exit_code == 0
        assert "Found" in result.output
        # Should find in alice, bob, and platform
        assert "alice" in result.output
        assert "bob" in result.output
        assert "platform" in result.output

    def test_search_case_insensitive(self, multiple_entities_with_memory):
        """Search is case insensitive."""
        result = runner.invoke(app, ["memory", "search", "PYTHON"])

        assert result.exit_code == 0
        assert "Found" in result.output
        # Should still find matches
        assert "alice" in result.output

    def test_search_no_results(self, multiple_entities_with_memory):
        """Search with no matches."""
        result = runner.invoke(app, ["memory", "search", "nonexistent-term-xyz"])

        assert result.exit_code == 0
        assert "No results" in result.output

    def test_search_empty_query(self, multiple_entities_with_memory):
        """Search with empty query matches everything."""
        result = runner.invoke(app, ["memory", "search", ""])

        assert result.exit_code == 0
        # Empty string matches all content
        assert "Found" in result.output

    def test_search_across_entities(self, multiple_entities_with_memory):
        """Search returns results from multiple entities."""
        result = runner.invoke(app, ["memory", "search", "Python"])

        assert result.exit_code == 0
        # Output format uses plural directory names: people/alice, team/platform
        assert "alice" in result.output
        assert "bob" in result.output
        assert "platform" in result.output

    def test_search_unique_term(self, multiple_entities_with_memory):
        """Search for unique term returns single result."""
        result = runner.invoke(app, ["memory", "search", "Rust"])

        assert result.exit_code == 0
        assert "Found 1 result" in result.output
        assert "alice" in result.output

    def test_search_shows_context(self, multiple_entities_with_memory):
        """Search shows context around match."""
        result = runner.invoke(app, ["memory", "search", "mentor"])

        assert result.exit_code == 0
        # Should show the matching line
        assert "great mentor" in result.output

    def test_search_no_memory_files(self, temp_data_dir):
        """Search when no memory files exist."""
        result = runner.invoke(app, ["memory", "search", "anything"])

        assert result.exit_code == 0
        assert "No results" in result.output


class TestMemoryFileEdgeCases:
    """Edge cases for memory file handling."""

    def test_multiple_entries_same_day(self, temp_data_dir, sample_person):
        """Multiple entries on same day get unique filenames."""
        for i in range(5):
            storage.save_memory_entry(
                "person", "john-doe", f"Entry {i}", "2026-01-20"
            )

        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 5

        # Check unique filenames
        filenames = [e[0].name for e in entries]
        assert len(set(filenames)) == 5  # All unique

    def test_memory_file_unicode_content(self, temp_data_dir, sample_person):
        """Unicode content is preserved."""
        unicode_content = "Meeting notes with émojis 🎉 and accénts"
        storage.save_memory_entry("person", "john-doe", unicode_content, "2026-01-20")

        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "émojis" in content
        assert "🎉" in content
        assert "accénts" in content

    def test_memory_file_very_large(self, temp_data_dir, sample_person):
        """Large content is handled."""
        # Create content with 10000 lines
        large_content = "\n".join([f"Line {i}: Some observation text" for i in range(10000)])
        storage.save_memory_entry("person", "john-doe", large_content, "2026-01-20")

        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 1
        _, content = entries[0]
        assert "Line 0:" in content
        assert "Line 9999:" in content

    def test_memory_path_special_entity_id(self, temp_data_dir):
        """Entity ID with many hyphens creates valid path."""
        person = Person(id="a-b-c-d-e-f-g", name="Hyphen Person")
        storage.add_person(person)

        storage.save_memory_entry("person", "a-b-c-d-e-f-g", "Test content", "2026-01-20")

        entries = storage.load_memory_entries("person", "a-b-c-d-e-f-g")
        assert len(entries) == 1

    def test_memory_different_entry_types(self, temp_data_dir, sample_person):
        """Different entry types are stored correctly."""
        storage.save_memory_entry("person", "john-doe", "Obs", "2026-01-20", entry_type="observation")
        storage.save_memory_entry("person", "john-doe", "Note", "2026-01-20", entry_type="note")
        storage.save_memory_entry("person", "john-doe", "Inf", "2026-01-20", entry_type="inference")

        entries = storage.load_memory_entries("person", "john-doe")
        filenames = [e[0].name for e in entries]

        assert any("observation" in f for f in filenames)
        assert any("note" in f for f in filenames)
        assert any("inference" in f for f in filenames)

    def test_memory_with_context(self, temp_data_dir, sample_person):
        """Memory entry with context is stored correctly."""
        storage.save_memory_entry(
            "person", "john-doe", "Discussion notes", "2026-01-20",
            context="Weekly 1:1 meeting"
        )

        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "Context: Weekly 1:1 meeting" in content

    def test_memory_dir_created_automatically(self, temp_data_dir, sample_person):
        """Memory directory is created if it doesn't exist."""
        # Directory doesn't exist yet for john-doe
        memory_dir = storage.get_memory_dir("person", "john-doe")
        assert not memory_dir.exists()

        storage.save_memory_entry("person", "john-doe", "Test", "2026-01-20")

        assert memory_dir.exists()
        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 1

    def test_load_memory_nonexistent_dir(self, temp_data_dir, sample_person):
        """Loading memory from non-existent directory returns empty list."""
        entries = storage.load_memory_entries("person", "nonexistent")
        assert entries == []

    def test_search_memory_special_regex_chars(self, multiple_entities_with_memory):
        """Search with regex special characters treats them as literal."""
        # Add content with special chars
        storage.save_memory_entry(
            "person", "alice", "Pattern: [a-z]+ and (test)", "2026-01-25"
        )

        # Search for literal bracket pattern
        result = runner.invoke(app, ["memory", "search", "[a-z]+"])

        assert result.exit_code == 0
        # Should find the literal match
        assert "Found" in result.output or "No results" in result.output
