import geopandas as gpd
import pandas as pd
import numpy as np
import os


def build_traffic():
    """
    Xây dựng ma trận chỉ số lưu lượng giao thông (traffic index) chuẩn hóa từ khoảng cách giữa các tâm điểm quận/huyện.

    Hàm này thực hiện đọc tệp `data/raw/hcmc_districts.geojson`, tính toán giá trị lưu lượng 
    dựa trên nghịch đảo khoảng cách giữa các tâm điểm (centroid-based inverse-distance) cho 
    tất cả các cặp quận/huyện, sau đó chuẩn hóa chúng về khoảng [0, 1]. Hàm cũng có tùy chọn 
    che (mask) các cặp không kề nhau bằng cách sử dụng `data/processed/adjacency_matrix.csv`. 
    Kết quả được lưu tại `data/raw/traffic_index.csv`.

    Returns
    -------
    pandas.DataFrame
        Ma trận chỉ số lưu lượng giao thông đã chuẩn hóa cho các quận/huyện.

    Notes
    -----
    Nếu thiếu tệp `data/processed/adjacency_matrix.csv`, hàm vẫn sẽ tính toán ma trận 
    lưu lượng đầy đủ và lưu lại mà không thực hiện che (masking) theo quan hệ kề.

    Example
    -------
    >>> traffic = build_traffic()
    >>> traffic.loc['Quận1', 'Quận3'] >= 0
    True
    """
    gdf = gpd.read_file("data/raw/hcmc_districts.geojson")
    gdf = gdf.to_crs(epsg=3857)
    gdf["centroid"] = gdf.geometry.centroid

    districts = gdf["district"].tolist()
    n = len(districts)

    traffic = pd.DataFrame(0.0, index=districts, columns=districts)

    for i in range(n):
        for j in range(n):
            if i != j:
                dist = gdf.iloc[i]["centroid"].distance(gdf.iloc[j]["centroid"])
                traffic.iloc[i, j] = 1 / dist if dist > 0 else 0

    # Normalize 0-1
    max_val = traffic.values.max()
    if max_val > 0:
        traffic = traffic / max_val

    # Chỉ giữ traffic giữa các quận TIẾP GIÁP (mask bằng adjacency)
    adj_path = "data/processed/adjacency_matrix.csv"
    if os.path.exists(adj_path):
        adj = pd.read_csv(adj_path, index_col=0, encoding="utf-8-sig")
        # Đảm bảo index/columns khớp
        common = [d for d in districts if d in adj.index]
        traffic_masked = traffic.loc[common, common] * adj.loc[common, common]
        print("Đã mask traffic theo adjacency matrix")
    else:
        traffic_masked = traffic
        print("Không tìm thấy adjacency_matrix.csv — dùng traffic đầy đủ")

    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/traffic_index.csv"
    traffic_masked.to_csv(output_path, encoding="utf-8-sig")
    print(f"Saved: {output_path}")
    print(traffic_masked.head())


if __name__ == "__main__":
    build_traffic()