"""Integration tests for 'pa entity update' command."""

import pytest
from typer.testing import CliRunner

from personal_assistant import storage
from personal_assistant.cli import app
from personal_assistant.schemas import Person, Team

runner = CliRunner()


@pytest.fixture
def person_with_tags(temp_data_dir):
    """Person with existing tags."""
    person = Person(
        id="tagged",
        name="Tagged Person",
        tags=["python", "testing", "senior"],
    )
    storage.add_person(person)
    return person


@pytest.fixture
def second_team(temp_data_dir, sample_team):
    """Second team for update tests."""
    team = Team(id="design", name="Design Team", team_type="creative")
    storage.add_team(team)
    return team


class TestUpdatePerson:
    """Tests for updating person entities."""

    def test_update_person_name(self, sample_person):
        """Update person name."""
        result = runner.invoke(
            app, ["entity", "update", "john-doe", "--name", "John Smith"]
        )

        assert result.exit_code == 0
        assert "Updated person:" in result.output

        person = storage.get_person("john-doe")
        assert person.name == "John Smith"

    def test_update_person_role(self, sample_person):
        """Update person role."""
        result = runner.invoke(
            app, ["entity", "update", "john-doe", "--role", "Senior Engineer"]
        )

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person.role == "Senior Engineer"

    def test_update_person_team(self, sample_person, sample_team):
        """Update person team assignment."""
        result = runner.invoke(
            app, ["entity", "update", "john-doe", "--team", "engineering"]
        )

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person.team_id == "engineering"

    def test_update_person_notion(self, sample_person):
        """Update person Notion page."""
        result = runner.invoke(
            app, ["entity", "update", "john-doe", "--notion", "https://new.notion.so/page"]
        )

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person.notion_page == "https://new.notion.so/page"

    def test_update_person_invalid_team(self, sample_person):
        """Error when updating person with non-existent team."""
        result = runner.invoke(
            app, ["entity", "update", "john-doe", "--team", "nonexistent"]
        )

        assert result.exit_code == 1
        assert "Team 'nonexistent' does not exist" in result.output

    def test_update_person_not_found(self, temp_data_dir):
        """Error when updating non-existent person."""
        result = runner.invoke(
            app, ["entity", "update", "ghost", "--name", "New Name"]
        )

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_update_no_changes(self, sample_person):
        """Warning when no update options provided."""
        result = runner.invoke(app, ["entity", "update", "john-doe"])

        assert result.exit_code == 0
        assert "No updates specified" in result.output

    def test_update_person_multiple_fields(self, sample_person, sample_team):
        """Update multiple fields at once."""
        result = runner.invoke(
            app,
            [
                "entity",
                "update",
                "john-doe",
                "--name",
                "John Updated",
                "--role",
                "Tech Lead",
                "--team",
                "engineering",
            ],
        )

        assert result.exit_code == 0
        person = storage.get_person("john-doe")
        assert person.name == "John Updated"
        assert person.role == "Tech Lead"
        assert person.team_id == "engineering"

    def test_update_person_change_team(self, sample_team, second_team):
        """Change person from one team to another."""
        person = Person(id="mover", name="Team Mover", team_id="engineering")
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "mover", "--team", "design"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("mover")
        assert updated.team_id == "design"


class TestUpdateTeam:
    """Tests for updating team entities."""

    def test_update_team_name(self, sample_team):
        """Update team name."""
        result = runner.invoke(
            app, ["entity", "update", "engineering", "--name", "Engineering Squad"]
        )

        assert result.exit_code == 0
        assert "Updated team:" in result.output

        team = storage.get_team("engineering")
        assert team.name == "Engineering Squad"

    def test_update_team_type(self, sample_team):
        """Update team type."""
        result = runner.invoke(
            app, ["entity", "update", "engineering", "--type", "platform"]
        )

        assert result.exit_code == 0
        team = storage.get_team("engineering")
        assert team.team_type == "platform"

    def test_update_team_not_found(self, temp_data_dir):
        """Error when updating non-existent team."""
        result = runner.invoke(
            app, ["entity", "update", "ghost", "--name", "New Name"]
        )

        assert result.exit_code == 1
        assert "Entity 'ghost' not found" in result.output

    def test_update_team_notion(self, sample_team):
        """Update team Notion page."""
        result = runner.invoke(
            app, ["entity", "update", "engineering", "--notion", "https://notion.so/team"]
        )

        assert result.exit_code == 0
        team = storage.get_team("engineering")
        assert team.notion_page == "https://notion.so/team"


class TestUpdateTags:
    """Tests for tag operations on person entities."""

    def test_replace_all_tags(self, person_with_tags):
        """Replace all tags with new set."""
        result = runner.invoke(
            app, ["entity", "update", "tagged", "--tags", "golang,rust"]
        )

        assert result.exit_code == 0
        person = storage.get_person("tagged")
        assert person.tags == ["golang", "rust"]

    def test_add_tag_new(self, person_with_tags):
        """Add a new tag."""
        result = runner.invoke(
            app, ["entity", "update", "tagged", "--add-tag", "leadership"]
        )

        assert result.exit_code == 0
        person = storage.get_person("tagged")
        assert "leadership" in person.tags
        # Original tags still present
        assert "python" in person.tags

    def test_add_tag_duplicate(self, person_with_tags):
        """Adding existing tag is idempotent."""
        result = runner.invoke(
            app, ["entity", "update", "tagged", "--add-tag", "python"]
        )

        assert result.exit_code == 0
        person = storage.get_person("tagged")
        # Should not have duplicate
        assert person.tags.count("python") == 1

    def test_remove_tag_exists(self, person_with_tags):
        """Remove an existing tag."""
        result = runner.invoke(
            app, ["entity", "update", "tagged", "--remove-tag", "testing"]
        )

        assert result.exit_code == 0
        person = storage.get_person("tagged")
        assert "testing" not in person.tags
        # Other tags still present
        assert "python" in person.tags
        assert "senior" in person.tags

    def test_remove_tag_not_exists(self, person_with_tags):
        """Removing non-existent tag is idempotent."""
        result = runner.invoke(
            app, ["entity", "update", "tagged", "--remove-tag", "ghost"]
        )

        assert result.exit_code == 0
        person = storage.get_person("tagged")
        # Original tags unchanged
        assert person.tags == ["python", "testing", "senior"]

    def test_add_tag_to_empty(self, sample_person):
        """Add tag to person with empty tags list."""
        # sample_person has tags from conftest
        person = Person(id="no-tags", name="No Tags Person")
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "no-tags", "--add-tag", "new-tag"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("no-tags")
        assert updated.tags == ["new-tag"]

    def test_remove_last_tag(self, temp_data_dir):
        """Remove the only tag leaves empty list."""
        person = Person(id="one-tag", name="One Tag Person", tags=["only-tag"])
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "one-tag", "--remove-tag", "only-tag"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("one-tag")
        assert updated.tags == []


class TestUpdatePreservesData:
    """Tests that updates preserve unrelated data."""

    def test_update_preserves_team_relationship(self, sample_team):
        """Update name preserves team relationship."""
        person = Person(id="team-member", name="Team Member", team_id="engineering")
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "team-member", "--role", "Lead"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("team-member")
        assert updated.team_id == "engineering"  # Preserved
        assert updated.role == "Lead"

    def test_update_preserves_tags(self, temp_data_dir):
        """Update name preserves tags."""
        person = Person(id="tagged", name="Tagged", tags=["a", "b", "c"])
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "tagged", "--name", "Updated Tagged"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("tagged")
        assert updated.tags == ["a", "b", "c"]

    def test_update_preserves_calendar_patterns(self, temp_data_dir):
        """Update preserves calendar patterns."""
        person = Person(
            id="patterned",
            name="Patterned",
            calendar_patterns=["1:1 Patterned", "Sync"],
        )
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "patterned", "--role", "Manager"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("patterned")
        assert updated.calendar_patterns == ["1:1 Patterned", "Sync"]

    def test_update_preserves_notion_page(self, temp_data_dir):
        """Update name preserves Notion page."""
        person = Person(
            id="notion-user",
            name="Notion User",
            notion_page="https://notion.so/original",
        )
        storage.add_person(person)

        result = runner.invoke(
            app, ["entity", "update", "notion-user", "--role", "Developer"]
        )

        assert result.exit_code == 0
        updated = storage.get_person("notion-user")
        assert updated.notion_page == "https://notion.so/original"
