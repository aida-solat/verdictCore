"""DAG executor — runs decision nodes in dependency order."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from verdictcore.dags.graph import DecisionGraph
from verdictcore.engine import Deciwa
from verdictcore.models.result import DecisionResult, DecisionStatus


class NodeResult(BaseModel):

    node_id: str
    node_name: str
    status: DecisionStatus
    selected_alternative_id: str | None = None
    blocked_upstream: bool = False
    result: DecisionResult | None = None


class DAGResult(BaseModel):

    graph_id: str
    node_results: list[NodeResult] = []
    final_status: DecisionStatus = DecisionStatus.DECIDED
    final_node_id: str | None = None
    metadata: dict[str, Any] = {}

    @property
    def final_result(self) -> NodeResult | None:
        if self.final_node_id:
            for nr in self.node_results:
                if nr.node_id == self.final_node_id:
                    return nr
        if self.node_results:
            return self.node_results[-1]
        return None


class DAGExecutor:

    def __init__(self, engine: Deciwa | None = None) -> None:
        self._engine = engine or Deciwa(enable_sensitivity=False)

    def execute(self, graph: DecisionGraph) -> DAGResult:
        order = graph.topological_order()
        results: dict[str, NodeResult] = {}
        node_results: list[NodeResult] = []

        for node_id in order:
            node = graph.get_node(node_id)
            if node is None:
                continue

            upstream_blocked = self._check_upstream_blocked(
                node.depends_on, results,
            )

            if upstream_blocked:
                nr = NodeResult(
                    node_id=node.id,
                    node_name=node.name,
                    status=DecisionStatus.BLOCKED,
                    blocked_upstream=True,
                )
                results[node.id] = nr
                node_results.append(nr)
                continue

            if node.decision_input is None:
                nr = NodeResult(
                    node_id=node.id,
                    node_name=node.name,
                    status=DecisionStatus.ERROR,
                )
                results[node.id] = nr
                node_results.append(nr)
                continue

            result = self._engine.run(node.decision_input)
            nr = NodeResult(
                node_id=node.id,
                node_name=node.name,
                status=result.status,
                selected_alternative_id=(
                    result.recommendation.selected_alternative_id
                ),
                result=result,
            )
            results[node.id] = nr
            node_results.append(nr)

        final_node_id = order[-1] if order else None
        final_status = self._determine_final_status(node_results)

        return DAGResult(
            graph_id=graph.graph_id,
            node_results=node_results,
            final_status=final_status,
            final_node_id=final_node_id,
        )

    @staticmethod
    def _check_upstream_blocked(
        depends_on: list[str],
        results: dict[str, NodeResult],
    ) -> bool:
        for dep in depends_on:
            dep_result = results.get(dep)
            if dep_result is None:
                return True
            if dep_result.status == DecisionStatus.BLOCKED:
                return True
            if dep_result.status == DecisionStatus.ERROR:
                return True
        return False

    @staticmethod
    def _determine_final_status(
        node_results: list[NodeResult],
    ) -> DecisionStatus:
        if not node_results:
            return DecisionStatus.ERROR
        statuses = {nr.status for nr in node_results}
        if DecisionStatus.ERROR in statuses:
            return DecisionStatus.ERROR
        if DecisionStatus.BLOCKED in statuses:
            return DecisionStatus.NEEDS_REVIEW
        if DecisionStatus.NEEDS_REVIEW in statuses:
            return DecisionStatus.NEEDS_REVIEW
        return DecisionStatus.DECIDED
