# src/epidemic_model.py

import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy


def sir_simulation(G, beta, gamma, seed_node, steps=20):
    """
    Mô phỏng lan truyền dịch bệnh SIR trên đồ thị.

    Parameters:
        G         : nx.Graph — đồ thị có trọng số
        beta      : float   — tỉ lệ lây nhiễm (0–1)
        gamma     : float   — tỉ lệ hồi phục (0–1)
        seed_node : str     — quận khởi phát dịch
        steps     : int     — số bước thời gian (tuần)

    Returns:
        history   : list of dict — trạng thái S/I/R từng node qua từng bước
        sir_curve : pd.DataFrame — tổng S, I, R toàn thành phố theo thời gian
    """
    # Khởi tạo trạng thái: tất cả Susceptible, trừ seed_node = Infected
    states = {node: "S" for node in G.nodes()}
    states[seed_node] = "I"

    history = [deepcopy(states)]
    curve = []

    for step in range(steps):
        new_states = deepcopy(states)

        for node in G.nodes():
            if states[node] == "I":
                # Lây cho các láng giềng S
                for neighbor in G.neighbors(node):
                    if states[neighbor] == "S":
                        # Xác suất lây tỉ lệ với edge weight
                        w = G[node][neighbor].get("weight", 1.0)
                        p_infect = 1 - np.exp(-beta * w)
                        if np.random.random() < p_infect:
                            new_states[neighbor] = "I"

                # Hồi phục
                if np.random.random() < gamma:
                    new_states[node] = "R"

        states = new_states
        history.append(deepcopy(states))

        n = len(G.nodes())
        curve.append({
            "step":  step + 1,
            "S":     sum(1 for s in states.values() if s == "S") / n,
            "I":     sum(1 for s in states.values() if s == "I") / n,
            "R":     sum(1 for s in states.values() if s == "R") / n,
        })

    sir_curve = pd.DataFrame(curve)
    return history, sir_curve


def apply_intervention(G, top_nodes, reduction=0.5):
    """
    Mô phỏng can thiệp y tế: giảm edge weight tại các quận trọng điểm.

    Parameters:
        G          : nx.Graph — đồ thị gốc
        top_nodes  : list    — danh sách quận cần can thiệp
        reduction  : float   — tỉ lệ giảm weight (0.5 = giảm 50%)

    Returns:
        G_intervened : nx.Graph — đồ thị đã can thiệp (bản copy)
    """
    G_intervened = deepcopy(G)
    for node in top_nodes:
        for neighbor in G_intervened.neighbors(node):
            G_intervened[node][neighbor]["weight"] *= (1 - reduction)
    return G_intervened


def plot_spread_heatmap(history, G, output_path, steps_to_show=None):
    """
    Vẽ heatmap lan truyền: trạng thái từng quận qua các bước thời gian.
    """
    if steps_to_show is None:
        steps_to_show = [0, 3, 6, 10, 15, len(history) - 1]
    steps_to_show = [s for s in steps_to_show if s < len(history)]

    nodes = list(G.nodes())
    state_map = {"S": 0, "I": 1, "R": 2}

    # Build matrix: rows = quận, cols = step
    matrix = np.array([
        [state_map[history[s][n]] for s in steps_to_show]
        for n in nodes
    ])

    fig, ax = plt.subplots(figsize=(10, 7))
    cmap = plt.cm.colors.ListedColormap(["#4C72B0", "#DD8452", "#55A868"])

    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=2)

    ax.set_xticks(range(len(steps_to_show)))
    ax.set_xticklabels([f"T{s}" for s in steps_to_show], fontsize=9)
    ax.set_yticks(range(len(nodes)))
    ax.set_yticklabels(nodes, fontsize=8)
    ax.set_xlabel("Bước thời gian (tuần)", fontsize=10)
    ax.set_title("Heatmap lan truyền dịch theo quận", fontsize=12, fontweight="bold")

    # Legend
    from matplotlib.patches import Patch
    legend = [
        Patch(color="#4C72B0", label="S — Chưa nhiễm"),
        Patch(color="#DD8452", label="I — Đang nhiễm"),
        Patch(color="#55A868", label="R — Đã hồi phục"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {output_path}")


def plot_sir_curve(curve_baseline, curve_intervened, seed_node, output_path):
    """
    Vẽ S, I, R của CẢ 2 kịch bản trên CÙNG 1 biểu đồ.
    Baseline = nét liền, Can thiệp = nét đứt.
    Output: sir_curve.png
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Baseline — nét liền
    ax.plot(curve_baseline["step"], curve_baseline["S"],
            color="#4C72B0", linewidth=2, linestyle="-",
            label="S — Baseline")
    ax.plot(curve_baseline["step"], curve_baseline["I"],
            color="#DD8452", linewidth=2, linestyle="-",
            label="I — Baseline")
    ax.plot(curve_baseline["step"], curve_baseline["R"],
            color="#55A868", linewidth=2, linestyle="-",
            label="R — Baseline")

    # Can thiệp — nét đứt
    ax.plot(curve_intervened["step"], curve_intervened["S"],
            color="#4C72B0", linewidth=2, linestyle="--",
            label="S — Can thiệp")
    ax.plot(curve_intervened["step"], curve_intervened["I"],
            color="#DD8452", linewidth=2, linestyle="--",
            label="I — Can thiệp")
    ax.plot(curve_intervened["step"], curve_intervened["R"],
            color="#55A868", linewidth=2, linestyle="--",
            label="R — Can thiệp")

    # Annotate peak cả 2
    for curve, style, label in [
        (curve_baseline,   "solid",  "Baseline"),
        (curve_intervened, "dashed", "Can thiệp"),
    ]:
        peak_step = curve.loc[curve["I"].idxmax(), "step"]
        peak_val  = curve["I"].max()
        ax.annotate(
            f"Peak {label}\n{peak_val:.1%} (T{peak_step})",
            xy=(peak_step, peak_val),
            xytext=(peak_step + 0.5, peak_val + 0.04),
            fontsize=8,
            arrowprops=dict(arrowstyle="->", color="gray"),
        )

    ax.set_title(
        f"Đường cong SIR — Khởi phát từ: {seed_node}\n"
        f"Nét liền = Baseline | Nét đứt = Can thiệp (giảm 50% top 3)",
        fontsize=12, fontweight="bold"
    )
    ax.set_xlabel("Tuần", fontsize=10)
    ax.set_ylabel("Tỉ lệ dân số", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {output_path}")


def plot_sir_comparison(curve_baseline, curve_intervened, seed_node, output_path):
    """
    Vẽ 2 subplot riêng để so sánh chi tiết từng kịch bản.
    Output: sir_intervention_comparison.png
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        f"So sánh 2 kịch bản SIR — Khởi phát: {seed_node}",
        fontsize=13, fontweight="bold"
    )

    configs = [
        (curve_baseline,   "Baseline (không can thiệp)",         axes[0]),
        (curve_intervened, "Can thiệp (giảm 50% weight top 3)",  axes[1]),
    ]

    for curve, title, ax in configs:
        ax.plot(curve["step"], curve["S"],
                label="S (Susceptible)", color="#4C72B0", linewidth=2)
        ax.plot(curve["step"], curve["I"],
                label="I (Infected)",    color="#DD8452", linewidth=2)
        ax.plot(curve["step"], curve["R"],
                label="R (Recovered)",   color="#55A868", linewidth=2)

        peak_step = curve.loc[curve["I"].idxmax(), "step"]
        peak_val  = curve["I"].max()
        ax.annotate(
            f"Peak: {peak_val:.1%}\n(tuần {peak_step})",
            xy=(peak_step, peak_val),
            xytext=(peak_step + 0.5, peak_val + 0.05),
            fontsize=8,
            arrowprops=dict(arrowstyle="->", color="gray"),
        )

        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Tuần", fontsize=10)
        ax.set_ylabel("Tỉ lệ dân số", fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {output_path}")