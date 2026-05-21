"""Decision graph model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from verdictcore.models.decision import DecisionInput


class DecisionNode(BaseModel):

    id: str
    name: str
    decision_input: DecisionInput | None = None
    decision_file: str | None = None
    depends_on: list[str] = []
    output_mapping: dict[str, Any] = {}


class DecisionEdge(BaseModel):

    from_node: str
    to_node: str


class DecisionGraph(BaseModel):

    graph_id: str
    nodes: list[DecisionNode]
    edges: list[DecisionEdge] = []
    metadata: dict[str, Any] = {}

    def topological_order(self) -> list[str]:
        adj: dict[str, list[str]] = {n.id: [] for n in self.nodes}
        in_degree: dict[str, int] = {n.id: 0 for n in self.nodes}

        for node in self.nodes:
            for dep in node.depends_on:
                adj[dep].append(node.id)
                in_degree[node.id] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            raise ValueError("Decision graph contains a cycle.")

        return order

    def get_node(self, node_id: str) -> DecisionNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None
