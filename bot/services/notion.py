"""
Notion integration for s_cot eval tracking and research log.

Connects to Notion databases to store and query evaluation results
and collaborator-facing research log entries.
Requires NOTION_SECRET and NOTION_DB_ID in .env.
Optional: NOTION_RESEARCH_DB_ID for research log.
"""
import logging
from datetime import datetime, timezone

from .config import NOTION_SECRET, NOTION_DB_ID, NOTION_RESEARCH_DB_ID

logger = logging.getLogger("ourosss")

BENCHMARKS = {
    "json_pathfinder",
    "nlgraph_shortest_path",
    "reasoning_gym",
    "nlgraph_connectivity",
}

TOPOLOGIES = {"erdos_renyi", "power_law", "mixed"}

MODELS = {"LFM2.5-1.2B-Thinking", "Qwen3-1.7B"}


RESEARCH_PROJECTS = {"s_cot", "mmred", "bbbo", "ourosss"}
RESEARCH_TYPES = {"finding", "milestone", "progress", "experiment", "decision"}
RESEARCH_STATUSES = {"active", "completed", "blocked", "archived"}


def _get_client():
    """Return a Notion client, or None if not configured."""
    if not NOTION_SECRET or not NOTION_DB_ID:
        return None
    from notion_client import Client
    return Client(auth=NOTION_SECRET)


def _get_research_client():
    """Return a Notion client for the research log DB, or None if not configured."""
    if not NOTION_SECRET or not NOTION_RESEARCH_DB_ID:
        return None
    from notion_client import Client
    return Client(auth=NOTION_SECRET)


def push_eval_result(
    checkpoint: str,
    step: int,
    benchmark: str,
    topology: str,
    accuracy: float,
    valid_format_pct: float,
    avg_completion_len: float,
    model: str,
    notes: str = "",
) -> dict | None:
    """Create a new eval result entry in Notion. Returns the created page or None."""
    client = _get_client()
    if client is None:
        return None

    properties = {
        "Checkpoint": {"title": [{"text": {"content": checkpoint}}]},
        "Step": {"number": step},
        "Benchmark": {"select": {"name": benchmark}},
        "Topology": {"select": {"name": topology}},
        "Accuracy": {"number": accuracy},
        "Valid Format %": {"number": valid_format_pct},
        "Avg Completion Length": {"number": avg_completion_len},
        "Model": {"select": {"name": model}},
        "Notes": {"rich_text": [{"text": {"content": notes}}] if notes else []},
        "Date": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
    }

    page = client.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties=properties,
    )
    logger.info(f"Notion: created eval entry for {checkpoint} / {benchmark}")
    return page


def get_recent_evals(limit: int = 10) -> list[dict]:
    """Query recent eval results from the Notion database."""
    client = _get_client()
    if client is None:
        return []

    response = client.databases.query(
        database_id=NOTION_DB_ID,
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=min(limit, 100),
    )

    results = []
    for page in response.get("results", []):
        props = page["properties"]
        results.append({
            "checkpoint": _get_title(props.get("Checkpoint", {})),
            "step": props.get("Step", {}).get("number"),
            "benchmark": _get_select(props.get("Benchmark", {})),
            "topology": _get_select(props.get("Topology", {})),
            "accuracy": props.get("Accuracy", {}).get("number"),
            "valid_format_pct": props.get("Valid Format %", {}).get("number"),
            "avg_completion_len": props.get("Avg Completion Length", {}).get("number"),
            "model": _get_select(props.get("Model", {})),
            "notes": _get_rich_text(props.get("Notes", {})),
            "date": _get_date(props.get("Date", {})),
        })
    return results


def format_eval_summary(results: list[dict]) -> str:
    """Format eval results as a Telegram-friendly markdown string."""
    if not results:
        return "No eval results found."

    lines = ["*Recent Eval Results*\n"]
    for r in results:
        acc = f"{r['accuracy']:.1%}" if r["accuracy"] is not None else "n/a"
        fmt = f"{r['valid_format_pct']:.1%}" if r["valid_format_pct"] is not None else "n/a"
        avg_len = f"{r['avg_completion_len']:.0f}" if r["avg_completion_len"] is not None else "n/a"
        lines.append(
            f"  {r['checkpoint']} | {r['benchmark']}\n"
            f"  acc={acc}  fmt={fmt}  len={avg_len}\n"
            f"  {r['model']} | {r['topology']} | {r['date'] or ''}\n"
        )
    return "\n".join(lines)


# -- Research Log --

def push_research_log(
    project: str,
    type: str,
    title: str,
    summary: str,
    metrics: str = "",
    status: str = "active",
) -> dict | None:
    """Create a new research log entry in Notion. Returns the created page or None."""
    client = _get_research_client()
    if client is None:
        return None

    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Project": {"select": {"name": project}},
        "Type": {"select": {"name": type}},
        "Summary": {"rich_text": [{"text": {"content": summary}}]},
        "Metrics": {"rich_text": [{"text": {"content": metrics}}] if metrics else []},
        "Date": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
        "Status": {"status": {"name": status}},
    }

    page = client.pages.create(
        parent={"database_id": NOTION_RESEARCH_DB_ID},
        properties=properties,
    )
    logger.info(f"Notion: created research log entry '{title}' [{project}/{type}]")
    return page


def get_research_log(project: str | None = None, limit: int = 10) -> list[dict]:
    """Query recent research log entries, optionally filtered by project."""
    client = _get_research_client()
    if client is None:
        return []

    filter_obj = None
    if project:
        filter_obj = {"property": "Project", "select": {"equals": project}}

    kwargs = dict(
        database_id=NOTION_RESEARCH_DB_ID,
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=min(limit, 100),
    )
    if filter_obj:
        kwargs["filter"] = filter_obj

    response = client.databases.query(**kwargs)

    results = []
    for page in response.get("results", []):
        props = page["properties"]
        results.append({
            "title": _get_title(props.get("Title", {})),
            "project": _get_select(props.get("Project", {})),
            "type": _get_select(props.get("Type", {})),
            "summary": _get_rich_text(props.get("Summary", {})),
            "metrics": _get_rich_text(props.get("Metrics", {})),
            "date": _get_date(props.get("Date", {})),
            "status": _get_status(props.get("Status", {})),
        })
    return results


def format_research_log(entries: list[dict]) -> str:
    """Format research log entries as a Telegram-friendly markdown string."""
    if not entries:
        return "No research log entries found."

    lines = ["*Research Log*\n"]
    for e in entries:
        metrics_line = f"\n  metrics: {e['metrics']}" if e["metrics"] else ""
        lines.append(
            f"*{e['title']}*\n"
            f"  {e['project']} | {e['type']} | {e['status']} | {e['date'] or ''}\n"
            f"  {e['summary']}"
            f"{metrics_line}\n"
        )
    return "\n".join(lines)


# -- Property extraction helpers --

def _get_title(prop: dict) -> str:
    title_list = prop.get("title", [])
    return title_list[0]["text"]["content"] if title_list else ""


def _get_select(prop: dict) -> str:
    sel = prop.get("select")
    return sel["name"] if sel else ""


def _get_rich_text(prop: dict) -> str:
    rt_list = prop.get("rich_text", [])
    return rt_list[0]["text"]["content"] if rt_list else ""


def _get_status(prop: dict) -> str:
    status = prop.get("status")
    return status["name"] if status else ""


def _get_date(prop: dict) -> str:
    date = prop.get("date")
    return date["start"] if date else ""
