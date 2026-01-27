"""Pydantic schemas for entities, mappings, and memory."""

import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Person(BaseModel):
    """A person entity."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Unique identifier (lowercase, alphanumeric, hyphens)")
    name: str = Field(..., min_length=1, description="Full name")
    role: str | None = Field(default=None, description="Job title or role")
    team_id: str | None = Field(default=None, description="Reference to team ID")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    calendar_patterns: list[str] = Field(default_factory=list, description="Patterns to match in calendar events")
    notion_page: str | None = Field(default=None, description="Notion page URL or ID")


class Team(BaseModel):
    """A team or group entity."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Unique identifier (lowercase, alphanumeric, hyphens)")
    name: str = Field(..., min_length=1, description="Team name")
    team_type: str | None = Field(default=None, description="Team type (e.g., engineering, product)")
    calendar_patterns: list[str] = Field(default_factory=list, description="Patterns to match in calendar events")
    notion_page: str | None = Field(default=None, description="Notion page URL or ID")


class CalendarNotionMapping(BaseModel):
    """A mapping between calendar events and Notion pages."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Unique identifier")
    calendar_pattern: str = Field(..., min_length=1, description="Pattern to match in calendar events")
    entity_id: str = Field(..., description="Reference to person or team ID")
    entity_type: Literal["person", "team"] = Field(..., description="Type of entity")
    notion_page: str | None = Field(default=None, description="Notion page URL or ID")


class MemoryEntry(BaseModel):
    """Metadata for a memory entry (the content is in markdown files)."""

    entity_id: str = Field(..., description="Reference to person or team ID")
    entity_type: Literal["person", "team"] = Field(..., description="Type of entity")
    entry_date: datetime.date = Field(..., description="Date of the entry")
    entry_type: Literal["observation", "note", "inference"] = Field(default="observation", description="Type of memory")
    source: Literal["user", "inferred"] = Field(default="user", description="Source of the memory")
    context: str | None = Field(default=None, description="Context for the observation (e.g., meeting reference)")


class Config(BaseModel):
    """Global configuration."""

    default_team: str | None = Field(default=None, description="Default team for new people")
    notion_workspace: str | None = Field(default=None, description="Default Notion workspace")
