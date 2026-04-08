import base64
import io


async def _send_chart(update, data: dict) -> None:
    img_bytes = base64.b64decode(data["chart"])
    await update.message.reply_photo(
        photo=io.BytesIO(img_bytes),
        caption=data.get("caption", ""),
    )
