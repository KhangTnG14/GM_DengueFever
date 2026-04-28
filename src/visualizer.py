import pandas as pd
import geopandas as gpd
import folium
import os
import json

def load_and_merge_data():
    """Loads all necessary datasets and merges them based on standardized district names."""
    # 1. Load cases
    cases_df = pd.read_csv('data/raw/dengue_cases_by_district_2022_2024.csv')
    cases_total = cases_df.groupby('district_name')['cases'].sum().reset_index()
    cases_total['district'] = cases_total['district_name'].str.replace(' ', '')

    # 2. Load population (Using ; as separator based on previous check)
    pop_df = pd.read_csv('data/raw/populations.csv', sep=';')
    pop_total = pop_df.groupby('district_name')['population'].max().reset_index()
    pop_total['district'] = pop_total['district_name'].str.replace(' ', '')

    # 3. Merge cases and population, calculate cases per 100k
    data_df = pd.merge(cases_total, pop_total[['district', 'population']], on='district', how='left')
    data_df['cases_per_100k'] = (data_df['cases'] / data_df['population']) * 100000
    data_df['cases_per_100k'] = data_df['cases_per_100k'].round(2)

    # 4. Load community and centrality
    comm_df = pd.read_csv('data/processed/community_labels.csv')
    cent_df = pd.read_csv('data/processed/centrality_scores.csv')

    # Merge all tabular data
    df = data_df.merge(comm_df, on='district', how='left').merge(cent_df, on='district', how='left')
    df['centrality_rank'] = df['betweenness'].rank(ascending=False, na_option='bottom').fillna(999).astype(int)

    # 5. Load GeoJSON
    gdf = gpd.read_file('data/raw/hcmc_districts.geojson')
    # Gom Quận 2, Quận 9 vào Thủ Đức (TP Thủ Đức) để khớp với data hiện tại (22 quận huyện)
    gdf['district'] = gdf['district'].replace({'Quận2': 'ThủĐức', 'Quận9': 'ThủĐức'})
    gdf = gdf.dissolve(by='district').reset_index()
    
    # Merge geospatial data with tabular data
    gdf = gdf.merge(df, on='district', how='left')
    
    return gdf, df

def get_centroids(gdf):
    """Calculates representative points for each district polygon to use for edge rendering.
    Using representative_point() instead of centroid ensures the point falls inside the polygon,
    which is important for concave districts like Bình Chánh."""
    # Reproject to a projected CRS (UTM Zone 48N for HCM) to calculate accurate points
    gdf_proj = gdf.to_crs('EPSG:32648')
    centroids = gdf_proj.representative_point().to_crs('EPSG:4326')
    
    centroid_dict = {}
    for idx, row in gdf.iterrows():
        # Folium uses [lat, lon]
        centroid_dict[row['district']] = [centroids.iloc[idx].y, centroids.iloc[idx].x]
    return centroid_dict

def draw_edges(m, centroid_dict):
    """Draws network edges between district centroids based on graph_edges.csv."""
    edges_df = pd.read_csv('data/processed/graph_edges.csv')
    edges_group = folium.FeatureGroup(name='Mạng lưới lây nhiễm (Edges)', show=True)
    
    max_w = edges_df['weight'].max() if len(edges_df) > 0 else 1
    
    for _, row in edges_df.iterrows():
        src = str(row['source']).replace(' ', '')
        tgt = str(row['target']).replace(' ', '')
        w = row['weight']
        
        if src in centroid_dict and tgt in centroid_dict:
            p1 = centroid_dict[src]
            p2 = centroid_dict[tgt]
            
            thickness = (w / max_w) * 5 + 1
            
            folium.PolyLine(
                locations=[p1, p2],
                color='blue',
                weight=thickness,
                opacity=0.4,
                tooltip=f"Từ: {src} - Đến: {tgt} (Trọng số: {w:.2f})"
            ).add_to(edges_group)
            
    edges_group.add_to(m)

def create_choropleth_map():
    """Creates the choropleth map for total cases and cases per 100k population."""
    gdf, df = load_and_merge_data()
    centroid_dict = get_centroids(gdf)

    m = folium.Map(location=[10.7769, 106.7009], zoom_start=11, tiles='cartodbpositron')

    # Layer 1: Total Cases Choropleth
    folium.Choropleth(
        geo_data=json.loads(gdf.to_json()),
        name='Tổng ca bệnh (Choropleth)',
        data=df,
        columns=['district', 'cases'],
        key_on='feature.properties.district',
        fill_color='Reds',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Tổng ca bệnh Sốt xuất huyết (2022-2024)',
        show=True
    ).add_to(m)

    # Layer 2: Cases per 100k Choropleth
    folium.Choropleth(
        geo_data=json.loads(gdf.to_json()),
        name='Tỉ lệ mắc/100k dân (Choropleth)',
        data=df,
        columns=['district', 'cases_per_100k'],
        key_on='feature.properties.district',
        fill_color='Oranges',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Tỉ lệ mắc bệnh trên 100k dân',
        show=False
    ).add_to(m)

    # Tooltips for the districts
    style_function = lambda x: {'fillColor': '#ffffff', 'color':'#000000', 'fillOpacity': 0.01, 'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 'color':'#000000', 'fillOpacity': 0.3, 'weight': 0.1}
    
    tooltip = folium.features.GeoJson(
        json.loads(gdf.to_json()),
        name='Thông tin Quận/Huyện',
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['district_name', 'cases', 'cases_per_100k', 'louvain_community', 'centrality_rank'],
            aliases=['Quận/Huyện:', 'Tổng số ca:', 'Tỉ lệ/100k dân:', 'Ổ dịch (Community ID):', 'Ranking (Betweenness):'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 14px; padding: 10px; border: 1px solid grey;") 
        )
    )
    m.add_child(tooltip)
    m.keep_in_front(tooltip)

    # Add network edges
    draw_edges(m, centroid_dict)

    # Add Layer Control
    folium.LayerControl().add_to(m)

    os.makedirs('outputs/maps', exist_ok=True)
    output_path = 'outputs/maps/hcmc_dengue_choropleth.html'
    m.save(output_path)
    print(f"Đã lưu bản đồ ca bệnh tại: {output_path}")

def create_cluster_map():
    """Creates the map visualizing disease clusters (communities) and the network."""
    gdf, df = load_and_merge_data()
    centroid_dict = get_centroids(gdf)

    m = folium.Map(location=[10.7769, 106.7009], zoom_start=11, tiles='cartodbpositron')

    # Color palette for communities
    cluster_colors = [
        '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', 
        '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999'
    ]
    
    # Default to 0 if NaN just in case
    communities = df['louvain_community'].fillna(0).unique()
    color_dict = {comm: cluster_colors[i % len(cluster_colors)] for i, comm in enumerate(communities)}
    
    def cluster_style(feature):
        comm = feature['properties'].get('louvain_community')
        if pd.isna(comm):
            comm = 0
        color = color_dict.get(comm, '#808080')
        return {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        }

    # Add community clusters layer
    folium.GeoJson(
        json.loads(gdf.to_json()),
        name='Ổ dịch (Community Clustering)',
        style_function=cluster_style,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['district_name', 'louvain_community', 'cases', 'centrality_rank'],
            aliases=['Quận/Huyện:', 'Ổ dịch (Community ID):', 'Tổng số ca:', 'Ranking (Betweenness):'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 14px; padding: 10px; border: 1px solid grey;")
        )
    ).add_to(m)

    # Add network edges
    draw_edges(m, centroid_dict)

    # Add Layer Control
    folium.LayerControl().add_to(m)

    os.makedirs('outputs/maps', exist_ok=True)
    output_path = 'outputs/maps/cluster_map.html'
    m.save(output_path)
    print(f"Đã lưu bản đồ ổ dịch tại: {output_path}")

if __name__ == "__main__":
    print("Đang tạo bản đồ phân bố ca bệnh...")
    create_choropleth_map()
    print("Đang tạo bản đồ cụm ổ dịch...")
    create_cluster_map()
    print("Hoàn tất!")
