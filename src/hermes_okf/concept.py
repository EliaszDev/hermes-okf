"""Concept dataclass — the atomic unit of knowledge in an OKF bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Concept:
    """A single concept in an OKF bundle.

    Corresponds to one ``.md`` file with YAML frontmatter + markdown body.

    Attributes:
        id: Relative path without ``.md`` (e.g. ``projects/fifa_pipeline``).
        type: OKF ``type`` field (e.g. ``Project``, ``Decision``, ``Metric``).
        title: Human-readable title.
        description: Short summary (optional).
        tags: List of tags for clustering/filtering.
        resource: External URL reference (optional).
        timestamp: ISO 8601 UTC timestamp string (optional).
        body: Markdown body content.
        metadata: Raw frontmatter dictionary for extensibility.
    """

    id: str
    type: str = "Unknown"
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    resource: str | None = None
    timestamp: str | None = None
    body: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
