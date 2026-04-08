
def _fmt_stats_header(s: dict) -> str:
    """Format a step stats dict into a compact header."""
    lines = [f"Step {s['step']} -- {s['n']} completions"]
    lines.append(f"  Accuracy:  mean={s['acc_mean']:.2f}  +1={s['acc_pos']}  -1={s['acc_neg']}")
    lines.append(f"  Format:    mean={s['fmt_mean']:.3f}  [{s['fmt_min']:.2f}, {s['fmt_max']:.2f}]")
    if "spec_mean" in s:
        lines.append(f"  Spectral:  mean={s['spec_mean']:.4f}")
    lines.append(f"  Advantage: mean={s['adv_mean']:.3f}  std={s['adv_std']:.3f}")
    return "\n".join(lines)


def _fmt_sample_brief(s: dict) -> str:
    """Format a sample as a brief inline block."""
    tag = "+" if s["acc"] == 1.0 else "-"
    reward = f"acc={s['acc']:.0f} fmt={s['fmt']:.2f}"
    if "spec" in s:
        reward += f" spec={s['spec']:.3f}"
    comp = s["completion"].replace("\n", " ")[:500]
    return f"[{tag}] {reward}\n{comp}"


def _fmt_trace(s: dict, idx: int) -> str:
    """Format a full trace for a separate message."""
    tag = "+" if s["acc"] == 1.0 else "-"
    header = f"[{tag}] acc={s['acc']:.0f} fmt={s['fmt']:.2f}"
    if "spec" in s:
        header += f" spec={s['spec']:.3f}"
    header += f" adv={s['adv']:.3f}"

    # Extract the user portion of the prompt (skip system message)
    prompt = s["prompt"]
    user_start = prompt.find("\nuser\n")
    if user_start >= 0:
        prompt = prompt[user_start + 6:]
    assistant_start = prompt.find("\nassistant\n")
    if assistant_start >= 0:
        prompt = prompt[:assistant_start]
    prompt = prompt.strip()

    parts = [f"--- Trace {idx} {header} ---", f"PROMPT: {prompt}", f"\n{s['completion']}"]
    return "\n".join(parts)
