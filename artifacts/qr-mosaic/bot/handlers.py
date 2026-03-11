import io
import logging
import shlex
import sys
from pathlib import Path

from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qr_mosaic import MosaicBlender, QRGenerator

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Welcome to QR Mosaic Bot!\n\n"
    "I generate QR codes and blend them with images.\n\n"
    "Commands:\n"
    "/qr <text> \u2014 generate a plain QR code\n"
    "Send a photo with a caption \u2014 generate a QR mosaic\n"
    "/help \u2014 usage instructions"
)

HELP_TEXT = (
    "Usage:\n\n"
    "/qr <text>\n"
    "  Generate a simple QR code encoding the given text.\n\n"
    "Send a photo with caption:\n"
    "  The caption text is encoded as a QR code, then blended\n"
    "  over your photo as a mosaic.\n\n"
    "  Optional flags at the start of the caption:\n"
    "    --style <halftone|artistic>  (default: halftone)\n"
    "    --opacity <0.0-1.0>         (default: 0.5)\n\n"
    "  Example caption:\n"
    "    --style artistic --opacity 0.7 https://example.com"
)

DEFAULT_OPACITY = 0.5
DEFAULT_STYLE = "halftone"


def _parse_caption(caption: str) -> tuple[str, str, float]:
    """Extract optional flags from caption, return (data, style, opacity)."""
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /qr <text>\nExample: /qr https://example.com")
        return

    data = " ".join(context.args)

    try:
        generator = QRGenerator()
        qr_img = generator.generate(data)
        buf = _image_to_bytes(qr_img)
        await update.message.reply_photo(photo=buf, caption=f"QR: {data[:100]}")
    except Exception:
        logger.exception("Failed to generate QR code")
        await update.message.reply_text("Failed to generate QR code. Please try shorter text.")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caption = update.message.caption
    if not caption:
        await update.message.reply_text(
            "Send a photo with a caption to create a QR mosaic.\n"
            "The caption text will be encoded as a QR code."
        )
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

        generator = QRGenerator()
        qr_img = generator.generate(data)

        blender = MosaicBlender()
        mosaic = blender.blend(
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
