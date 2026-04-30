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
    if G.number_of_nodes() == 0:
        raise ValueError("Đồ thị rỗng — không có node nào.")
    
    return nx.degree_centrality(G)


def compute_betweenness_centrality(G):
    """
    Betweenness centrality: tần suất xuất hiện trên shortest path giữa các cặp quận.
    Quận có betweenness cao = "cầu nối" quan trọng, nếu bùng dịch sẽ lan sang nhiều nơi.
    Dùng weighted shortest path (weight càng lớn = cạnh càng "ngắn/dễ đi").
    Chú ý: NetworkX betweenness dùng weight là DISTANCE, nên cần invert.
    """
    # Tạo graph với inverted weight để betweenness tính đúng

    if G.number_of_nodes() == 0:
        raise ValueError("Đồ thị rỗng — không có node nào.")
    if G.number_of_edges() == 0:
        return {node: 0.0 for node in G.nodes()}

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

    if G.number_of_nodes() == 0:
        raise ValueError("Đồ thị rỗng — không có node nào.")
    if G.number_of_edges() == 0:
        return {node: 0.0 for node in G.nodes()}

    G_inv = G.copy()
    for u, v, data in G_inv.edges(data=True):
        w = data.get("weight", 1.0)
        G_inv[u][v]["distance"] = 1.0 / w if w > 0 else 1.0

    return nx.closeness_centrality(G_inv, distance="distance")


def compute_pagerank(G, alpha=0.85):
    """
    Tính PageRank cho tất cả node trong đồ thị.

    Đánh giá tầm quan trọng của quận dựa trên tầm quan trọng
    của các quận láng giềng. Quận được nhiều quận "mạnh" kết nối
    → PageRank cao → nguy cơ nhận dịch từ nhiều nguồn đồng thời.

    Parameters
    ----------
    G     : nx.Graph
        Đồ thị NetworkX có trọng số.
    alpha : float, optional
        Damping factor (mặc định 0.85 — giá trị chuẩn).

    Returns
    -------
    dict
        {district_name: pagerank_score}

    Example
    -------
    >>> pr = compute_pagerank(G)
    >>> pr["Quận 10"]
    0.064
    """
    if G.number_of_nodes() == 0:
        raise ValueError("Đồ thị rỗng — không có node nào.")
    if not (0 < alpha < 1):
        raise ValueError(f"alpha phải trong khoảng (0, 1), nhận được: {alpha}")

    return nx.pagerank(G, alpha=alpha, weight="weight")


# TOP N

def get_top_districts(centrality_dict, n=5):
    """
    Lấy top N quận có centrality score cao nhất.

    Parameters
    ----------
    centrality_dict : dict
        Output từ các hàm compute_*_centrality.
    n : int
        Số quận muốn lấy (mặc định 5).

    Returns
    -------
    list of tuple
        [(district_name, score), ...] sắp xếp giảm dần.

    Example
    -------
    >>> top5 = get_top_districts(betweenness, n=5)
    >>> top5[0]
    ('Quận 1', 0.224)
    """
    if not centrality_dict:
        raise ValueError("centrality_dict rỗng.")
    if n <= 0:
        raise ValueError(f"n phải > 0, nhận được: {n}")
    return sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:n]


# =========================
# COMPUTE ALL & SAVE
# =========================

def compute_all_centrality(G):
    """
    Tính toàn bộ 4 centrality metrics trong một lần gọi.

    Parameters
    ----------
    G : nx.Graph
        Đồ thị NetworkX có trọng số.

    Returns
    -------
    dict
        {
            "degree":      {node: score},
            "betweenness": {node: score},
            "closeness":   {node: score},
            "pagerank":    {node: score},
        }
    """
    return {
        "degree":       compute_degree_centrality(G),
        "betweenness":  compute_betweenness_centrality(G),
        "closeness":    compute_closeness_centrality(G),
        "pagerank":     compute_pagerank(G),
    }


def build_centrality_df(G, centrality_dict):
    """
    Tạo DataFrame tổng hợp từ dict centrality.

    Parameters
    ----------
    G                : nx.Graph
        Đồ thị gốc (để lấy danh sách nodes).
    centrality_dict  : dict
        Output từ compute_all_centrality().

    Returns
    -------
    pd.DataFrame
        Columns: district, degree, betweenness, closeness, pagerank.
        Sắp xếp theo betweenness giảm dần.
    """
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
    """
    Lưu DataFrame centrality ra file CSV.

    Parameters
    ----------
    df          : pd.DataFrame
        Output từ build_centrality_df().
    output_path : str
        Đường dẫn file CSV đầu ra.

    Returns
    -------
    None
    """
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved: {output_path}")



# DEBUG
def print_graph_info(G: nx.Graph) -> None:
    """
    In thông tin tổng quan về đồ thị ra console.

    Parameters
    ----------
    G : nx.Graph
        Đồ thị cần kiểm tra.
    """
    if G.number_of_nodes() == 0:
        print("Đồ thị rỗng.")
        return

    degrees = dict(G.degree())
    weights = [d["weight"] for _, _, d in G.edges(data=True) if "weight" in d]

    print("===== GRAPH INFO =====")
    print(f"Nodes    : {G.number_of_nodes()}")
    print(f"Edges    : {G.number_of_edges()}")
    print(f"Connected: {nx.is_connected(G)}")
    print(f"Density  : {nx.density(G):.4f}")
    print(f"Degree   — max: {max(degrees.values())}, "
          f"min: {min(degrees.values())}, "
          f"avg: {np.mean(list(degrees.values())):.2f}")
    if weights:
        print(f"Weight   — max: {max(weights):.4f}, "
              f"min: {min(weights):.4f}, "
              f"avg: {np.mean(weights):.4f}")
    else:
        print("Weight   — không có trọng số trên cạnh")