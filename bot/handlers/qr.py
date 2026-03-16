"""
/qr — generate QR codes and QR mosaics from Telegram.

Usage:
  /qr <text>          — generate a plain QR code
  Send photo+caption  — blend QR code over the image as a mosaic

Caption flags (optional, before the text):
  --style <halftone|artistic>  (default: halftone)
  --opacity <0.0-1.0>         (default: 0.5)
"""
import io
import logging
import shlex
import sys
from pathlib import Path

from PIL import Image
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..services.tg import authorized

# Make qr_mosaic library importable (optional — missing on fresh clones)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "artifacts" / "qr-mosaic"))
try:
    from qr_mosaic import MosaicBlender, QRGenerator
except ImportError:
    MosaicBlender = None  # type: ignore[assignment,misc]
    QRGenerator = None  # type: ignore[assignment,misc]

logger = logging.getLogger("ourosss")

DEFAULT_OPACITY = 0.5
DEFAULT_STYLE = "halftone"


def _parse_caption(caption: str) -> tuple[str, str, float]:
    """Extract optional --style/--opacity flags from caption."""
    style = DEFAULT_STYLE
    opacity = DEFAULT_OPACITY

    if not caption.startswith("--"):
        return caption, style, opacity

    try:
        tokens = shlex.split(caption)
    except ValueError:
        return caption, style, opacity

    data_start = 0
    i = 0
    while i < len(tokens):
        if tokens[i] == "--style" and i + 1 < len(tokens):
            style = tokens[i + 1]
            i += 2
            data_start = i
        elif tokens[i] == "--opacity" and i + 1 < len(tokens):
            try:
                opacity = float(tokens[i + 1])
                opacity = max(0.0, min(1.0, opacity))
            except ValueError:
                pass
            i += 2
            data_start = i
        else:
            break

    data = " ".join(tokens[data_start:])
    return data, style, opacity


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


@authorized
async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/qr <text> — generate a plain QR code."""
    if not context.args:
        await update.message.reply_text("Usage: /qr <text>\nExample: /qr https://example.com")
        return

    data = " ".join(context.args)

    if QRGenerator is None:
        await update.message.reply_text("QR module not installed (qr_mosaic missing).")
        return

    try:
        qr_img = QRGenerator().generate(data)
        buf = _image_to_bytes(qr_img)
        await update.message.reply_photo(photo=buf, caption=f"QR: {data[:100]}")
    except Exception:
        logger.exception("Failed to generate QR code")
        await update.message.reply_text("Failed to generate QR code. Please try shorter text.")


@authorized
async def photo_mosaic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Photo + caption — blend QR code over the image as a mosaic."""
    caption = update.message.caption
    if not caption:
        return  # Ignore photos without captions (don't hijack all photo messages)

    if MosaicBlender is None:
        await update.message.reply_text("QR mosaic module not installed (qr_mosaic missing).")
        return

    data, style, opacity = _parse_caption(caption)
    if not data:
        await update.message.reply_text("Caption must contain text to encode as QR.")
        return

    status_msg = await update.message.reply_text("Generating mosaic...")

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        img_bytes = await file.download_as_bytearray()
        background = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        qr_img = QRGenerator().generate(data)
        mosaic = MosaicBlender().blend(
            background=background,
            qr_image=qr_img,
            opacity=opacity,
            style=style,
        )

        buf = _image_to_bytes(mosaic)
        await update.message.reply_photo(
            photo=buf,
            caption=f"QR mosaic ({style}, opacity {opacity})",
        )
        await status_msg.delete()
    except Exception:
        logger.exception("Failed to generate mosaic")
        try:
            await status_msg.edit_text("Failed to generate mosaic. Please try again.")
        except Exception:
            await update.message.reply_text("Failed to generate mosaic. Please try again.")


handler = CommandHandler("qr", qr_command)
photo_handler = MessageHandler(
    filters.PHOTO & filters.Caption(), photo_mosaic_handler
)
