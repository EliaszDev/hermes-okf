"""Graph extraction utilities.

Builds an implicit knowledge graph from markdown links, directory structure,
and tag clustering. No RDF, no Cypher — just portable conventions.
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from hermes_okf.bundle import OKFBundle


class GraphExtractor:
    """Extracts and navigates the implicit knowledge graph inside an OKF bundle."""

    def __init__(self, bundle: OKFBundle) -> None:
        self.bundle = bundle

    # ------------------------------------------------------------------
    # Link-based edges
    # ------------------------------------------------------------------
    def get_edges(self) -> list[dict[str, str]]:
        """Return all markdown links as directed edges."""
        return self.bundle.get_graph_edges()

    def get_neighbors(self, concept_id: str) -> list[str]:
        """Return target IDs of all outgoing edges from a concept."""
        return [e["target"] for e in self.get_edges() if e["source"] == concept_id]

    def get_backlinks(self, concept_id: str) -> list[str]:
        """Return source IDs of all incoming edges to a concept."""
        return [e["source"] for e in self.get_edges() if e["target"] == concept_id]

    # ------------------------------------------------------------------
    # Directory-based hierarchy
    # ------------------------------------------------------------------
    def get_children(self, concept_id: str) -> list[str]:
        """Return concept IDs that live inside the same directory."""
        file_path = self.bundle.root / Path(concept_id.replace("/", os.sep) + ".md")
        if not file_path.exists():
            return []
        parent_dir = file_path.parent
        children: list[str] = []
        for md_file in parent_dir.glob("*.md"):
            if md_file.name == "index.md" or md_file == file_path:
                continue
            rel_id = md_file.relative_to(self.bundle.root).with_suffix("").as_posix()
            children.append(rel_id)
        return sorted(children)

    # ------------------------------------------------------------------
    # Tag clustering
    # ------------------------------------------------------------------
    def get_tag_clusters(self) -> dict[str, list[str]]:
        """Return a mapping ``tag -> list[concept_id]``."""
        clusters: dict[str, list[str]] = defaultdict(list)
        for concept_id in self.bundle.list_concepts():
            concept = self.bundle.read_concept(concept_id)
            if concept:
                for tag in concept.tags:
                    clusters[tag].append(concept_id)
        return dict(clusters)

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------
    def traverse(
        self,
        start_id: str,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Breadth-first traversal of the link graph from a starting concept.

        Returns a nested dict representing the subgraph.
        """
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(start_id, 0)]
        result: dict[str, Any] = {"id": start_id, "depth": 0, "children": []}

        # Map depth -> list of node ids for reconstruction
        depth_map: dict[int, list[str]] = {0: [start_id]}
        edges_map: dict[str, list[str]] = defaultdict(list)

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth >= max_depth:
                continue
            visited.add(current_id)

            neighbors = self.get_neighbors(current_id)
            edges_map[current_id] = neighbors

            for n in neighbors:
                if n not in visited:
                    queue.append((n, depth + 1))
                    depth_map.setdefault(depth + 1, []).append(n)

        # Build nested tree structure (only for start node children)
        def build_subtree(node_id: str, current_depth: int) -> dict[str, Any] | None:
            if current_depth > max_depth:
                return None
            concept = self.bundle.read_concept(node_id)
            node: dict[str, Any] = {
                "id": node_id,
                "title": concept.title if concept else node_id,
                "type": concept.type if concept else "Unknown",
                "depth": current_depth,
            }
            children = []
            for child_id in edges_map.get(node_id, []):
                subtree = build_subtree(child_id, current_depth + 1)
                if subtree:
                    children.append(subtree)
            if children:
                node["children"] = children
            return node

        return build_subtree(start_id, 0) or result

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def to_networkx(self) -> Any:
        """Export the graph to a ``networkx.DiGraph`` (requires networkx)."""
        try:
            import networkx as nx
        except ImportError as exc:
            raise ImportError(
                "networkx is required for graph export. Install it: pip install networkx"
            ) from exc

        graph = nx.DiGraph()
        for concept_id in self.bundle.list_concepts():
            concept = self.bundle.read_concept(concept_id)
            if concept:
                graph.add_node(concept_id, **concept.metadata)

        for edge in self.get_edges():
            graph.add_edge(edge["source"], edge["target"], context=edge.get("context", ""))

        return graph
