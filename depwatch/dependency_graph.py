"""Build and query a simple dependency graph across all monitored projects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class GraphNode:
    package: str
    language: str
    projects: Set[str] = field(default_factory=set)
    current_version: str = ""
    latest_version: str = ""

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "language": self.language,
            "projects": sorted(self.projects),
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "shared": len(self.projects) > 1,
        }


@dataclass
class DependencyGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.nodes) == 0

    def shared_packages(self) -> List[GraphNode]:
        """Return nodes used by more than one project."""
        return [n for n in self.nodes.values() if len(n.projects) > 1]

    def packages_for_project(self, project_name: str) -> List[GraphNode]:
        return [n for n in self.nodes.values() if project_name in n.projects]

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "total_packages": len(self.nodes),
            "shared_packages": len(self.shared_packages()),
        }


def _node_key(package: str, language: str) -> str:
    return f"{language}:{package.lower()}"


def build_graph(digests: List[ProjectDigest]) -> DependencyGraph:
    """Build a DependencyGraph from a list of ProjectDigest objects."""
    graph = DependencyGraph()
    for digest in digests:
        for update in digest.updates:
            key = _node_key(update.package, update.language)
            if key not in graph.nodes:
                graph.nodes[key] = GraphNode(
                    package=update.package,
                    language=update.language,
                    current_version=update.current_version,
                    latest_version=update.latest_version,
                )
            node = graph.nodes[key]
            node.projects.add(digest.project_name)
            # Keep the newest latest_version seen
            node.latest_version = update.latest_version
    return graph
