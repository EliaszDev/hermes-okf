"""Core OKF bundle manager.

Provides read/write operations for an OKF-compliant knowledge bundle,
including concept management, logging, and graph traversal.
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from hermes_okf.concept import Concept


class OKFBundle:
    """Manages an OKF-compliant knowledge bundle on the local filesystem.

    An OKF bundle is a directory tree of ``.md`` files with YAML frontmatter,
    where each file represents a "concept" in the knowledge graph. The bundle
    includes reserved files ``index.md`` and ``log.md`` for directory listings
    and chronological agent history.

    Args:
        root_path: Path to the bundle root directory. Created if it does not exist.
    """

    def __init__(self, root_path: str | Path) -> None:
        self.root = Path(root_path).expanduser().resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True)
        if not (self.root / "index.md").exists():
            self._init_bundle()

    def _init_bundle(self) -> None:
        """Create minimal conformant OKF structure."""
        self._write_file(
            "index.md",
            "---\nokf_version: \"0.1\"\n---\n\n# Knowledge Index\n\n"
            "* [Projects](projects/)\n"
            "* [Decisions](decisions/)\n"
            "* [Context](context/)\n",
        )
        self._write_file("log.md", "# Agent Log\n\n")

        # Seed subdirectories with index stubs
        for subdir in ("projects", "decisions", "context"):
            (self.root / subdir).mkdir(exist_ok=True)
            self._write_file(
                f"{subdir}/index.md",
                f"---\ntype: Directory\ntitle: {subdir.title()}\n---\n\n# {subdir.title()}\n\n",
            )

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    def _write_file(self, rel_path: str, content: str) -> None:
        file_path = self.root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def _parse_concept(self, content: str, concept_id: str) -> Concept:
        """Parse YAML frontmatter + markdown body into a ``Concept``."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                _, frontmatter, body = parts
                metadata = yaml.safe_load(frontmatter) or {}
            else:
                metadata = {}
                body = content
        else:
            metadata = {}
            body = content

        return Concept(
            id=concept_id,
            type=metadata.get("type", "Unknown"),
            title=metadata.get("title", concept_id),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []) or [],
            resource=metadata.get("resource"),
            timestamp=metadata.get("timestamp"),
            body=body.strip(),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def read_concept(self, concept_id: str) -> Concept | None:
        """Read a concept by its ID (relative path without ``.md``)."""
        # Normalize concept_id to use OS path separators
        file_path = self.root / Path(concept_id.replace("/", os.sep) + ".md")
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding="utf-8")
        return self._parse_concept(content, concept_id)

    def write_concept(
        self,
        concept_id: str,
        body: str,
        **frontmatter: Any,
    ) -> Concept:
        """Write or overwrite a concept. Auto-adds timestamp if missing.

        Args:
            concept_id: Relative path without ``.md`` (e.g. ``projects/my_project``).
            body: Markdown body content.
            **frontmatter: Arbitrary YAML frontmatter fields. ``type`` is required
                by OKF spec but not enforced here (use ``OKFValidator`` for that).

        Returns:
            The written ``Concept``.
        """
        file_path = self.root / Path(concept_id.replace("/", os.sep) + ".md")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if "timestamp" not in frontmatter:
            frontmatter["timestamp"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        yaml_block = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        content = f"---\n{yaml_block}---\n\n{body.strip()}\n"
        file_path.write_text(content, encoding="utf-8")

        return self._parse_concept(content, concept_id)

    def delete_concept(self, concept_id: str) -> bool:
        """Delete a concept. Returns ``True`` if it existed."""
        file_path = self.root / Path(concept_id.replace("/", os.sep) + ".md")
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_concepts(self, subdir: str | None = None) -> list[str]:
        """Return all concept IDs in the bundle, optionally filtered by subdirectory."""
        search_root = self.root / subdir if subdir else self.root
        results: list[str] = []
        for md_file in search_root.rglob("*.md"):
            if md_file.name in ("index.md", "log.md"):
                continue
            rel_id = md_file.relative_to(self.root).with_suffix("").as_posix()
            results.append(rel_id)
        return sorted(results)

    def append_log(self, entry: str, category: str = "Update") -> None:
        """Append an entry to ``log.md`` with today's date."""
        log_path = self.root / "log.md"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        line = f"* **{category}**: {entry}\n"

        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
        else:
            content = "# Agent Log\n\n"

        if f"## {today}" not in content:
            content += f"\n## {today}\n"

        content += line
        log_path.write_text(content, encoding="utf-8")

    def read_log(self) -> str:
        """Return the full contents of ``log.md``."""
        log_path = self.root / "log.md"
        if not log_path.exists():
            return ""
        return log_path.read_text(encoding="utf-8")

    def search_by_tag(self, tag: str) -> list[Concept]:
        """Find all concepts that contain a given tag."""
        results: list[Concept] = []
        for concept_id in self.list_concepts():
            concept = self.read_concept(concept_id)
            if concept and tag in concept.tags:
                results.append(concept)
        return results

    def get_graph_edges(self) -> list[dict[str, str]]:
        """Extract all markdown links as directed edges."""
        edges: list[dict[str, str]] = []
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for md_file in self.root.rglob("*.md"):
            if md_file.name in ("index.md", "log.md"):
                continue
            content = md_file.read_text(encoding="utf-8")
            source = md_file.relative_to(self.root).with_suffix("").as_posix()

            for match in link_pattern.finditer(content):
                target = match.group(2)
                # Normalise relative links to concept IDs
                if target.endswith(".md"):
                    target = target.replace(".md", "")
                if not target.startswith("http"):
                    edges.append(
                        {
                            "source": source,
                            "target": target,
                            "context": match.group(1),
                        }
                    )
        return edges

    def get_neighbors(self, concept_id: str) -> list[dict[str, str]]:
        """Return all outgoing edges from a given concept."""
        return [e for e in self.get_graph_edges() if e["source"] == concept_id]

    def to_dict(self, concept_id: str) -> dict[str, Any] | None:
        """Return a plain dict representation of a concept (useful for JSON)."""
        concept = self.read_concept(concept_id)
        if concept is None:
            return None
        return asdict(concept)
