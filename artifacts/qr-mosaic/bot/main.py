import argparse
import logging
import os
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler, MessageHandler, filters

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bot.handlers import help_command, photo_handler, qr_command, start_command

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _load_token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass

    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token:
        logger.error("TELEGRAM_TOKEN not set")
        sys.exit(1)
    return token


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QR Mosaic Telegram Bot")
    parser.add_argument(
        "--webhook",
        action="store_true",
        help="Run in webhook mode (requires WEBHOOK_URL env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8443,
        help="Port for webhook server (default: 8443)",
    )
    return parser.parse_args()


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("qr", qr_command))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    return app


def main() -> None:
    args = _parse_args()
    token = _load_token()
    app = build_app(token)

    if args.webhook:
        webhook_url = os.environ.get("WEBHOOK_URL", "")
        if not webhook_url:
            logger.error("WEBHOOK_URL not set for webhook mode")
            sys.exit(1)
        logger.info("Starting webhook on port %d", args.port)
        app.run_webhook(
            listen="0.0.0.0",
            port=args.port,
            webhook_url=webhook_url,
        )
    else:
        logger.info("Starting polling")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
