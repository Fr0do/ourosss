"""Generate and push updated HTML for the ourosss project page."""
import asyncio
import html as html_mod
import json
import logging
import re
from datetime import date
from pathlib import Path

from .vitals import collect_all

logger = logging.getLogger("ourosss")

SITE_REPO = Path.home() / "experiments" / "fr0do.github.io"
OUROBOROS_PAGE = SITE_REPO / "ouroboros" / "index.html"
LANDING_PAGE = SITE_REPO / "index.html"
STATUS_FILE = SITE_REPO / "ouroboros" / "status.json"


async def _git(
    *args: str, cwd: str | None = None, timeout: int = 30,
) -> tuple[int, str]:
    """Run a git subprocess, return (returncode, stdout). Never raises."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or str(SITE_REPO),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode(errors="replace").strip()
        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            logger.warning("git %s failed (rc=%d): %s", " ".join(args), proc.returncode, err)
        return proc.returncode, out
    except asyncio.TimeoutError:
        try:
            proc.kill()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        return -1, ""
    except Exception as exc:
        logger.debug("page._git failed: %s", exc)
        return -1, ""


# ---------------------------------------------------------------------------
# Status entries (stored as JSON, rendered as HTML timeline)
# ---------------------------------------------------------------------------

def _load_status() -> list[dict]:
    """Load status entries from status.json."""
    if STATUS_FILE.is_file():
        try:
            return json.loads(STATUS_FILE.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read status.json: %s", exc)
    return []


def _save_status(entries: list[dict]) -> None:
    """Write status entries to status.json."""
    STATUS_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def add_status_entry(
    title: str,
    body: str = "",
    tag: str = "status",
    entry_date: str | None = None,
) -> dict:
    """Add a new entry to the top of the status timeline. Returns the entry."""
    entries = _load_status()
    entry = {
        "date": entry_date or date.today().isoformat(),
        "title": title,
        "body": body,
        "tag": tag,
    }
    entries.insert(0, entry)
    _save_status(entries)
    return entry


def _render_timeline_html(entries: list[dict]) -> str:
    """Render status entries as HTML timeline divs."""
    lines = ['    <div class="timeline" id="status">']
    for e in entries:
        tag = e.get("tag", "status")
        cls = "timeline-entry milestone" if tag == "milestone" else "timeline-entry"
        d = html_mod.escape(e.get("date", ""))
        t = html_mod.escape(e.get("title", ""))
        b = html_mod.escape(e.get("body", ""))
        lines.append(f'      <div class="{cls}">')
        lines.append(f'        <div class="timeline-date">{d}</div>')
        lines.append(f'        <div class="timeline-title">{t}</div>')
        if b:
            lines.append(f'        <div class="timeline-body">{b}</div>')
        lines.append(f'        <span class="timeline-tag {tag}">{tag}</span>')
        lines.append('      </div>')
    lines.append('    </div>')
    return "\n".join(lines)


def _update_status_section(html: str, entries: list[dict]) -> str:
    """Replace content between STATUS:START and STATUS:END markers."""
    timeline_block = _render_timeline_html(entries)
    pattern = r"(<!-- STATUS:START[^>]*-->)\n.*?\n(    <!-- STATUS:END -->)"
    replacement = rf"\1\n{timeline_block}\n\2"
    return re.sub(pattern, replacement, html, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Vitals HTML
# ---------------------------------------------------------------------------

def _build_vitals_html(data: dict) -> str:
    """Build the HTML block that goes between VITALS:START and VITALS:END."""
    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    commits = git.get("total_commits", 0)
    loc = cb.get("total_loc", 0)
    files = cb.get("total_files", 0)
    handlers = cb.get("handlers", 0)
    services = cb.get("services", 0)
    open_issues = gh.get("open_issues", 0)
    closed_issues = gh.get("closed_issues", 0)
    version = gh.get("latest_release") or "—"

    return (
        '    <div class="metrics-grid" id="vitals">\n'
        '      <div class="metric-card accent-blue">\n'
        f'        <div class="value" id="v-commits">{commits}</div>\n'
        '        <div class="metric-label">Commits (30d)</div>\n'
        '      </div>\n'
        '      <div class="metric-card accent-indigo">\n'
        f'        <div class="value" id="v-loc">{loc}</div>\n'
        '        <div class="metric-label">Lines of Code</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-files">{files}</div>\n'
        '        <div class="metric-label">Python Files</div>\n'
        '      </div>\n'
        '      <div class="metric-card accent-green">\n'
        f'        <div class="value" id="v-handlers">{handlers}</div>\n'
        '        <div class="metric-label">Bot Handlers</div>\n'
        '      </div>\n'
        '      <div class="metric-card">\n'
        f'        <div class="value" id="v-services">{services}</div>\n'
        '        <div class="metric-label">Services</div>\n'
        '      </div>\n'
        '      <div class="metric-card accent-amber">\n'
        f'        <div class="value" id="v-issues-open">{open_issues}</div>\n'
        '        <div class="metric-label">Open Issues</div>\n'
        '      </div>\n'
        '      <div class="metric-card accent-green">\n'
        f'        <div class="value" id="v-issues-closed">{closed_issues}</div>\n'
        '        <div class="metric-label">Closed Issues</div>\n'
        '      </div>\n'
        '      <div class="metric-card accent-indigo">\n'
        f'        <div class="value" id="v-version">{version}</div>\n'
        '        <div class="metric-label">Version</div>\n'
        '      </div>\n'
        '    </div>'
    )


def _update_ouroboros_page(html: str, data: dict) -> str:
    """Replace content between VITALS:START and VITALS:END markers."""
    vitals_block = _build_vitals_html(data)
    pattern = r"(<!-- VITALS:START[^>]*-->)\n.*?\n(    <!-- VITALS:END -->)"
    replacement = rf"\1\n{vitals_block}\n\2"
    return re.sub(pattern, replacement, html, flags=re.DOTALL)


def _update_landing_page(html: str, data: dict) -> str:
    """Update stat divs (stat-commits, stat-loc, stat-issues) on the landing page."""
    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    commits = git.get("total_commits", 0)
    loc = cb.get("total_loc", 0)
    closed_issues = gh.get("closed_issues", 0)

    html = re.sub(
        r'(<div class="number" id="stat-commits">).*?(</div>)',
        rf"\g<1>{commits}\2",
        html,
    )
    html = re.sub(
        r'(<div class="number" id="stat-loc">).*?(</div>)',
        rf"\g<1>{loc}\2",
        html,
    )
    html = re.sub(
        r'(<div class="number" id="stat-issues">).*?(</div>)',
        rf"\g<1>{closed_issues}\2",
        html,
    )
    return html


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

async def update_page(status_entry: dict | None = None) -> str:
    """Collect vitals, optionally add status entry, update HTML, commit & push."""
    data = await collect_all()
    updated_files: list[str] = []

    # Add new status entry if provided
    if status_entry:
        add_status_entry(**status_entry)
        updated_files.append("ouroboros/status.json")

    # Update ouroboros/index.html (vitals + status timeline)
    if OUROBOROS_PAGE.is_file():
        original = OUROBOROS_PAGE.read_text()
        updated = _update_ouroboros_page(original, data)
        # Also update status timeline from JSON
        entries = _load_status()
        if entries:
            updated = _update_status_section(updated, entries)
        if updated != original:
            OUROBOROS_PAGE.write_text(updated)
            updated_files.append("ouroboros/index.html")
    else:
        logger.warning("Ouroboros page not found: %s", OUROBOROS_PAGE)

    # Update landing page index.html
    if LANDING_PAGE.is_file():
        original = LANDING_PAGE.read_text()
        updated = _update_landing_page(original, data)
        if updated != original:
            LANDING_PAGE.write_text(updated)
            updated_files.append("index.html")
    else:
        logger.warning("Landing page not found: %s", LANDING_PAGE)

    if not updated_files:
        return "No changes — pages already up to date."

    # Git add, commit, push
    for f in updated_files:
        await _git("add", f)

    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    if status_entry:
        title = status_entry.get("title", "update")
        msg = f"status: {title}"
    else:
        msg = (
            f"vitals: {git.get('total_commits', '?')} commits, "
            f"{cb.get('total_loc', '?')} LOC, "
            f"{gh.get('open_issues', '?')} open issues"
        )

    rc, _ = await _git("commit", "-m", msg)
    if rc != 0:
        return f"Updated {', '.join(updated_files)} but commit failed."

    rc, out = await _git("push", timeout=60)
    if rc != 0:
        return f"Committed {', '.join(updated_files)} but push failed."

    return f"Updated {', '.join(updated_files)} — pushed.\n{msg}"
