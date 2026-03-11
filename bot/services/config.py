import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
BOT_TMUX_SESSION = os.getenv("BOT_TMUX_SESSION", "ouro")
GH_BIN = os.getenv("GH_BIN", os.path.expanduser("~/.local/bin/gh"))
NOTION_SECRET = os.getenv("NOTION_SECRET", "")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")

# First run: send /start to bot, copy your user ID here
AUTHORIZED_USERS: set[int] = set()
_raw = os.getenv("AUTHORIZED_USERS", "")
if _raw:
    AUTHORIZED_USERS = {int(x.strip()) for x in _raw.split(",") if x.strip()}

PROJECTS = {
    "s_cot": {
        "remote": "kurkin-1",
        "path": "/workspace-SR004.nfs2/kurkin/s_cot",
        "local": str(Path.home() / "experiments" / "s_cot_tex"),
        "tmux": "cot",
        "conda": "kurkin_313_torch",
        "train_cmd": "bash train.sh",
    },
    "mmred": {
        "remote": "kurkin-1",
        "path": "/workspace-SR004.nfs2/kurkin/mmred",
        "local": str(Path.home() / "experiments" / "mmred"),
        "tmux": "mmred",
        "conda": "kurkin_313_torch",
        "train_cmd": "bash inference.sh",
    },
    "bbbo": {
        "remote": "kurkin-1",
        "path": "/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer",
        "local": None,
        "tmux": "bbbo",
        "conda": "kurkin_313_torch",
        "train_cmd": "python main.py",
    },
}
