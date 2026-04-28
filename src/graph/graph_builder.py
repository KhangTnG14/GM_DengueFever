# src/graph/graph_builder.py
# Phiên bản tạm thời do thành viên B tự viết
# Thành viên A sẽ mở rộng sau

import networkx as nx
import pandas as pd


def build_graph(adj_matrix_path, traffic_path):
    """
    Xây dựng đồ thị NetworkX từ adjacency matrix + traffic index.

    Parameters:
        adj_matrix_path : str — đường dẫn tới adjacency_matrix.csv
        traffic_path    : str — đường dẫn tới traffic_index.csv (optional)

    Returns:
        G : nx.Graph — đồ thị có trọng số
    """
    adj_df = pd.read_csv(adj_matrix_path, index_col=0, encoding="utf-8-sig")
    adj_df.index   = adj_df.index.str.strip()
    adj_df.columns = adj_df.columns.str.strip()

    G = nx.Graph()
    G.add_nodes_from(adj_df.index)

    traffic_df = None
    if traffic_path:
        traffic_df = pd.read_csv(traffic_path, index_col=0, encoding="utf-8-sig")
        traffic_df.index   = traffic_df.index.str.strip()
        traffic_df.columns = traffic_df.columns.str.strip()

    for i in adj_df.index:
        for j in adj_df.columns:
            if i >= j:
                continue
            if adj_df.loc[i, j] != 1:
                continue

            weight = 1.0
            if traffic_df is not None:
                if i in traffic_df.index and j in traffic_df.columns:
                    val = traffic_df.loc[i, j]
                    if pd.notna(val) and val > 0:
                        weight = float(val)

            G.add_edge(i, j, weight=weight)

    return G