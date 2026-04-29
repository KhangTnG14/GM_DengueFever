import networkx as nx
import pandas as pd
import numpy as np


def build_graph(adj_matrix_path, traffic_path=None, alpha=0.5):
    """
    Xây dựng đồ thị NetworkX từ ma trận lân cận và giao thông.

    Công thức: weight = (alpha × 1.0) + ((1 - alpha) × traffic_index)
    
    alpha = 0.9 → coi trọng địa lý (Thủ Đức rìa đô thị → betweenness thấp)
    alpha = 0.5 → cân bằng cả hai    (mặc định khuyến nghị)
    alpha = 0.1 → coi trọng giao thông (Thủ Đức là hub → betweenness cao)
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