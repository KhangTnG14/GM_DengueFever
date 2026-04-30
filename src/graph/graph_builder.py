import networkx as nx
import pandas as pd
import numpy as np


def build_graph(adj_matrix_path, traffic_path=None, alpha=0.5):
    """
    Xây dựng đồ thị NetworkX từ ma trận lân cận (adjacency matrix)
    và dữ liệu mật độ giao thông giữa các quận.

    Mỗi node đại diện cho một quận/huyện.
    Một edge được tạo khi hai quận có biên giới chung (adjacency = 1).

    Trọng số cạnh (edge weight) được tính theo công thức:
        weight = (alpha × 1.0) + ((1 - alpha) × traffic_index)

    Trong đó:
        - Thành phần 1.0 đại diện cho kết nối địa lý (có chung biên giới)
        - traffic_index đại diện cho cường độ di chuyển giữa hai quận
        - alpha ∈ [0, 1] điều chỉnh mức độ ưu tiên:
            + alpha → 1.0: ưu tiên địa lý
            + alpha → 0.0: ưu tiên giao thông
            + alpha = 0.5: cân bằng (khuyến nghị)

    Parameters
    ----------
    adj_matrix_path : str
        Đường dẫn tới file CSV ma trận lân cận (22×22).
        Giá trị = 1 nếu hai quận tiếp giáp, ngược lại = 0.

    traffic_path : str, optional (default=None)
        Đường dẫn tới file CSV ma trận giao thông (traffic index).
        Nếu None, trọng số cạnh chỉ dựa trên adjacency.

    alpha : float, optional (default=0.5)
        Hệ số kết hợp giữa adjacency và traffic_index.
        Phải nằm trong khoảng [0, 1].

    Returns
    -------
    G : networkx.Graph
        Đồ thị vô hướng với:
        - Nodes: tên quận
        - Edges: các cặp quận tiếp giáp
        - Edge attribute:
            + weight (float): trọng số cạnh

    Notes
    -----
    - Hàm tự động loại bỏ cạnh trùng (u, v) và (v, u).
    - Nếu traffic_index bị thiếu hoặc ≤ 0 → mặc định = 0.
    - Tên quận được strip() để tránh lỗi mismatch.

    Example
    -------
    >>> G = build_graph(
    ...     adj_matrix_path="data/processed/adjacency_matrix.csv",
    ...     traffic_path="data/raw/traffic_index.csv",
    ...     alpha=0.5
    ... )
    >>> G.number_of_nodes()
    22
    """

    # 1. Load adjacency matrix
    adj_df = pd.read_csv(adj_matrix_path, index_col=0, encoding="utf-8-sig")
    adj_df.index   = adj_df.index.str.strip()
    adj_df.columns = adj_df.columns.str.strip()

    # 2. Stack → edge list (nhanh hơn vòng for lồng nhau)
    adj_stacked = adj_df.stack()
    edges_df = adj_stacked[adj_stacked == 1].reset_index()
    edges_df.columns = ["source", "target", "adj"]

    # Bỏ cặp trùng (u,v) và (v,u)
    edges_df = edges_df[edges_df["source"] < edges_df["target"]].copy()

    # 3. Gắn traffic index
    traffic_df = None
    if traffic_path:
        traffic_df = pd.read_csv(traffic_path, index_col=0, encoding="utf-8-sig")
        traffic_df.index   = traffic_df.index.str.strip()
        traffic_df.columns = traffic_df.columns.str.strip()

    def compute_weight(row):
        u, v = row["source"], row["target"]

        # Lấy traffic value
        t_val = 0.0
        if traffic_df is not None:
            try:
                t_val = float(traffic_df.loc[u, v])
                if pd.isna(t_val) or t_val <= 0:
                    t_val = 0.0
            except KeyError:
                t_val = 0.0

        # Áp dụng đúng công thức từ ảnh
        # weight = (alpha × 1.0) + ((1 - alpha) × traffic_index)
        return (alpha * 1.0) + ((1 - alpha) * t_val)

    edges_df["weight"] = edges_df.apply(compute_weight, axis=1)

    # 4. Build graph
    G = nx.Graph()
    G.add_nodes_from(adj_df.index)

    # Dùng itertuples thay vì .values để giữ đúng kiểu string
    for row in edges_df.itertuples(index=False):
        G.add_edge(row.source, row.target, weight=row.weight)

    return G