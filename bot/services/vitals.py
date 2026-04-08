"""Project vital stats — git activity, codebase metrics, GitHub."""
import asyncio
import logging
from pathlib import Path

from .config import GH_BIN

logger = logging.getLogger("ourosss")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


async def _run(
    *args: str, cwd: str | None = None, timeout: int = 15,
) -> tuple[int, str]:
    """Run a subprocess, return (returncode, stdout). Never raises."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or str(REPO_ROOT),
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        try:
            proc.kill()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        return -1, ""
    except Exception as exc:
        logger.debug("vitals._run failed: %s", exc)
        return -1, ""


# ---------------------------------------------------------------------------
# 1. Git activity
# ---------------------------------------------------------------------------

async def git_activity(days: int = 30) -> dict:
    """Local git log stats for the last *days* days."""
    result: dict = {}

    # Commits per day
    since = f"--since={days} days ago"
    rc, out = await _run(
        "git", "log", since, "--format=%ad", "--date=short",
    )
    if rc == 0 and out:
        from collections import Counter
        counts = Counter(out.splitlines())
        result["commits_per_day"] = sorted(counts.items())
        result["total_commits"] = sum(counts.values())
    else:
        result["commits_per_day"] = []
        result["total_commits"] = 0

    # LOC added / deleted
    rc, out = await _run(
        "git", "log", since, "--shortstat", "--format=",
    )
    added = deleted = 0
    if rc == 0 and out:
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # "3 files changed, 120 insertions(+), 40 deletions(-)"
            for part in line.split(","):
                part = part.strip()
                if "insertion" in part:
                    try:
                        added += int(part.split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "deletion" in part:
                    try:
                        deleted += int(part.split()[0])
                    except (ValueError, IndexError):
                        pass
    result["loc_added"] = added
    result["loc_deleted"] = deleted

    # Unique authors
    rc, out = await _run(
        "git", "log", since, "--format=%aN",
    )
    if rc == 0 and out:
        result["authors"] = sorted(set(out.splitlines()))
    else:
        result["authors"] = []

    return result


# ---------------------------------------------------------------------------
# 2. Codebase stats
# ---------------------------------------------------------------------------

async def codebase_stats() -> dict:
    """Filesystem metrics for the bot/ directory."""
    bot_dir = REPO_ROOT / "bot"
    result: dict = {}

    try:
        py_files = list(bot_dir.rglob("*.py"))
        result["total_files"] = len(py_files)

        total_loc = 0
        for f in py_files:
            try:
                total_loc += len(f.read_text(errors="replace").splitlines())
            except OSError:
                pass
        result["total_loc"] = total_loc

        handlers_dir = bot_dir / "handlers"
        if handlers_dir.is_dir():
            result["handlers"] = len(
                [p for p in handlers_dir.iterdir() if p.suffix == ".py"]
            )
        else:
            result["handlers"] = 0

        services_dir = bot_dir / "services"
        if services_dir.is_dir():
            result["services"] = len(
                [p for p in services_dir.iterdir() if p.suffix == ".py"]
            )
        else:
            result["services"] = 0

    except Exception as exc:
        logger.warning("codebase_stats error: %s", exc)
        result.setdefault("total_files", 0)
        result.setdefault("total_loc", 0)
        result.setdefault("handlers", 0)
        result.setdefault("services", 0)

    return result


# ---------------------------------------------------------------------------
# 3. GitHub stats (via gh CLI)
# ---------------------------------------------------------------------------

async def github_stats() -> dict:
    """Issue / release info from the gh CLI."""
    result: dict = {}

    # Open issues
    rc_open, out_open = await _run(
        GH_BIN, "issue", "list", "--state=open", "--json=number", "--jq=length",
    )
    # Closed issues
    rc_closed, out_closed = await _run(
        GH_BIN, "issue", "list", "--state=closed", "--json=number", "--jq=length",
    )

    open_n = 0
    closed_n = 0
    if rc_open == 0 and out_open.isdigit():
        open_n = int(out_open)
    if rc_closed == 0 and out_closed.isdigit():
        closed_n = int(out_closed)

    result["open_issues"] = open_n
    result["closed_issues"] = closed_n
    result["total_issues"] = open_n + closed_n

    # Latest release
    rc, out = await _run(
        GH_BIN, "release", "view", "--json=tagName", "--jq=.tagName",
    )
    result["latest_release"] = out if rc == 0 and out else None

    return result


# ---------------------------------------------------------------------------
# 4. Collect all
# ---------------------------------------------------------------------------

async def collect_all() -> dict:
    """Run all vitals collectors in parallel, return combined dict."""
    keys = ("git", "codebase", "github")
    coros = (git_activity(), codebase_stats(), github_stats())

    results = await asyncio.gather(*coros, return_exceptions=True)

    combined: dict = {}
    for key, val in zip(keys, results):
        if isinstance(val, Exception):
            logger.warning("collect_all: %s failed: %s", key, val)
            combined[key] = {"error": str(val)}
        else:
            combined[key] = val

    return combined
