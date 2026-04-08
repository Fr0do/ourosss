import json
import textwrap


def _remote_script(parquet_glob: str, opts: dict) -> str:
    """Build a Python script that outputs JSON for the handler to format."""
    opts_json = json.dumps(opts)
    return textwrap.dedent(f'''\
import glob, json, sys, random, base64, io
import pandas as pd

files = sorted(glob.glob("{parquet_glob}"))
if not files:
    print(json.dumps({{"error": "No completions found."}}))
    sys.exit(0)

opts = json.loads('{opts_json}')
mode = opts["mode"]
step_sel = opts.get("step")  # {{"index": N}} or {{"slice": [start, stop, step]}} or None
count = opts.get("count", 3)
filt = opts.get("filter")
brief = opts.get("brief", True)

def select_files(files, sel):
    """Select files using Python-style index or slice."""
    if sel is None:
        return [files[-1]]
    if "index" in sel:
        idx = sel["index"]
        try:
            return [files[idx]]
        except IndexError:
            return None
    if "slice" in sel:
        s = sel["slice"]
        return files[slice(s[0], s[1], s[2])]
    return [files[-1]]

def step_stats(df):
    d = {{}}
    d["step"] = int(df["step"].iloc[0])
    d["n"] = len(df)
    d["acc_mean"] = float(df["accuracy_reward_func"].mean())
    d["acc_pos"] = int((df["accuracy_reward_func"] == 1).sum())
    d["acc_neg"] = int((df["accuracy_reward_func"] == -1).sum())
    d["fmt_mean"] = float(df["format_reward_func"].mean())
    d["fmt_min"] = float(df["format_reward_func"].min())
    d["fmt_max"] = float(df["format_reward_func"].max())
    if "spectral_reward_func" in df.columns:
        d["spec_mean"] = float(df["spectral_reward_func"].mean())
    d["adv_mean"] = float(df["advantage"].mean())
    d["adv_std"] = float(df["advantage"].std())
    d["comp_len_mean"] = float(df["completion"].str.len().mean())
    return d

def get_samples(df, n, filt, brief):
    if filt == "correct":
        df = df[df["accuracy_reward_func"] == 1.0]
    elif filt == "wrong":
        df = df[df["accuracy_reward_func"] != 1.0]
    if len(df) == 0:
        return []
    rows = df.sample(min(n, len(df)))
    samples = []
    for _, row in rows.iterrows():
        s = {{
            "prompt": str(row["prompt"]),
            "completion": str(row["completion"]),
            "acc": float(row["accuracy_reward_func"]),
            "fmt": float(row["format_reward_func"]),
            "adv": float(row["advantage"]),
        }}
        if "spectral_reward_func" in df.columns:
            s["spec"] = float(row["spectral_reward_func"])
        if brief:
            s["completion"] = s["completion"][:600]
            s["prompt"] = s["prompt"][:200]
        samples.append(s)
    return samples

def render_chart(trend):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    steps = [t["step"] for t in trend]
    acc = [t["acc_pos"] / t["n"] * 100 for t in trend]
    fmt = [t["fmt_mean"] for t in trend]
    has_spec = "spec_mean" in trend[0]
    spec = [t.get("spec_mean", 0) for t in trend] if has_spec else None
    comp_len = [t.get("comp_len_mean", 0) for t in trend]

    n_panels = 3 if has_spec else 2
    fig, axes = plt.subplots(n_panels, 1, figsize=(10, 3 * n_panels), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#e0e0e0")
        ax.spines["bottom"].set_color("#333")
        ax.spines["left"].set_color("#333")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.label.set_color("#e0e0e0")
        ax.xaxis.label.set_color("#e0e0e0")
        ax.title.set_color("#e0e0e0")

    def smooth(y, w=7):
        if len(y) < w:
            return y
        return np.convolve(y, np.ones(w)/w, mode="valid").tolist()

    smooth_steps = steps[len(steps)-len(smooth(acc)):]

    ax = axes[0]
    ax.plot(steps, acc, alpha=0.3, color="#4cc9f0", linewidth=0.8)
    ax.plot(smooth_steps, smooth(acc), color="#4cc9f0", linewidth=2, label="accuracy %")
    ax.set_ylabel("Accuracy %")
    ax.set_ylim(-5, 105)
    ax.axhline(y=50, color="#555", linestyle="--", linewidth=0.5)
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    ax.set_title(f"GRPO Completions  |  steps {{steps[0]}}-{{steps[-1]}}  |  {{len(trend)}} checkpoints")

    ax = axes[1]
    ax.plot(steps, fmt, alpha=0.3, color="#f72585", linewidth=0.8)
    ax.plot(smooth_steps, smooth(fmt), color="#f72585", linewidth=2, label="format reward")
    ax.set_ylabel("Format Reward")
    ax2 = ax.twinx()
    ax2.plot(steps, comp_len, alpha=0.2, color="#7209b7", linewidth=0.8)
    ax2.plot(smooth_steps, smooth(comp_len), color="#7209b7", linewidth=1.5, label="completion len", linestyle="--")
    ax2.set_ylabel("Completion Length", color="#7209b7")
    ax2.tick_params(colors="#7209b7")
    ax2.spines["right"].set_color("#7209b7")
    ax2.spines["top"].set_visible(False)
    ax.legend(loc="upper left", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    ax2.legend(loc="upper right", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")

    if has_spec:
        ax = axes[2]
        ax.plot(steps, spec, alpha=0.3, color="#4361ee", linewidth=0.8)
        ax.plot(smooth_steps, smooth(spec), color="#4361ee", linewidth=2, label="spectral reward")
        ax.set_ylabel("Spectral Reward")
        ax.set_xlabel("Step")
        ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    else:
        axes[-1].set_xlabel("Step")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

if mode == "baseline":
    import re as _re
    import numpy as _np

    all_dfs = []
    trend = []
    for f in files:
        df = pd.read_parquet(f)
        all_dfs.append(df)
        trend.append(step_stats(df))

    full = pd.concat(all_dfs, ignore_index=True)
    has_spec = "spectral_reward_func" in full.columns

    def count_nodes(prompt):
        lines = prompt.split("\\n")
        n = 0
        for line in lines:
            stripped = line.strip()
            if stripped and "->" in stripped and ":" not in stripped[:3]:
                continue
            if stripped and len(stripped) >= 1 and stripped[0].isupper() and (":" in stripped or "->" in stripped):
                n += 1
        return n

    full["node_count"] = full["prompt"].apply(count_nodes)
    full["comp_len"] = full["completion"].str.len()
    full["correct"] = (full["accuracy_reward_func"] == 1.0)

    steps = [t["step"] for t in trend]
    acc_pct = [t["acc_pos"] / t["n"] * 100 for t in trend]
    fmt_vals = [t["fmt_mean"] for t in trend]
    spec_vals = [t.get("spec_mean", 0) for t in trend]
    comp_lens = [t["comp_len_mean"] for t in trend]

    total_completions = len(full)
    total_correct = int(full["correct"].sum())
    overall_acc = total_correct / total_completions * 100
    avg_comp_len = float(full["comp_len"].mean())
    median_comp_len = float(full["comp_len"].median())
    avg_fmt = float(full["format_reward_func"].mean())
    avg_spec = float(full["spectral_reward_func"].mean()) if has_spec else None
    avg_adv = float(full["advantage"].mean())

    full["len_q"] = pd.qcut(full["comp_len"], 4, labels=["short", "medium", "long", "very_long"], duplicates="drop")
    acc_by_len = full.groupby("len_q", observed=True)["correct"].mean().to_dict()
    acc_by_len = {{k: round(float(v) * 100, 1) for k, v in acc_by_len.items()}}

    correct_len = float(full[full["correct"]]["comp_len"].mean()) if total_correct > 0 else 0
    wrong_len = float(full[~full["correct"]]["comp_len"].mean()) if total_correct < total_completions else 0

    mid = len(trend) // 2
    first_half_acc = sum(t["acc_pos"] for t in trend[:mid]) / sum(t["n"] for t in trend[:mid]) * 100 if mid > 0 else 0
    second_half_acc = sum(t["acc_pos"] for t in trend[mid:]) / sum(t["n"] for t in trend[mid:]) * 100

    spec_corr = None
    if has_spec:
        spec_corr = float(full["spectral_reward_func"].corr(full["accuracy_reward_func"]))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.patch.set_facecolor("#1a1a2e")
    fig.suptitle(f"BASELINE REPORT  |  {{len(files)}} steps  |  {{total_completions}} completions", color="#e0e0e0", fontsize=14, fontweight="bold")

    def style_ax(ax):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#e0e0e0", labelsize=8)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color("#333")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.yaxis.label.set_color("#e0e0e0")
        ax.xaxis.label.set_color("#e0e0e0")
        ax.title.set_color("#e0e0e0")

    for ax_row in axes:
        for ax in ax_row:
            style_ax(ax)

    def smooth(y, w=5):
        if len(y) < w:
            return y
        return np.convolve(y, np.ones(w)/w, mode="valid").tolist()

    ax = axes[0][0]
    ax.plot(steps, acc_pct, alpha=0.3, color="#4cc9f0", linewidth=0.8)
    sm = smooth(acc_pct)
    ax.plot(steps[len(steps)-len(sm):], sm, color="#4cc9f0", linewidth=2)
    ax.axhline(y=50, color="#555", linestyle="--", linewidth=0.5)
    ax.set_ylabel("Accuracy %")
    ax.set_ylim(-5, 105)
    ax.set_title("Accuracy Over Training")

    ax = axes[0][1]
    ax.hist(full["accuracy_reward_func"].values, bins=20, color="#4cc9f0", alpha=0.7, label="accuracy")
    ax.hist(full["format_reward_func"].values, bins=20, color="#f72585", alpha=0.5, label="format")
    if has_spec:
        ax.hist(full["spectral_reward_func"].values, bins=20, color="#4361ee", alpha=0.5, label="spectral")
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0", fontsize=7)
    ax.set_title("Reward Distributions (all steps)")
    ax.set_ylabel("Count")

    ax = axes[1][0]
    ax.plot(steps, fmt_vals, alpha=0.3, color="#f72585", linewidth=0.8)
    sm_fmt = smooth(fmt_vals)
    ax.plot(steps[len(steps)-len(sm_fmt):], sm_fmt, color="#f72585", linewidth=2, label="format")
    if has_spec:
        ax2 = ax.twinx()
        ax2.plot(steps, spec_vals, alpha=0.3, color="#4361ee", linewidth=0.8)
        sm_spec = smooth(spec_vals)
        ax2.plot(steps[len(steps)-len(sm_spec):], sm_spec, color="#4361ee", linewidth=2, label="spectral")
        ax2.set_ylabel("Spectral", color="#4361ee")
        ax2.tick_params(colors="#4361ee", labelsize=8)
        ax2.spines["right"].set_color("#4361ee")
        ax2.spines["top"].set_visible(False)
        ax2.legend(loc="upper right", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0", fontsize=7)
    ax.set_ylabel("Format Reward")
    ax.set_title("Format & Spectral Trends")
    ax.legend(loc="upper left", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0", fontsize=7)

    ax = axes[1][1]
    bins = np.linspace(0, full["comp_len"].quantile(0.95), 30)
    if total_correct > 0:
        ax.hist(full[full["correct"]]["comp_len"].values, bins=bins, color="#06d6a0", alpha=0.6, label=f"correct (avg {{correct_len:.0f}})")
    if total_correct < total_completions:
        ax.hist(full[~full["correct"]]["comp_len"].values, bins=bins, color="#ef476f", alpha=0.5, label=f"wrong (avg {{wrong_len:.0f}})")
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0", fontsize=7)
    ax.set_title("Completion Length: Correct vs Wrong")
    ax.set_xlabel("Characters")
    ax.set_ylabel("Count")

    ax = axes[2][0]
    ax.plot(steps, comp_lens, alpha=0.3, color="#7209b7", linewidth=0.8)
    sm_cl = smooth(comp_lens)
    ax.plot(steps[len(steps)-len(sm_cl):], sm_cl, color="#7209b7", linewidth=2)
    ax.set_ylabel("Avg Characters")
    ax.set_xlabel("Step")
    ax.set_title("Completion Length Over Training")

    ax = axes[2][1]
    ax.axis("off")
    summary_lines = [
        f"Total completions:  {{total_completions}}",
        f"Overall accuracy:   {{overall_acc:.1f}}%",
        f"  1st half:         {{first_half_acc:.1f}}%",
        f"  2nd half:         {{second_half_acc:.1f}}%",
        f"",
        f"Avg completion len: {{avg_comp_len:.0f}} chars (median {{median_comp_len:.0f}})",
        f"  correct avg:      {{correct_len:.0f}} chars",
        f"  wrong avg:        {{wrong_len:.0f}} chars",
        f"",
        f"Mean format reward: {{avg_fmt:.3f}}",
    ]
    if avg_spec is not None:
        summary_lines.append(f"Mean spectral:      {{avg_spec:.4f}}")
    if spec_corr is not None:
        summary_lines.append(f"Spectral~accuracy:  r={{spec_corr:.3f}}")
    summary_lines.append(f"Mean advantage:     {{avg_adv:.3f}}")
    if acc_by_len:
        summary_lines.append("")
        summary_lines.append("Accuracy by length quartile:")
        for q, v in acc_by_len.items():
            summary_lines.append(f"  {{q}}: {{v:.1f}}%")

    ax.text(0.05, 0.95, "\\n".join(summary_lines), transform=ax.transAxes,
            fontsize=9, verticalalignment="top", fontfamily="monospace",
            color="#e0e0e0",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#16213e", edgecolor="#333"))

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode()

    caption = f"Baseline: {{len(files)}} steps, {{total_completions}} completions\\n"
    caption += f"Accuracy: {{overall_acc:.1f}}% ({{first_half_acc:.1f}}% -> {{second_half_acc:.1f}}%)\\n"
    caption += f"Completion: {{avg_comp_len:.0f}} chars (correct={{correct_len:.0f}}, wrong={{wrong_len:.0f}})\\n"
    caption += f"Format: {{avg_fmt:.3f}}"
    if avg_spec is not None:
        caption += f"  Spectral: {{avg_spec:.4f}}"
    if spec_corr is not None:
        caption += f"  (r={{spec_corr:.3f}} w/ acc)"

    result = {{
        "type": "baseline",
        "chart": chart_b64,
        "caption": caption,
        "summary": {{
            "total_steps": len(files),
            "total_completions": total_completions,
            "overall_acc": overall_acc,
            "first_half_acc": first_half_acc,
            "second_half_acc": second_half_acc,
            "avg_comp_len": avg_comp_len,
            "correct_len": correct_len,
            "wrong_len": wrong_len,
            "avg_fmt": avg_fmt,
            "avg_spec": avg_spec,
            "spec_corr": spec_corr,
            "acc_by_len": acc_by_len,
        }},
    }}
    print(json.dumps(result))

elif mode == "numeric":
    import numpy as _np

    all_dfs = []
    for f in files:
        df = pd.read_parquet(f)
        all_dfs.append(df)
    full = pd.concat(all_dfs, ignore_index=True)

    num_df = full.select_dtypes(include="number")
    cols = list(num_df.columns)

    if not cols:
        print(json.dumps({{"error": "No numeric columns found."}}))
        sys.exit(0)

    col_stats = {{}}
    for c in cols:
        s = num_df[c]
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        lo = q1 - 1.5 * iqr
        hi = q3 + 1.5 * iqr
        outliers = int(((s < lo) | (s > hi)).sum())
        col_stats[c] = {{
            "count": int(s.count()),
            "mean": float(s.mean()),
            "std": float(s.std()),
            "min": float(s.min()),
            "25%": float(q1),
            "50%": float(s.median()),
            "75%": float(q3),
            "max": float(s.max()),
            "skew": float(s.skew()),
            "kurtosis": float(s.kurtosis()),
            "zeros": int((s == 0).sum()),
            "nans": int(s.isna().sum()),
            "iqr": float(iqr),
            "outliers": outliers,
        }}

    corr = num_df.corr()
    corr_dict = {{c: {{c2: round(float(corr.loc[c, c2]), 3) for c2 in cols}} for c in cols}}

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor("#1a1a2e")
    fig.suptitle(f"NUMERIC ANALYSIS  |  {{len(cols)}} columns  |  {{len(full)}} rows",
                 color="#e0e0e0", fontsize=14, fontweight="bold")

    def style_ax(ax):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#e0e0e0", labelsize=7)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color("#333")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.yaxis.label.set_color("#e0e0e0")
        ax.xaxis.label.set_color("#e0e0e0")
        ax.title.set_color("#e0e0e0")

    for ax_row in axes:
        for ax in ax_row:
            style_ax(ax)

    ax = axes[0][0]
    plot_cols = cols[:12]  # limit to 12 columns for readability
    z_data = []
    for c in plot_cols:
        s = num_df[c].dropna()
        if s.std() > 0:
            z_data.append(((s - s.mean()) / s.std()).values)
        else:
            z_data.append(s.values)
    bp = ax.boxplot(z_data, labels=[c[:15] for c in plot_cols], patch_artist=True,
                    showfliers=False, medianprops=dict(color="#f72585", linewidth=1.5))
    for patch in bp["boxes"]:
        patch.set_facecolor("#4cc9f066")
        patch.set_edgecolor("#4cc9f0")
    ax.tick_params(axis="x", rotation=45)
    ax.set_title("Z-scored Distributions (box)")
    ax.set_ylabel("Z-score")

    ax = axes[0][1]
    heatmap_cols = cols[:10]  # limit for readability
    corr_matrix = num_df[heatmap_cols].corr().values
    im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(heatmap_cols)))
    ax.set_yticks(range(len(heatmap_cols)))
    ax.set_xticklabels([c[:12] for c in heatmap_cols], rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels([c[:12] for c in heatmap_cols], fontsize=7)
    for i in range(len(heatmap_cols)):
        for j in range(len(heatmap_cols)):
            val = corr_matrix[i, j]
            color = "#000" if abs(val) < 0.5 else "#fff"
            ax.text(j, i, f"{{val:.2f}}", ha="center", va="center", fontsize=6, color=color)
    ax.set_title("Correlation Matrix")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax = axes[1][0]
    variances = {{c: float(num_df[c].var()) for c in cols if num_df[c].var() == num_df[c].var()}}
    top4 = sorted(variances, key=variances.get, reverse=True)[:4]
    colors = ["#4cc9f0", "#f72585", "#4361ee", "#06d6a0"]
    for i, c in enumerate(top4):
        vals = num_df[c].dropna().values
        ax.hist(vals, bins=30, alpha=0.5, color=colors[i], label=c[:15])
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0", fontsize=7)
    ax.set_title("Distributions (top 4 by variance)")
    ax.set_ylabel("Count")

    ax = axes[1][1]
    ax.axis("off")
    lines = [f"Columns: {{len(cols)}}  |  Rows: {{len(full)}}\\n"]
    for c in cols:
        cs = col_stats[c]
        lines.append(f"{{c[:20]:20s}}  μ={{cs['mean']:>9.3f}}  σ={{cs['std']:>8.3f}}  skew={{cs['skew']:>6.2f}}  kurt={{cs['kurtosis']:>6.2f}}  outliers={{cs['outliers']}}")
    ax.text(0.02, 0.98, "\\n".join(lines), transform=ax.transAxes,
            fontsize=7, verticalalignment="top", fontfamily="monospace",
            color="#e0e0e0",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#16213e", edgecolor="#333"))

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode()

    caption = f"Numeric: {{len(cols)}} columns, {{len(full)}} rows\\n"
    top_corrs = []
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i < j:
                top_corrs.append((c1, c2, abs(corr_dict[c1][c2]), corr_dict[c1][c2]))
    top_corrs.sort(key=lambda x: x[2], reverse=True)
    if top_corrs:
        caption += "Top correlations:\\n"
        for c1, c2, _, r in top_corrs[:3]:
            caption += f"  {{c1}} ~ {{c2}}: r={{r:.3f}}\\n"

    result = {{
        "type": "numeric",
        "chart": chart_b64,
        "caption": caption,
        "stats_table": col_stats,
    }}
    print(json.dumps(result))

elif mode == "stats":
    use_files = select_files(files, step_sel) if step_sel else files
    if use_files is None or len(use_files) == 0:
        print(json.dumps({{"error": f"Index out of range. {{len(files)}} files available."}}))
        sys.exit(0)
    trend = []
    for f in use_files:
        df = pd.read_parquet(f)
        trend.append(step_stats(df))
    chart_b64 = render_chart(trend)
    first, last = trend[0], trend[-1]
    acc_first = first["acc_pos"] / first["n"] * 100
    acc_last = last["acc_pos"] / last["n"] * 100
    caption = f"Steps {{first['step']}}-{{last['step']}} ({{len(trend)}} ckpts)\\n"
    caption += f"Accuracy: {{acc_first:.0f}}% -> {{acc_last:.0f}}%\\n"
    caption += f"Format: {{first['fmt_mean']:.3f}} -> {{last['fmt_mean']:.3f}}"
    if "spec_mean" in first:
        caption += f"\\nSpectral: {{first['spec_mean']:.4f}} -> {{last['spec_mean']:.4f}}"
    print(json.dumps({{"type": "stats", "chart": chart_b64, "caption": caption}}))

else:
    selected = select_files(files, step_sel)
    if selected is None or len(selected) == 0:
        print(json.dumps({{"error": f"Index out of range. {{len(files)}} files available."}}))
        sys.exit(0)
    df = pd.read_parquet(selected[0])

    result = {{
        "type": mode,
        "stats": step_stats(df),
        "samples": get_samples(df, count, filt, brief),
        "total_steps": len(files),
    }}
    print(json.dumps(result))
''')
