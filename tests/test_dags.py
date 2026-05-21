"""Tests for Decision DAGs."""

import pytest

from verdictcore import Alternative, Criterion, DecisionInput
from verdictcore.dags import DAGExecutor, DecisionGraph
from verdictcore.dags.graph import DecisionNode


def _make_decision(decision_id: str, winner_score: int = 90) -> DecisionInput:
    return DecisionInput(
        decision_id=decision_id,
        question="Test?",
        domain="test",
        criteria=[
            Criterion(name="score", weight=1.0, direction="maximize"),
        ],
        alternatives=[
            Alternative(id="a", name="A", values={"score": winner_score}),
            Alternative(id="b", name="B", values={"score": 70}),
        ],
    )


class TestDecisionGraph:

    def test_topological_order_linear(self):
        graph = DecisionGraph(
            graph_id="g1",
            nodes=[
                DecisionNode(id="n1", name="Node 1"),
                DecisionNode(id="n2", name="Node 2", depends_on=["n1"]),
                DecisionNode(id="n3", name="Node 3", depends_on=["n2"]),
            ],
        )
        order = graph.topological_order()
        assert order == ["n1", "n2", "n3"]

    def test_topological_order_parallel(self):
        graph = DecisionGraph(
            graph_id="g2",
            nodes=[
                DecisionNode(id="n1", name="Node 1"),
                DecisionNode(id="n2", name="Node 2"),
                DecisionNode(
                    id="n3", name="Node 3", depends_on=["n1", "n2"],
                ),
            ],
        )
        order = graph.topological_order()
        assert order[-1] == "n3"
        assert set(order[:2]) == {"n1", "n2"}

    def test_cycle_detection(self):
        graph = DecisionGraph(
            graph_id="g3",
            nodes=[
                DecisionNode(id="n1", name="N1", depends_on=["n2"]),
                DecisionNode(id="n2", name="N2", depends_on=["n1"]),
            ],
        )
        with pytest.raises(ValueError, match="cycle"):
            graph.topological_order()

    def test_get_node(self):
        graph = DecisionGraph(
            graph_id="g4",
            nodes=[DecisionNode(id="n1", name="Node 1")],
        )
        assert graph.get_node("n1") is not None
        assert graph.get_node("nope") is None


class TestDAGExecutor:

    def test_linear_execution(self):
        graph = DecisionGraph(
            graph_id="g_exec_1",
            nodes=[
                DecisionNode(
                    id="step1", name="Step 1",
                    decision_input=_make_decision("d1"),
                ),
                DecisionNode(
                    id="step2", name="Step 2",
                    decision_input=_make_decision("d2"),
                    depends_on=["step1"],
                ),
            ],
        )
        executor = DAGExecutor()
        result = executor.execute(graph)

        assert result.graph_id == "g_exec_1"
        assert len(result.node_results) == 2
        assert result.final_status.value == "decided"

    def test_upstream_block_propagates(self):
        from verdictcore.models.constraint import Constraint

        blocked_decision = DecisionInput(
            decision_id="d_blocked",
            question="All blocked?",
            domain="test",
            criteria=[
                Criterion(name="score", weight=1.0, direction="maximize"),
            ],
            constraints=[
                Constraint(
                    field="score", operator=">=", value=100, action="block",
                ),
            ],
            alternatives=[
                Alternative(id="a", name="A", values={"score": 50}),
            ],
        )

        graph = DecisionGraph(
            graph_id="g_block",
            nodes=[
                DecisionNode(
                    id="screening", name="Screening",
                    decision_input=blocked_decision,
                ),
                DecisionNode(
                    id="final", name="Final",
                    decision_input=_make_decision("d_final"),
                    depends_on=["screening"],
                ),
            ],
        )
        executor = DAGExecutor()
        result = executor.execute(graph)

        final = result.node_results[1]
        assert final.blocked_upstream is True
        assert result.final_status.value == "needs_review"

    def test_no_input_produces_error(self):
        graph = DecisionGraph(
            graph_id="g_err",
            nodes=[
                DecisionNode(id="n1", name="No Input"),
            ],
        )
        executor = DAGExecutor()
        result = executor.execute(graph)
        assert result.node_results[0].status.value == "error"
