import geopandas as gpd
import unicodedata


# 🔥 Hàm bỏ dấu tiếng Việt
def remove_accents(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    return "".join([c for c in text if not unicodedata.combining(c)])


def filter_hcm():
    # 1. Load dữ liệu
    gdf = gpd.read_file("data/raw/gadm41_VNM_2.json")

    print("Danh sách tỉnh/thành (NAME_1):")
    print(gdf["NAME_1"].unique())

    # 2. Tạo cột không dấu để so sánh
    gdf["NAME_1_clean"] = gdf["NAME_1"].apply(remove_accents).str.lower()

    # 3. Filter TP.HCM (sau khi bỏ dấu)
    hcm = gdf[gdf["NAME_1_clean"].str.contains("hochiminh")]

    # 4. Check rỗng
    if hcm.empty:
        print("Không tìm thấy TP.HCM sau khi xử lý!")
        return

    print(f"Số quận/huyện tìm được: {len(hcm)}")

    # 5. Giữ cột cần thiết
    hcm = hcm[["NAME_2", "geometry"]]

    # 6. Rename
    hcm = hcm.rename(columns={"NAME_2": "district"})

    # 7. Reset index
    hcm = hcm.reset_index(drop=True)

    # 8. Set CRS nếu chưa có
    if hcm.crs is None:
        hcm = hcm.set_crs(epsg=4326)

    # 9. Save
    output_path = "data/raw/hcmc_districts.geojson"
    hcm.to_file(output_path, driver="GeoJSON")

    print(f"Đã lưu file: {output_path}")

    print("\nSample:")
    print(hcm.head())


if __name__ == "__main__":
    filter_hcm()