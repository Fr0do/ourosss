
def _parse_step(raw: str) -> dict:
    """Parse a Python-style index or slice string.

    Returns {"index": int} for single index, or
    {"slice": [start|None, stop|None, step|None]} for slices.
    """
    if ":" in raw:
        parts = raw.split(":")
        def _int_or_none(s):
            s = s.strip()
            return int(s) if s else None
        if len(parts) == 2:
            return {"slice": [_int_or_none(parts[0]), _int_or_none(parts[1]), None]}
        elif len(parts) == 3:
            return {"slice": [_int_or_none(parts[0]), _int_or_none(parts[1]), _int_or_none(parts[2])]}
        raise ValueError(f"Invalid slice: {raw}")
    return {"index": int(raw)}


def _parse_flags(args: list[str]) -> dict:
    """Parse flexible flag list into options dict."""
    opts = {
        "mode": "dashboard",  # dashboard | stats | traces
        "step": None,         # {"index": N} or {"slice": [start, stop, step]} or None
        "last": None,         # last N steps (stats mode) — shorthand for step -N:
        "count": 3,           # number of samples
        "filter": None,       # correct | wrong | None
        "brief": None,        # True/False/None (auto)
    }
    i = 0
    while i < len(args):
        a = args[i].lower()
        if a == "stats":
            opts["mode"] = "stats"
        elif a == "baseline":
            opts["mode"] = "baseline"
        elif a == "numeric":
            opts["mode"] = "numeric"
        elif a == "traces":
            opts["mode"] = "traces"
        elif a == "correct":
            opts["filter"] = "correct"
        elif a == "wrong":
            opts["filter"] = "wrong"
        elif a == "brief":
            opts["brief"] = True
        elif a == "step" and i + 1 < len(args):
            i += 1
            try:
                opts["step"] = _parse_step(args[i])
            except (ValueError, IndexError):
                pass  # ignore malformed step, use default
        elif a == "last" and i + 1 < len(args):
            i += 1
            opts["last"] = int(args[i])
        elif a.isdigit():
            opts["count"] = int(a)
        i += 1
    # `last N` is shorthand for `step -N:`
    if opts["last"] and opts["step"] is None:
        opts["step"] = {"slice": [-opts["last"], None, None]}
    # Auto-brief: dashboard=brief, traces=full
    if opts["brief"] is None:
        opts["brief"] = opts["mode"] != "traces"
    return opts
