# src/graph/graph_analysis.py

import networkx as nx
import pandas as pd
import numpy as np


# =========================
# CENTRALITY METRICS
# =========================

def compute_degree_centrality(G):
    """
    Degree centrality: tỉ lệ số cạnh kết nối / (n-1).
    Quận có degree cao = nhiều quận láng giềng trực tiếp.
    """
    return nx.degree_centrality(G)


def compute_betweenness_centrality(G):
    """
    Betweenness centrality: tần suất xuất hiện trên shortest path giữa các cặp quận.
    Quận có betweenness cao = "cầu nối" quan trọng, nếu bùng dịch sẽ lan sang nhiều nơi.
    Dùng weighted shortest path (weight càng lớn = cạnh càng "ngắn/dễ đi").
    Chú ý: NetworkX betweenness dùng weight là DISTANCE, nên cần invert.
    """
    # Tạo graph với inverted weight để betweenness tính đúng
    G_inv = G.copy()
    for u, v, data in G_inv.edges(data=True):
        w = data.get("weight", 1.0)
        G_inv[u][v]["distance"] = 1.0 / w if w > 0 else 1.0

    return nx.betweenness_centrality(G_inv, weight="distance", normalized=True)


def compute_closeness_centrality(G):
    """
    Closeness centrality: nghịch đảo trung bình khoảng cách đến tất cả quận khác.
    Quận có closeness cao = dịch lan nhanh ra toàn thành phố nếu bùng phát ở đây.
    Dùng inverted weight làm distance.
    """
    G_inv = G.copy()
    for u, v, data in G_inv.edges(data=True):
        w = data.get("weight", 1.0)
        G_inv[u][v]["distance"] = 1.0 / w if w > 0 else 1.0

    return nx.closeness_centrality(G_inv, distance="distance")


def compute_pagerank(G, alpha=0.85):
    """
    PageRank: tầm quan trọng của quận dựa trên tầm quan trọng của quận láng giềng.
    Quận được nhiều quận "mạnh" kết nối → PageRank cao.
    alpha=0.85 là giá trị chuẩn (damping factor).
    """
    return nx.pagerank(G, alpha=alpha, weight="weight")


# =========================
# TOP N
# =========================

def get_top_districts(centrality_dict, n=5):
    """Trả về top N quận có centrality cao nhất."""
    return sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:n]


# =========================
# COMPUTE ALL & SAVE
# =========================

def compute_all_centrality(G):
    """
    Tính toàn bộ 4 centrality metrics.
    Trả về dict để notebook có thể dùng linh hoạt.
    """
    return {
        "degree":       compute_degree_centrality(G),
        "betweenness":  compute_betweenness_centrality(G),
        "closeness":    compute_closeness_centrality(G),
        "pagerank":     compute_pagerank(G),
    }


def build_centrality_df(G, centrality_dict):
    """Tạo DataFrame từ dict centrality, sắp xếp theo betweenness."""
    nodes = list(G.nodes())
    df = pd.DataFrame({
        "district":    nodes,
        "degree":      [centrality_dict["degree"][n]      for n in nodes],
        "betweenness": [centrality_dict["betweenness"][n] for n in nodes],
        "closeness":   [centrality_dict["closeness"][n]   for n in nodes],
        "pagerank":    [centrality_dict["pagerank"][n]     for n in nodes],
    })
    return df.sort_values("betweenness", ascending=False).reset_index(drop=True)


def save_centrality(df, output_path):
    """Lưu CSV với encoding UTF-8 BOM để mở đúng tiếng Việt trên Excel."""
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved: {output_path}")


# =========================
# DEBUG
# =========================

def print_graph_info(G):
    print("===== GRAPH INFO =====")
    print(f"Nodes  : {G.number_of_nodes()}")
    print(f"Edges  : {G.number_of_edges()}")
    print(f"Connected: {nx.is_connected(G)}")
    degrees = dict(G.degree())
    print(f"Degree — max: {max(degrees.values())}, min: {min(degrees.values())}, "
          f"avg: {np.mean(list(degrees.values())):.2f}")
    weights = [d["weight"] for _, _, d in G.edges(data=True)]
    print(f"Weight — max: {max(weights):.3f}, min: {min(weights):.3f}, "
          f"avg: {np.mean(weights):.3f}")