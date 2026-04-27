import geopandas as gpd
import pandas as pd
import os


def build_adjacency():
    gdf = gpd.read_file("data/raw/hcmc_districts.geojson")

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)

    # Chuyển sang mét để buffer chính xác
    gdf_m = gdf.to_crs(epsg=3857)

    districts = gdf["district"].tolist()
    n = len(districts)
    print(f"Tổng số quận/huyện: {n}")

    adjacency_matrix = pd.DataFrame(0, index=districts, columns=districts)

    for i in range(n):
        for j in range(i + 1, n):
            geom_i = gdf_m.iloc[i].geometry
            geom_j = gdf_m.iloc[j].geometry

            # Buffer 50m để bắt các cạnh bị lỗi làm tròn tọa độ
            if geom_i.touches(geom_j) or geom_i.buffer(50).intersects(geom_j.buffer(50)):
                d1 = districts[i]
                d2 = districts[j]
                adjacency_matrix.loc[d1, d2] = 1
                adjacency_matrix.loc[d2, d1] = 1

    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/adjacency_matrix.csv"
    adjacency_matrix.to_csv(output_path, encoding="utf-8-sig")
    print(f"Saved: {output_path}")

    # Kiểm tra sanity: mỗi quận phải có ít nhất 1 hàng xóm
    neighbor_count = adjacency_matrix.sum()
    print("\nSố quận hàng xóm của từng quận:")
    print(neighbor_count.sort_values())

    isolated = neighbor_count[neighbor_count == 0]
    if len(isolated) > 0:
        print(f"\nQuận bị cô lập (0 hàng xóm): {isolated.index.tolist()}")
        print("→ Tăng buffer lên 100m hoặc kiểm tra lại GeoJSON")
    else:
        print("\nTất cả quận đều có ít nhất 1 hàng xóm")


if __name__ == "__main__":
    build_adjacency()