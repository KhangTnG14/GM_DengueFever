import geopandas as gpd
import pandas as pd
import unicodedata
import os


def remove_accents(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    return "".join([c for c in text if not unicodedata.combining(c)])


def filter_and_merge_hcm():
    # 1. Load
    gdf = gpd.read_file("data/raw/gadm41_VNM_2.json")

    # 2. Filter HCM
    gdf["NAME_1_clean"] = gdf["NAME_1"].apply(remove_accents).str.lower()
    hcm = gdf[gdf["NAME_1_clean"].str.contains("hochiminh")].copy()
    hcm = hcm[["NAME_2", "geometry"]].rename(columns={"NAME_2": "district"})
    hcm = hcm.reset_index(drop=True)

    print(f"Số quận trước khi merge: {len(hcm)}")
    print("Danh sách quận hiện có:")
    print(sorted(hcm["district"].tolist()))

    # 3. Xác định tên 3 quận cũ trong file GADM
    # (In ra ở bước trên rồi điền vào đây cho chính xác)
    thu_duc_old_names = ["Quận2", "Quận9", "ThủĐức"]  # ← Sửa theo tên thực trong file

    # 4. Tách 3 quận cũ ra
    mask = hcm["district"].apply(remove_accents).str.lower().isin(
        [remove_accents(n).lower() for n in thu_duc_old_names]
    )

    # Kiểm tra có tìm đúng 3 quận không
    print(f"\nTìm thấy {mask.sum()} quận để merge (cần đúng 3):")
    print(hcm[mask]["district"].tolist())

    if mask.sum() != 3:
        print("⚠️  Không đúng 3 quận — kiểm tra lại tên trong thu_duc_old_names!")
        return

    # 5. Merge geometry 3 quận → 1 polygon TP. Thủ Đức
    thu_duc_merged = hcm[mask].copy()
    thu_duc_merged["district"] = "Thủ Đức"  # gán tên chung trước
    thu_duc_dissolved = thu_duc_merged.dissolve(by="district").reset_index()

    # 6. Ghép lại: các quận còn lại + TP. Thủ Đức
    other = hcm[~mask].copy()
    hcm_fixed = pd.concat([other, thu_duc_dissolved], ignore_index=True)

    if hcm_fixed.crs is None:
        hcm_fixed = hcm_fixed.set_crs(epsg=4326)

    print(f"\nSố quận sau khi merge: {len(hcm_fixed)}")  # Phải ra 21
    print(sorted(hcm_fixed["district"].tolist()))

    # 7. Save
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/hcmc_districts.geojson"
    hcm_fixed.to_file(output_path, driver="GeoJSON")
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    filter_and_merge_hcm()