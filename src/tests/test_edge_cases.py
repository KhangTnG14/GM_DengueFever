# src/tests/test_edge_cases.py
"""
Test edge cases cho toàn bộ module trong src/.
Chạy: python -m pytest src/tests/ -v
"""

import sys, os
# sys.path.append(os.path.abspath("../../"))
sys.path.append(os.path.abspath("."))

import networkx as nx
import pandas as pd
import numpy as np
import pytest

from src.graph.graph_analysis import (
    compute_degree_centrality,
    compute_betweenness_centrality,
    compute_closeness_centrality,
    compute_pagerank,
    get_top_districts,
    build_centrality_df,
    compute_all_centrality,
)
from src.epidemic_model import sir_simulation, apply_intervention


# =============================================================
# FIXTURES — đồ thị dùng chung cho nhiều test
@pytest.fixture
def simple_graph():
    """Đồ thị đơn giản 5 node đầy đủ kết nối."""
    G = nx.Graph()
    edges = [("A", "B", 0.8), ("B", "C", 0.5),
             ("C", "D", 0.6), ("D", "E", 0.3), ("A", "C", 0.4)]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G


@pytest.fixture
def graph_with_isolated():
    """Đồ thị có 1 node bị cô lập (không có cạnh)."""
    G = nx.Graph()
    G.add_nodes_from(["A", "B", "C", "Isolated"])
    G.add_edge("A", "B", weight=0.5)
    G.add_edge("B", "C", weight=0.3)
    return G


@pytest.fixture
def empty_graph():
    """Đồ thị hoàn toàn rỗng."""
    return nx.Graph()

# =============================================================
# TEST: Centrality với đồ thị bình thường
def test_degree_centrality_normal(simple_graph):
    dc = compute_degree_centrality(simple_graph)
    assert len(dc) == 5
    assert all(0 <= v <= 1 for v in dc.values()), "Degree phải trong [0, 1]"


def test_betweenness_sum_normal(simple_graph):
    bc = compute_betweenness_centrality(simple_graph)
    assert len(bc) == 5
    assert all(v >= 0 for v in bc.values()), "Betweenness phải >= 0"


def test_pagerank_sum_to_one(simple_graph):
    pr = compute_pagerank(simple_graph)
    total = sum(pr.values())
    assert abs(total - 1.0) < 1e-6, f"PageRank tổng phải = 1, nhận được {total}"


# =============================================================
# TEST: Edge case — node bị cô lập (không có ca bệnh)
def test_isolated_node_betweenness(graph_with_isolated):
    """Node cô lập phải có betweenness = 0, không được crash."""
    bc = compute_betweenness_centrality(graph_with_isolated)
    assert bc["Isolated"] == 0.0, "Node cô lập phải có betweenness = 0"
    print(f"Node cô lập: betweenness = {bc['Isolated']}")


def test_isolated_node_closeness(graph_with_isolated):
    """Node cô lập: closeness = 0 (không reach được ai)."""
    cc = compute_closeness_centrality(graph_with_isolated)
    assert cc["Isolated"] == 0.0, "Node cô lập phải có closeness = 0"


def test_isolated_node_pagerank(graph_with_isolated):
    """PageRank vẫn chạy được khi có node cô lập."""
    pr = compute_pagerank(graph_with_isolated)
    assert "Isolated" in pr
    assert pr["Isolated"] >= 0


# =============================================================
# TEST: Edge case — đồ thị rỗng
def test_empty_graph_raises(empty_graph):
    """Đồ thị rỗng phải raise ValueError rõ ràng."""
    with pytest.raises(ValueError, match="rỗng"):
        compute_degree_centrality(empty_graph)


# =============================================================
# TEST: Edge case — quận không có ca bệnh trong SIR
def test_sir_district_no_cases(simple_graph):
    """
    SIR vẫn chạy được khi seed_node là quận
    không có ca bệnh thực tế (weight thấp).
    """
    history, curve = sir_simulation(
        simple_graph, beta=0.3, gamma=0.1,
        seed_node="A", steps=10
    )
    assert len(history) == 11       # step 0 + 10 steps
    assert len(curve) == 10
    assert set(curve.columns) == {"step", "S", "I", "R"}
    assert all(abs(row.S + row.I + row.R - 1.0) < 1e-6
               for _, row in curve.iterrows()), "S+I+R phải = 1 mọi bước"


def test_sir_invalid_seed(simple_graph):
    """Seed node không tồn tại phải raise lỗi rõ ràng."""
    with pytest.raises(KeyError):
        sir_simulation(simple_graph, beta=0.3, gamma=0.1,
                      seed_node="KHÔNG_TỒN_TẠI", steps=5)

# =============================================================
# TEST: apply_intervention
def test_intervention_reduces_weight(simple_graph):
    original_weight = simple_graph["A"]["B"]["weight"]
    G_new = apply_intervention(simple_graph, ["A"], reduction=0.5)
    new_weight = G_new["A"]["B"]["weight"]
    assert abs(new_weight - original_weight * 0.5) < 1e-9
    # Đồ thị gốc không bị thay đổi
    assert simple_graph["A"]["B"]["weight"] == original_weight


def test_intervention_invalid_reduction(simple_graph):
    with pytest.raises(ValueError):
        apply_intervention(simple_graph, ["A"], reduction=1.5)


def test_intervention_missing_node(simple_graph):
    """Node không tồn tại → warning, không crash."""
    G_new = apply_intervention(simple_graph, ["KHÔNG_TỒN_TẠI"], reduction=0.5)
    assert G_new is not None

# =============================================================
# TEST: get_top_districts
def test_get_top_districts_normal(simple_graph):
    bc = compute_betweenness_centrality(simple_graph)
    top3 = get_top_districts(bc, n=3)
    assert len(top3) == 3
    scores = [s for _, s in top3]
    assert scores == sorted(scores, reverse=True), "Phải sắp xếp giảm dần"


def test_get_top_districts_empty():
    with pytest.raises(ValueError):
        get_top_districts({}, n=3)


if __name__ == "__main__":
    # Chạy thủ công không cần pytest
    import traceback
    tests = [
        test_degree_centrality_normal,
        test_betweenness_sum_normal,
        test_pagerank_sum_to_one,
        test_isolated_node_betweenness,
        test_isolated_node_closeness,
        test_isolated_node_pagerank,
        test_sir_district_no_cases,
        test_intervention_reduces_weight,
        test_get_top_districts_normal,
    ]

    G_simple   = nx.Graph()
    for u, v, w in [("A","B",0.8),("B","C",0.5),
                    ("C","D",0.6),("D","E",0.3),("A","C",0.4)]:
        G_simple.add_edge(u, v, weight=w)

    G_isolated = nx.Graph()
    G_isolated.add_nodes_from(["A","B","C","Isolated"])
    G_isolated.add_edge("A","B",weight=0.5)
    G_isolated.add_edge("B","C",weight=0.3)

    passed = 0
    for test_fn in tests:
        try:
            sig = test_fn.__code__.co_varnames[:test_fn.__code__.co_argcount]
            if "simple_graph" in sig:
                test_fn(G_simple)
            elif "graph_with_isolated" in sig:
                test_fn(G_isolated)
            else:
                test_fn()
            print(f"PASS: {test_fn.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL: {test_fn.__name__}")
            traceback.print_exc()

    print(f"\n{passed}/{len(tests)} tests passed")