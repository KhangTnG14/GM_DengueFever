"""Community detection utilities for dengue district graph analysis.

This module supports two approaches:
1) Louvain community detection with tunable resolution and modularity score.
2) Spectral clustering on the graph adjacency matrix with silhouette score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from community import community_louvain
from sklearn.cluster import SpectralClustering
from sklearn.metrics import silhouette_score


@dataclass
class LouvainResult:
    """Container for a Louvain run."""

    resolution: float
    modularity_q: float
    labels: Dict[str, int]


@dataclass
class SpectralResult:
    """Container for a Spectral Clustering run."""

    n_clusters: int
    silhouette: float
    labels: Dict[str, int]


def load_graph_from_csv(
    nodes_path: str, edges_path: str, node_id_col: str = "district"
) -> nx.Graph:
    """Load an undirected weighted graph from nodes/edges CSV files.

    Expected edge columns:
    - source
    - target
    - weight (optional, defaults to 1.0 if missing)
    """
    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)

    if node_id_col not in nodes_df.columns:
        raise ValueError(f"Missing node id column '{node_id_col}' in nodes file.")
    for col in ("source", "target"):
        if col not in edges_df.columns:
            raise ValueError(f"Missing edge column '{col}' in edges file.")

    graph = nx.Graph()
    for _, row in nodes_df.iterrows():
        node_id = str(row[node_id_col])
        attrs = row.drop(labels=[node_id_col]).to_dict()
        graph.add_node(node_id, **attrs)

    has_weight = "weight" in edges_df.columns
    for _, row in edges_df.iterrows():
        source = str(row["source"])
        target = str(row["target"])
        weight = float(row["weight"]) if has_weight else 1.0
        graph.add_edge(source, target, weight=weight)

    if not nx.is_connected(graph):
        largest_cc = max(nx.connected_components(graph), key=len)
        graph = graph.subgraph(largest_cc).copy()

    return graph


def run_louvain_grid(
    graph: nx.Graph, resolutions: Iterable[float] = (0.5, 1.0, 1.5), seed: int = 42
) -> List[LouvainResult]:
    """Run Louvain for multiple resolutions and compute modularity Q."""
    results: List[LouvainResult] = []
    for resolution in resolutions:
        labels = community_louvain.best_partition(
            graph, resolution=resolution, random_state=seed, weight="weight"
        )
        q = community_louvain.modularity(labels, graph, weight="weight")
        results.append(
            LouvainResult(resolution=resolution, modularity_q=float(q), labels=labels)
        )
    return results


def run_spectral_grid(
    graph: nx.Graph, n_clusters_list: Iterable[int] = (3, 4, 5), seed: int = 42
) -> List[SpectralResult]:
    """Run Spectral Clustering for several k values and compute silhouette score."""
    nodes = sorted(graph.nodes())
    adjacency = nx.to_numpy_array(graph, nodelist=nodes, weight="weight")

    # Ensure numerical stability for sparse/isolated structures.
    adjacency = np.nan_to_num(adjacency, nan=0.0, posinf=0.0, neginf=0.0)

    results: List[SpectralResult] = []
    for n_clusters in n_clusters_list:
        model = SpectralClustering(
            n_clusters=n_clusters,
            affinity="precomputed",
            random_state=seed,
            assign_labels="kmeans",
        )
        labels_arr = model.fit_predict(adjacency)
        silhouette = silhouette_score(adjacency, labels_arr, metric="euclidean")
        labels = {node: int(label) for node, label in zip(nodes, labels_arr)}
        results.append(
            SpectralResult(
                n_clusters=int(n_clusters),
                silhouette=float(silhouette),
                labels=labels,
            )
        )
    return results


def pick_best_louvain(results: List[LouvainResult]) -> LouvainResult:
    """Pick Louvain result with maximum modularity."""
    return max(results, key=lambda r: r.modularity_q)


def pick_best_spectral(results: List[SpectralResult]) -> SpectralResult:
    """Pick Spectral result with maximum silhouette score."""
    return max(results, key=lambda r: r.silhouette)


def compare_partitions(
    louvain_labels: Dict[str, int], spectral_labels: Dict[str, int]
) -> pd.DataFrame:
    """Build district-level comparison table of Louvain vs Spectral labels."""
    common_nodes = sorted(set(louvain_labels).intersection(set(spectral_labels)))
    return pd.DataFrame(
        {
            "district": common_nodes,
            "louvain_community": [louvain_labels[n] for n in common_nodes],
            "spectral_cluster": [spectral_labels[n] for n in common_nodes],
        }
    )


def export_community_labels(
    out_path: str,
    comparison_df: pd.DataFrame,
    louvain_resolution: float,
    spectral_k: int,
) -> None:
    """Save final community label file for downstream reporting."""
    df = comparison_df.copy()
    df["louvain_resolution"] = louvain_resolution
    df["spectral_k"] = spectral_k
    df.to_csv(out_path, index=False)


def export_metric_summary(
    out_path: str,
    louvain_results: List[LouvainResult],
    spectral_results: List[SpectralResult],
) -> pd.DataFrame:
    """Create and save metric summary table for method comparison."""
    louvain_df = pd.DataFrame(
        [
            {"method": "louvain", "setting": r.resolution, "score": r.modularity_q}
            for r in louvain_results
        ]
    )
    spectral_df = pd.DataFrame(
        [
            {"method": "spectral", "setting": r.n_clusters, "score": r.silhouette}
            for r in spectral_results
        ]
    )
    summary = pd.concat([louvain_df, spectral_df], ignore_index=True)
    summary.to_csv(out_path, index=False)
    return summary
