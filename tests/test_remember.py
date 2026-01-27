"""Integration tests for the 'pa remember' command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app

runner = CliRunner()


class TestRememberWithText:
    """Tests for remember command with text argument."""

    def test_remember_text_for_person(self, sample_person):
        """Remember text content for a person."""
        result = runner.invoke(app, ["remember", "john-doe", "Great debugging skills"])

        assert result.exit_code == 0
        assert "Saved memory for John Doe" in result.output

        # Verify file was created
        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 1
        _, content = entries[0]
        assert "Great debugging skills" in content

    def test_remember_text_for_team(self, sample_team):
        """Remember text content for a team."""
        result = runner.invoke(app, ["remember", "engineering", "Team morale is high"])

        assert result.exit_code == 0
        assert "Saved memory for Engineering Team" in result.output

        entries = storage.load_memory_entries("team", "engineering")
        assert len(entries) == 1
        _, content = entries[0]
        assert "Team morale is high" in content

    def test_remember_with_context(self, sample_person):
        """Remember text with context option."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "Mentioned interest in ML", "--context", "1:1 meeting 2025-01-27"],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "Context: 1:1 meeting 2025-01-27" in content
        assert "Mentioned interest in ML" in content

    def test_remember_with_type(self, sample_person):
        """Remember with custom entry type."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "This is a note", "--type", "note"],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        filepath, content = entries[0]
        assert "_note_" in filepath.name
        assert "# Note:" in content

    def test_remember_nonexistent_entity(self, temp_data_dir):
        """Error when entity doesn't exist."""
        result = runner.invoke(app, ["remember", "nonexistent", "Some text"])

        assert result.exit_code == 1
        assert "Entity 'nonexistent' not found" in result.output


class TestRememberWithFile:
    """Tests for remember command with --file option."""

    def test_remember_from_file(self, sample_person, temp_markdown_file):
        """Remember content from external markdown file."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(temp_markdown_file)],
        )

        assert result.exit_code == 0
        assert "Saved memory for John Doe" in result.output

        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 1
        _, content = entries[0]
        assert "# Meeting Notes" in content
        assert "Discussed project timeline" in content
        assert "Follow up on design review" in content

    def test_remember_from_file_with_context(self, sample_person, temp_markdown_file):
        """Remember from file with context option."""
        result = runner.invoke(
            app,
            [
                "remember",
                "john-doe",
                "--file",
                str(temp_markdown_file),
                "--context",
                "Weekly sync",
            ],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "Context: Weekly sync" in content
        assert "# Meeting Notes" in content

    def test_remember_from_file_with_type(self, sample_person, temp_markdown_file):
        """Remember from file with custom entry type."""
        result = runner.invoke(
            app,
            [
                "remember",
                "john-doe",
                "--file",
                str(temp_markdown_file),
                "--type",
                "note",
            ],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        filepath, _ = entries[0]
        assert "_note_" in filepath.name

    def test_remember_from_file_for_team(self, sample_team, temp_markdown_file):
        """Remember from file for a team."""
        result = runner.invoke(
            app,
            ["remember", "engineering", "--file", str(temp_markdown_file)],
        )

        assert result.exit_code == 0
        assert "Saved memory for Engineering Team" in result.output

        entries = storage.load_memory_entries("team", "engineering")
        assert len(entries) == 1

    def test_remember_file_not_found(self, sample_person):
        """Error when file doesn't exist."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", "/nonexistent/path/file.md"],
        )

        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_remember_file_is_directory(self, sample_person, tmp_path):
        """Error when path is a directory."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert "Not a file" in result.output


class TestRememberInputValidation:
    """Tests for input validation in remember command."""

    def test_no_text_no_file(self, sample_person):
        """Error when neither text nor file is provided."""
        result = runner.invoke(app, ["remember", "john-doe"])

        assert result.exit_code == 1
        assert "Either provide text argument or --file option" in result.output

    def test_both_text_and_file(self, sample_person, temp_markdown_file):
        """Error when both text and file are provided."""
        result = runner.invoke(
            app,
            ["remember", "john-doe", "Some text", "--file", str(temp_markdown_file)],
        )

        assert result.exit_code == 1
        assert "Cannot provide both text argument and --file option" in result.output


class TestRememberFileContent:
    """Tests for handling various file content types."""

    def test_empty_file(self, sample_person, tmp_path):
        """Handle empty file content."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")

        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(empty_file)],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        assert len(entries) == 1

    def test_unicode_content(self, sample_person, tmp_path):
        """Handle unicode content in file."""
        unicode_file = tmp_path / "unicode.md"
        unicode_file.write_text("Meeting with team member\nTopic: CI/CD improvements")

        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(unicode_file)],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "CI/CD improvements" in content

    def test_multiline_content(self, sample_person, tmp_path):
        """Handle multiline file content."""
        multiline_file = tmp_path / "multiline.md"
        multiline_file.write_text(
            """Line 1
Line 2
Line 3

New paragraph with more content.
"""
        )

        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(multiline_file)],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        _, content = entries[0]
        assert "Line 1" in content
        assert "Line 3" in content
        assert "New paragraph" in content

    def test_large_file(self, sample_person, tmp_path):
        """Handle larger file content."""
        large_file = tmp_path / "large.md"
        # Create a file with 1000 lines
        content = "\n".join([f"Line {i}: Some content here" for i in range(1000)])
        large_file.write_text(content)

        result = runner.invoke(
            app,
            ["remember", "john-doe", "--file", str(large_file)],
        )

        assert result.exit_code == 0
        entries = storage.load_memory_entries("person", "john-doe")
        _, saved_content = entries[0]
        assert "Line 0:" in saved_content
        assert "Line 999:" in saved_content
