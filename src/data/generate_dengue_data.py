import pandas as pd
import numpy as np
import os

# ── 22 QUẬN với tên đúng (khớp với GeoJSON GADM) và district_id khớp population.csv
DISTRICTS = [
    {"district_id": "BC",  "district_name": "Bình Chánh", "base_annual": 9500},
    {"district_id": "BT",  "district_name": "Bình Tân",   "base_annual": 7800},
    {"district_id": "BTH", "district_name": "Bình Thạnh", "base_annual": 4200},
    {"district_id": "CG",  "district_name": "Cần Giờ",    "base_annual": 800},
    {"district_id": "CC",  "district_name": "Củ Chi",      "base_annual": 4800},
    {"district_id": "GV",  "district_name": "Gò Vấp",     "base_annual": 5800},
    {"district_id": "HM",  "district_name": "Hóc Môn",    "base_annual": 5500},
    {"district_id": "NB",  "district_name": "Nhà Bè",     "base_annual": 2200},
    {"district_id": "PN",  "district_name": "Phú Nhuận",  "base_annual": 900},
    {"district_id": "Q1",  "district_name": "Quận 1",     "base_annual": 1200},
    {"district_id": "Q10", "district_name": "Quận 10",    "base_annual": 1300},
    {"district_id": "Q11", "district_name": "Quận 11",    "base_annual": 1500},
    {"district_id": "Q12", "district_name": "Quận 12",    "base_annual": 5500},
    {"district_id": "Q3",  "district_name": "Quận 3",     "base_annual": 900},
    {"district_id": "Q4",  "district_name": "Quận 4",     "base_annual": 1400},
    {"district_id": "Q5",  "district_name": "Quận 5",     "base_annual": 1100},
    {"district_id": "Q6",  "district_name": "Quận 6",     "base_annual": 1800},
    {"district_id": "Q7",  "district_name": "Quận 7",     "base_annual": 2800},
    {"district_id": "Q8",  "district_name": "Quận 8",     "base_annual": 3200},
    {"district_id": "TB",  "district_name": "Tân Bình",   "base_annual": 4100},
    {"district_id": "TP",  "district_name": "Tân Phú",    "base_annual": 4000},
    {"district_id": "TD",  "district_name": "Thủ Đức",    "base_annual": 12000},
]

# Hệ số mùa vụ theo tuần — đỉnh tuần 28-42 (tháng 7-10, mùa mưa TP.HCM)
def seasonal_factor(week: int) -> float:
    # Dùng sin lệch pha để đỉnh rơi vào giữa năm (tuần ~35)
    peak_week = 35
    return 1.0 + 0.85 * np.exp(-0.5 * ((week - peak_week) / 10) ** 2)

# Hệ số theo năm — 2023 bùng phát mạnh nhất (thực tế ~89k ca)
YEAR_FACTOR = {2022: 0.75, 2023: 1.00, 2024: 0.85}

def week_to_month(week: int) -> int:
    """Chuyển số tuần sang tháng chính xác (ISO week approximation)."""
    return min(int((week - 1) / 52 * 12) + 1, 12)

def generate_data():
    np.random.seed(42)
    records = []

    for year in [2022, 2023, 2024]:
        for week in range(1, 53):
            sf   = seasonal_factor(week)
            yf   = YEAR_FACTOR[year]
            month = week_to_month(week)

            for d in DISTRICTS:
                # Base trung bình mỗi tuần của quận này
                weekly_base = d["base_annual"] / 52

                # Số ca = base × mùa vụ × năm × nhiễu Poisson (realistic noise)
                mean_cases = weekly_base * sf * yf
                cases = int(np.random.poisson(max(mean_cases, 0.1)))

                records.append({
                    "district_id":   d["district_id"],
                    "district_name": d["district_name"],
                    "year":          year,
                    "month":         month,
                    "week":          week,
                    "cases":         cases,
                })

    df = pd.DataFrame(records)

    # ── Kiểm tra sanity: tổng ca mỗi năm
    summary = df.groupby("year")["cases"].sum()
    print("Tổng ca theo năm:")
    print(summary.to_string())
    print(f"\nTổng 3 năm: {df['cases'].sum():,} ca")
    print(f"Số dòng: {len(df):,}")

    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/dengue_cases_by_district_2022_2024.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved → {output_path}")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    generate_data()