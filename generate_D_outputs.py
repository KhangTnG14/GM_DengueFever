"""
Script tạo đủ 5 file output theo yêu cầu Phần D - Day 3:
  1. outputs/graphs/dengue_network.html      (Pyvis tương tác)
  2. outputs/graphs/gephi_export.gexf        (Gephi export)
  3. outputs/figures/centrality_bar.png      (Bar chart top 10 Betweenness)
  4. outputs/figures/community_plot.png      (Pie chart phân bổ ca theo community)
  5. outputs/figures/centrality_vs_cases_scatter.png  (Scatter: Betweenness vs Cases)

Chạy từ thư mục gốc dự án:
    python generate_D_outputs.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# ── 0. Setup đường dẫn ─────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PROC  = os.path.join(ROOT, "data", "processed")
DATA_RAW   = os.path.join(ROOT, "data", "raw")
OUT_FIG    = os.path.join(ROOT, "outputs", "figures")
OUT_GRAPH  = os.path.join(ROOT, "outputs", "graphs")

os.makedirs(OUT_FIG,   exist_ok=True)
os.makedirs(OUT_GRAPH, exist_ok=True)

# ── 1. Load dữ liệu ────────────────────────────────────────────────────────
df_cent   = pd.read_csv(os.path.join(DATA_PROC, "centrality_scores.csv")).dropna()
df_comm   = pd.read_csv(os.path.join(DATA_PROC, "community_labels.csv")).dropna()
df_edges  = pd.read_csv(os.path.join(DATA_PROC, "graph_edges.csv")).dropna()
df_nodes  = pd.read_csv(os.path.join(DATA_PROC, "graph_nodes.csv")).dropna()
df_cases_raw = pd.read_csv(
    os.path.join(DATA_RAW, "dengue_cases_by_district_2022_2024.csv"),
    encoding="utf-8-sig"
)

# Chuẩn hóa tên quận trong cases (raw dùng dấu cách, processed không có)
def normalize(s):
    return str(s).replace(" ", "").strip()

df_cases_raw["district_norm"] = df_cases_raw["district_name"].apply(normalize)
total_cases = (
    df_cases_raw.groupby("district_norm")["cases"]
    .sum()
    .reset_index()
    .rename(columns={"district_norm": "district", "cases": "total_cases"})
)

# Merge centrality + community + total_cases
df_cent["district_norm"] = df_cent["district"].apply(normalize)
df_comm["district_norm"] = df_comm["district"].apply(normalize)

df_merged = (
    df_cent
    .merge(df_comm[["district_norm", "louvain_community"]], on="district_norm", how="left")
    .merge(total_cases, left_on="district_norm", right_on="district", how="left",
           suffixes=("", "_cases"))
)
df_merged["total_cases"] = df_merged["total_cases"].fillna(0)
df_merged["louvain_community"] = df_merged["louvain_community"].fillna(-1).astype(int)

print(f"[OK] Loaded {len(df_merged)} districts")
print(df_merged[["district","betweenness","louvain_community","total_cases"]].to_string(index=False))

# ── Bảng màu community ─────────────────────────────────────────────────────
COMM_COLORS = {
    0: "#E63946",   # đỏ
    1: "#F4A261",   # cam
    2: "#2A9D8F",   # xanh lá
    3: "#457B9D",   # xanh dương
    4: "#A8DADC",   # xanh nhạt
   -1: "#CCCCCC",   # xám (không xác định)
}

def comm_color(cid):
    return COMM_COLORS.get(int(cid), "#CCCCCC")

# ═══════════════════════════════════════════════════════════════════════════
# FILE 3 — centrality_bar.png
# ═══════════════════════════════════════════════════════════════════════════
print("\n[Chart] Dang ve centrality_bar.png ...")

top10 = df_merged.nlargest(10, "betweenness").sort_values("betweenness", ascending=True)
colors_bar = [comm_color(c) for c in top10["louvain_community"]]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top10["district"], top10["betweenness"], color=colors_bar, edgecolor="white", linewidth=0.8)

for bar, val in zip(bars, top10["betweenness"]):
    ax.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}", va="center", ha="left", fontsize=9, color="#333333")

ax.set_title("Top 10 Quận theo Betweenness Centrality\n(màu = ổ dịch Louvain)",
             fontsize=13, fontweight="bold", pad=14)
ax.set_xlabel("Betweenness Centrality", fontsize=11)
ax.set_ylabel("Quận / Huyện", fontsize=11)
ax.set_xlim(0, top10["betweenness"].max() * 1.25)
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.spines[["top","right"]].set_visible(False)

# Legend community
unique_comms = sorted(top10["louvain_community"].unique())
legend_handles = [mpatches.Patch(color=comm_color(c), label=f"Cụm {c}") for c in unique_comms]
ax.legend(handles=legend_handles, title="Ổ dịch (Louvain)", loc="lower right", fontsize=9)

plt.tight_layout()
path_bar = os.path.join(OUT_FIG, "centrality_bar.png")
plt.savefig(path_bar, dpi=150, bbox_inches="tight")
plt.close()
print(f"   [OK] Saved: {path_bar}")

# ═══════════════════════════════════════════════════════════════════════════
# FILE 4 — community_plot.png  (Pie chart phân bổ ca theo community)
# ═══════════════════════════════════════════════════════════════════════════
print("\n[Chart] Dang ve community_plot.png ...")

comm_cases = (
    df_merged.groupby("louvain_community")["total_cases"]
    .sum()
    .reset_index()
    .sort_values("total_cases", ascending=False)
)
comm_cases["label"] = comm_cases["louvain_community"].apply(lambda x: f"Cụm {x}")
colors_pie = [comm_color(c) for c in comm_cases["louvain_community"]]

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Phân bổ ca bệnh Sốt Xuất Huyết theo Ổ Dịch (Louvain Community)",
             fontsize=13, fontweight="bold")

# Sub-plot 1: Pie chart
wedges, texts, autotexts = axes[0].pie(
    comm_cases["total_cases"],
    labels=comm_cases["label"],
    colors=colors_pie,
    autopct="%1.1f%%",
    startangle=140,
    pctdistance=0.78,
    wedgeprops=dict(edgecolor="white", linewidth=1.5)
)
for t in autotexts:
    t.set_fontsize(9)
axes[0].set_title("Tỉ lệ ca bệnh theo ổ dịch", fontsize=11)

# Sub-plot 2: Bar chart số quận + tổng ca
comm_district_count = df_merged.groupby("louvain_community")["district"].count().reset_index()
comm_district_count.columns = ["louvain_community", "num_districts"]
comm_summary = comm_cases.merge(comm_district_count, on="louvain_community")

x = np.arange(len(comm_summary))
bar_width = 0.4
ax2 = axes[1]
bars2 = ax2.bar(x, comm_summary["total_cases"], color=colors_pie, width=bar_width,
                edgecolor="white", linewidth=0.8, label="Tổng ca bệnh")
ax2.set_xticks(x)
ax2.set_xticklabels(comm_summary["label"], fontsize=10)
ax2.set_ylabel("Tổng ca bệnh (2022-2024)", fontsize=11)
ax2.set_title("Tổng ca bệnh & số quận theo ổ dịch", fontsize=11)
ax2.grid(axis="y", alpha=0.3, linestyle="--")
ax2.spines[["top","right"]].set_visible(False)

# Annotate số quận
for bar, row in zip(bars2, comm_summary.itertuples()):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
             f"{row.num_districts} quận", ha="center", va="bottom", fontsize=9, color="#555555")

# Bảng danh sách quận theo cụm bên dưới
district_by_comm = (
    df_merged.groupby("louvain_community")["district"]
    .apply(lambda x: ", ".join(x.tolist()))
    .reset_index()
)
district_by_comm.columns = ["Cụm", "Các quận"]
district_by_comm["Cụm"] = district_by_comm["Cụm"].apply(lambda x: f"Cụm {x}")

plt.tight_layout(rect=[0, 0.08, 1, 1])

# Table at bottom
table_data = [[row["Cụm"], row["Các quận"]] for _, row in district_by_comm.iterrows()]
col_labels = ["Ổ dịch", "Các quận/huyện thuộc cụm"]
table = plt.table(cellText=table_data, colLabels=col_labels,
                  cellLoc="left", loc="bottom", bbox=[0, -0.38, 1, 0.28])
table.auto_set_font_size(False)
table.set_fontsize(7.5)

path_comm = os.path.join(OUT_FIG, "community_plot.png")
plt.savefig(path_comm, dpi=150, bbox_inches="tight")
plt.close()
print(f"   [OK] Saved: {path_comm}")

# ═══════════════════════════════════════════════════════════════════════════
# FILE 5 — centrality_vs_cases_scatter.png
# ═══════════════════════════════════════════════════════════════════════════
print("\n[Chart] Dang ve centrality_vs_cases_scatter.png ...")

fig, ax = plt.subplots(figsize=(11, 7))

for _, row in df_merged.iterrows():
    color = comm_color(row["louvain_community"])
    size  = (row["betweenness"] * 3000) + 80
    ax.scatter(row["betweenness"], row["total_cases"],
               color=color, s=size, alpha=0.85, edgecolors="white", linewidths=1.2, zorder=3)
    ax.annotate(
        row["district"],
        xy=(row["betweenness"], row["total_cases"]),
        xytext=(6, 4), textcoords="offset points",
        fontsize=8, color="#333333"
    )

# Trend line
x_vals = df_merged["betweenness"].values
y_vals = df_merged["total_cases"].values
if x_vals.std() > 0:
    z = np.polyfit(x_vals, y_vals, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
    ax.plot(x_line, p(x_line), "--", color="#888888", linewidth=1.5, alpha=0.7, label="Trend line")

ax.set_title("Betweenness Centrality vs Tổng Ca Bệnh (2022–2024)\n"
             "Kích thước điểm tỉ lệ với Betweenness · Màu = Ổ dịch Louvain",
             fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Betweenness Centrality", fontsize=11)
ax.set_ylabel("Tổng ca bệnh (2022–2024)", fontsize=11)
ax.grid(alpha=0.25, linestyle="--")
ax.spines[["top","right"]].set_visible(False)

# Legend community
all_comms = sorted(df_merged["louvain_community"].unique())
legend_handles = [mpatches.Patch(color=comm_color(c), label=f"Cụm {c}") for c in all_comms]
legend_handles.append(plt.Line2D([0],[0], color="#888888", linestyle="--", label="Trend line"))
ax.legend(handles=legend_handles, title="Ổ dịch", loc="upper left", fontsize=9)

plt.tight_layout()
path_scatter = os.path.join(OUT_FIG, "centrality_vs_cases_scatter.png")
plt.savefig(path_scatter, dpi=150, bbox_inches="tight")
plt.close()
print(f"   [OK] Saved: {path_scatter}")

# ═══════════════════════════════════════════════════════════════════════════
# FILE 2 — gephi_export.gexf
# ═══════════════════════════════════════════════════════════════════════════
print("\n[GEXF] Dang tao gephi_export.gexf ...")

G = nx.Graph()

# Add nodes
for _, row in df_merged.iterrows():
    G.add_node(
        row["district"],
        total_cases=float(row["total_cases"]),
        betweenness=float(row["betweenness"]),
        pagerank=float(row["pagerank"]),
        degree_centrality=float(row["degree"]),
        louvain_community=int(row["louvain_community"]),
    )

# Add edges
for _, row in df_edges.iterrows():
    G.add_edge(row["source"], row["target"], weight=float(row["weight"]))

path_gexf = os.path.join(OUT_GRAPH, "gephi_export.gexf")
nx.write_gexf(G, path_gexf)
print(f"   [OK] Saved: {path_gexf}")
print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ═══════════════════════════════════════════════════════════════════════════
# FILE 1 — dengue_network.html  (Pyvis)
# ═══════════════════════════════════════════════════════════════════════════
print("\n[HTML] Dang tao dengue_network.html (Pyvis) ...")

try:
    from pyvis.network import Network
except ImportError:
    print("   ⚠️  pyvis chưa cài. Đang cài...")
    os.system(f"{sys.executable} -m pip install pyvis -q")
    from pyvis.network import Network

net = Network(
    height="750px", width="100%",
    bgcolor="#1a1a2e", font_color="#eaeaea"
)
net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120)

# Normalize node size: map total_cases → [20, 80]
max_cases = df_merged["total_cases"].max()
min_cases = df_merged["total_cases"].min()

def node_size(cases):
    if max_cases == min_cases:
        return 40
    return 20 + 60 * (cases - min_cases) / (max_cases - min_cases)

for _, row in df_merged.iterrows():
    district = row["district"]
    comm     = int(row["louvain_community"])
    color    = comm_color(comm)
    size     = node_size(row["total_cases"])

    tooltip = (
        f"{district}\n"
        f"Tong ca (2022-2024): {int(row['total_cases']):,}\n"
        f"Betweenness: {row['betweenness']:.4f}\n"
        f"PageRank:    {row['pagerank']:.4f}\n"
        f"O dich (Louvain): Cum {comm}"
    )

    net.add_node(
        district,
        label=district,
        title=tooltip,
        color=color,
        size=size,
        borderWidth=2,
        borderWidthSelected=4,
        font={"size": 13, "color": "#ffffff", "strokeWidth": 2, "strokeColor": "#000000"},
    )

# Add edges
for _, row in df_edges.iterrows():
    net.add_edge(
        row["source"], row["target"],
        weight=float(row["weight"]),
        width=max(1.0, float(row["weight"]) * 3),
        color={"color": "#ffffff44", "highlight": "#ffdd57"},
        title=f"Trọng số: {row['weight']:.2f}"
    )

# Legend HTML injected into notebook header
legend_html = """
<div style="position:fixed;top:15px;left:15px;background:#1a1a2e;
            border:1px solid #444;border-radius:8px;padding:12px;
            font-family:Arial,sans-serif;font-size:13px;color:#eaeaea;z-index:9999;">
  <b>O Dich Louvain</b><br>
  <span style="color:#E63946">&#9679;</span> Cum 0 &nbsp;
  <span style="color:#F4A261">&#9679;</span> Cum 1 &nbsp;
  <span style="color:#2A9D8F">&#9679;</span> Cum 2<br>
  <span style="color:#457B9D">&#9679;</span> Cum 3 &nbsp;
  <span style="color:#A8DADC">&#9679;</span> Cum 4<br><br>
  <b>Kich thuoc node</b><br>
  Ti le voi tong ca benh<br><br>
  <b>Canh</b><br>
  Dia ly ke nhau (weight=1)
</div>
"""

net.set_options("""
{
  "interaction": {
    "hover": true,
    "tooltipDelay": 100,
    "zoomView": true,
    "dragView": true
  },
  "physics": {
    "enabled": true,
    "barnesHut": {
      "gravitationalConstant": -8000,
      "centralGravity": 0.3,
      "springLength": 120,
      "springConstant": 0.04,
      "damping": 0.09
    },
    "stabilization": {"iterations": 200}
  },
  "nodes": {
    "shape": "dot"
  },
  "edges": {
    "smooth": {"type": "continuous"}
  }
}
""")

path_html = os.path.join(OUT_GRAPH, "dengue_network.html")
net.save_graph(path_html)

# Inject legend vào HTML
with open(path_html, "r", encoding="utf-8") as f:
    html_content = f.read()
html_content = html_content.replace("<body>", "<body>" + legend_html, 1)
with open(path_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"   [OK] Saved: {path_html}")

# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("HOAN THANH - 5 file Part D da duoc tao:")
print(f"  1. {os.path.join(OUT_GRAPH, 'dengue_network.html')}")
print(f"  2. {os.path.join(OUT_GRAPH, 'gephi_export.gexf')}")
print(f"  3. {os.path.join(OUT_FIG,   'centrality_bar.png')}")
print(f"  4. {os.path.join(OUT_FIG,   'community_plot.png')}")
print(f"  5. {os.path.join(OUT_FIG,   'centrality_vs_cases_scatter.png')}")
print("="*60)
