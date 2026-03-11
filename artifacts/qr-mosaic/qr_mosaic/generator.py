from io import BytesIO

import qrcode
from PIL import Image
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

ERROR_CORRECTION_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


class QRGenerator:
    def generate(
        self,
        data: str,
        size: int = 512,
        error_correction: str = "H",
    ) -> Image.Image:
        ec_level = ERROR_CORRECTION_MAP.get(error_correction.upper())
        if ec_level is None:
            raise ValueError(
                f"Invalid error correction level '{error_correction}'. "
                f"Must be one of: {', '.join(ERROR_CORRECTION_MAP)}"
            )

        qr = qrcode.QRCode(
            error_correction=ec_level,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img = img.resize((size, size), Image.NEAREST)
        return img

    def generate_bytes(
        self,
        data: str,
        size: int = 512,
        fmt: str = "PNG",
    ) -> bytes:
        img = self.generate(data, size=size)
        buf = BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()
