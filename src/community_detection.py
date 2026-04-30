"""Tiện ích phát hiện cộng đồng (Community detection) cho phân tích đồ thị số ca nhiễm dengue theo quận/huyện.

Module này hỗ trợ hai phương pháp tiếp cận:
1) Phát hiện cộng đồng Louvain (Louvain community detection) với khả năng điều chỉnh resolution và modularity score.
2) Phân cụm phổ (Spectral clustering) trên ma trận kề (adjacency matrix) của đồ thị với silhouette score.
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
    """Lớp lưu trữ kết quả của một lượt chạy thuật toán Louvain."""

    resolution: float
    modularity_q: float
    labels: Dict[str, int]


@dataclass
class SpectralResult:
    """Lớp lưu trữ kết quả của một lượt chạy thuật toán Spectral Clustering."""

    n_clusters: int
    silhouette: float
    labels: Dict[str, int]


def load_graph_from_csv(
    nodes_path: str, edges_path: str, node_id_col: str = "district"
) -> nx.Graph:
    """
    Tải một đồ thị vô hướng có trọng số (undirected weighted graph) từ các tệp CSV chứa nodes và edges.

    Các cột dự kiến trong tệp cạnh (edge):
    - source: Nguồn
    - target: Đích
    - weight: Trọng số (tùy chọn, mặc định là 1.0 nếu thiếu)
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
    """Chạy thuật toán Louvain với nhiều giá trị resolution khác nhau và tính modularity Q."""
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
    """Chạy Spectral Clustering cho một danh sách các giá trị k (n_clusters) và tính silhouette score."""
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
    """Chọn kết quả Louvain có modularity cao nhất."""
    return max(results, key=lambda r: r.modularity_q)


def pick_best_spectral(results: List[SpectralResult]) -> SpectralResult:
    """Chọn kết quả Spectral Clustering có silhouette score cao nhất."""
    return max(results, key=lambda r: r.silhouette)


def compare_partitions(
    louvain_labels: Dict[str, int], spectral_labels: Dict[str, int]
) -> pd.DataFrame:
    """Xây dựng bảng so sánh cấp độ quận/huyện giữa nhãn của Louvain và Spectral."""
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
    """Lưu tệp nhãn cộng đồng cuối cùng để phục vụ cho các báo cáo sau này."""
    df = comparison_df.copy()
    df["louvain_resolution"] = louvain_resolution
    df["spectral_k"] = spectral_k
    df.to_csv(out_path, index=False)


def export_metric_summary(
    out_path: str,
    louvain_results: List[LouvainResult],
    spectral_results: List[SpectralResult],
) -> pd.DataFrame:
    """Tạo và lưu bảng tóm tắt các chỉ số (metrics) để so sánh các phương pháp."""
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
