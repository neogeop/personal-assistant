"""Integration tests for 'pa config' commands."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app

runner = CliRunner()


class TestConfigSet:
    """Tests for 'pa config set' command."""

    def test_set_default_team(self, temp_data_dir):
        """Set default_team config value."""
        result = runner.invoke(app, ["config", "set", "default_team", "engineering"])

        assert result.exit_code == 0
        assert "Set default_team:" in result.output
        assert "engineering" in result.output

        config = storage.load_config()
        assert config.default_team == "engineering"

    def test_set_notion_workspace(self, temp_data_dir):
        """Set notion_workspace config value."""
        result = runner.invoke(
            app, ["config", "set", "notion_workspace", "https://notion.so/workspace"]
        )

        assert result.exit_code == 0
        assert "Set notion_workspace:" in result.output
        assert "https://notion.so/workspace" in result.output

        config = storage.load_config()
        assert config.notion_workspace == "https://notion.so/workspace"

    def test_set_invalid_key(self, temp_data_dir):
        """Error when setting invalid config key."""
        result = runner.invoke(app, ["config", "set", "invalid_key", "value"])

        assert result.exit_code == 1
        assert "Unknown config key" in result.output
        assert "invalid_key" in result.output
        # Should list valid keys
        assert "default_team" in result.output
        assert "notion_workspace" in result.output

    def test_overwrite_existing(self, temp_data_dir):
        """Overwrite existing config value."""
        # Set initial value
        result = runner.invoke(app, ["config", "set", "default_team", "team1"])
        assert result.exit_code == 0

        # Overwrite with new value
        result = runner.invoke(app, ["config", "set", "default_team", "team2"])
        assert result.exit_code == 0

        config = storage.load_config()
        assert config.default_team == "team2"

    def test_set_empty_value(self, temp_data_dir):
        """Set config to empty string."""
        result = runner.invoke(app, ["config", "set", "default_team", ""])

        assert result.exit_code == 0

        config = storage.load_config()
        assert config.default_team == ""

    def test_set_value_with_spaces(self, temp_data_dir):
        """Set config value with spaces."""
        result = runner.invoke(
            app, ["config", "set", "notion_workspace", "https://notion.so/my workspace"]
        )

        assert result.exit_code == 0

        config = storage.load_config()
        assert config.notion_workspace == "https://notion.so/my workspace"

    def test_set_special_characters(self, temp_data_dir):
        """Set config with special characters."""
        result = runner.invoke(
            app, ["config", "set", "default_team", "team-with-hyphens_and_underscores"]
        )

        assert result.exit_code == 0

        config = storage.load_config()
        assert config.default_team == "team-with-hyphens_and_underscores"


class TestConfigShow:
    """Tests for 'pa config show' command."""

    def test_show_empty_config(self, temp_data_dir):
        """Show config when nothing is set."""
        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "Configuration:" in result.output
        assert "(not set)" in result.output
        # Both keys should show (not set)
        assert "default_team:" in result.output
        assert "notion_workspace:" in result.output

    def test_show_partial_config(self, temp_data_dir):
        """Show config with one key set."""
        # Set one value
        runner.invoke(app, ["config", "set", "default_team", "engineering"])

        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "engineering" in result.output
        assert "(not set)" in result.output  # notion_workspace not set

    def test_show_full_config(self, temp_data_dir):
        """Show config with all keys set."""
        runner.invoke(app, ["config", "set", "default_team", "engineering"])
        runner.invoke(
            app, ["config", "set", "notion_workspace", "https://notion.so/ws"]
        )

        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "engineering" in result.output
        assert "https://notion.so/ws" in result.output
        # No "(not set)" when all configured
        assert "(not set)" not in result.output


class TestConfigPersistence:
    """Tests for config persistence across commands."""

    def test_config_persists_across_commands(self, temp_data_dir):
        """Config values persist after being set."""
        # Set values
        runner.invoke(app, ["config", "set", "default_team", "eng"])
        runner.invoke(app, ["config", "set", "notion_workspace", "https://notion.so"])

        # Verify via show
        result = runner.invoke(app, ["config", "show"])
        assert "eng" in result.output
        assert "https://notion.so" in result.output

        # Verify via storage
        config = storage.load_config()
        assert config.default_team == "eng"
        assert config.notion_workspace == "https://notion.so"

    def test_config_survives_entity_operations(self, temp_data_dir):
        """Config is not affected by entity operations."""
        # Set config
        runner.invoke(app, ["config", "set", "default_team", "team1"])

        # Do some entity operations
        runner.invoke(app, ["entity", "add", "person", "--name", "Jane"])
        runner.invoke(app, ["entity", "list"])

        # Config should still be there
        result = runner.invoke(app, ["config", "show"])
        assert "team1" in result.output

    def test_config_file_created_on_first_set(self, temp_data_dir):
        """Config file is created on first set operation."""
        config_path = temp_data_dir / "config.yaml"

        # Before any set, config might not exist or be empty
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0  # Should work even without file

        # Set a value
        runner.invoke(app, ["config", "set", "default_team", "test"])

        # Config file should exist now
        assert config_path.exists()


class TestConfigEdgeCases:
    """Edge cases for config operations."""

    def test_config_with_unicode(self, temp_data_dir):
        """Config handles unicode values."""
        result = runner.invoke(
            app, ["config", "set", "default_team", "équipe-française"]
        )

        assert result.exit_code == 0

        config = storage.load_config()
        assert config.default_team == "équipe-française"

    def test_config_long_value(self, temp_data_dir):
        """Config handles long values."""
        long_value = "x" * 1000
        result = runner.invoke(app, ["config", "set", "notion_workspace", long_value])

        assert result.exit_code == 0

        config = storage.load_config()
        assert config.notion_workspace == long_value

    def test_config_case_sensitive_key(self, temp_data_dir):
        """Config keys are case-sensitive."""
        result = runner.invoke(app, ["config", "set", "Default_Team", "value"])

        assert result.exit_code == 1
        assert "Unknown config key" in result.output

    def test_show_after_reload(self, temp_data_dir):
        """Config is correctly reloaded from file."""
        # Set values
        runner.invoke(app, ["config", "set", "default_team", "team1"])

        # Clear any in-memory cache by loading fresh
        config1 = storage.load_config()
        assert config1.default_team == "team1"

        # Update
        runner.invoke(app, ["config", "set", "default_team", "team2"])

        # Reload and verify
        config2 = storage.load_config()
        assert config2.default_team == "team2"
