import pandas as pd
import geopandas as gpd
import folium
import os

def create_draft_map():
    """
    Tạo bản đồ choropleth nháp cho tổng số ca nhiễm dengue và lưu thành tệp HTML.

    Hàm này thực hiện tải dữ liệu thô về các ca nhiễm dengue và tệp GeoJSON của các quận/huyện, 
    tổng hợp số lượng ca bệnh theo từng đơn vị hành chính, chuẩn hóa tên quận/huyện, 
    và dựng (render) bản đồ folium choropleth. Tệp HTML đầu ra sẽ được lưu tại 
    `outputs/maps/draft_choropleth.html`.

    Returns
    -------
    str
        Đường dẫn (outputs/maps/draft_choropleth.html) dẫn đến tệp HTML đã lưu.

    Raises
    ------
    FileNotFoundError
        Nếu các tệp dữ liệu nguồn (data/raw/dengue_cases_by_district_2022_2024.csv) bị thiếu.

    Example
    -------
    >>> output_path = create_draft_map()
    >>> output_path.endswith('draft_choropleth.html')
    True
    """
    # 1. Tải dữ liệu
    cases_path = "data/raw/dengue_cases_by_district_2022_2024.csv"
    geojson_path = "data/raw/hcmc_districts.geojson"
    output_dir = "outputs/maps"
    # Quay lại tên file chuẩn theo yêu cầu
    output_path = os.path.join(output_dir, "draft_choropleth.html")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pd.read_csv(cases_path)
    gdf = gpd.read_file(geojson_path)

    # 2. Tổng hợp số ca bệnh
    total_cases = df.groupby('district_name')['cases'].sum().reset_index()

    # 3. Chuẩn hóa tên quận
    total_cases['name_normalized'] = total_cases['district_name'].str.replace(' ', '')
    gdf['name_normalized'] = gdf['district'].str.replace(' ', '')

    # 4. Khởi tạo bản đồ
    m = folium.Map(location=[10.7769, 106.7009], zoom_start=11, tiles='cartodbpositron')

    # Chú giải tiếng Việt (Unicode mã hóa an toàn)
    legend_title = "T\u1ed5ng s\u1ed1 ca b\u1ec7nh S\u1ed1t xu\u1ea5t huy\u1ebft (2022-2024)"

    folium.Choropleth(
        geo_data=gdf,
        name='choropleth',
        data=total_cases,
        columns=['name_normalized', 'cases'],
        key_on='feature.properties.district',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_title,
    ).add_to(m)

    # Thêm Tooltips
    style_function = lambda x: {'fillColor': '#ffffff', 'color':'#000000', 'fillOpacity': 0.01, 'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 'color':'#000000', 'fillOpacity': 0.3, 'weight': 0.1}
    
    gdf_with_data = gdf.merge(total_cases[['name_normalized', 'district_name', 'cases']], on='name_normalized')
    
    alias_district = "Qu\u1eadn/Huy\u1ec7n: "
    alias_cases = "T\u1ed5ng s\u1ed1 ca: "

    NIL = folium.features.GeoJson(
        gdf_with_data,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['district_name', 'cases'],
            aliases=[alias_district, alias_cases],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 14px; padding: 10px; border: 1px solid grey;") 
        )
    )
    NIL.add_to(m)

    # 5. Lưu bản đồ
    m.save(output_path)
    print(f"Ban do da duoc cap nhat tai: {output_path}")

if __name__ == "__main__":
    create_draft_map()
