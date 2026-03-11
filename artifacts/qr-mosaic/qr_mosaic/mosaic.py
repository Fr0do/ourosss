from typing import Tuple

import numpy as np
from PIL import Image

from .generator import QRGenerator

STYLES = ("overlay", "halftone", "artistic")


class MosaicBlender:
    def __init__(self) -> None:
        self._generator = QRGenerator()

    def blend(
        self,
        qr_image: Image.Image,
        background: Image.Image,
        opacity: float = 0.5,
        style: str = "overlay",
    ) -> Image.Image:
        if style not in STYLES:
            raise ValueError(f"Unknown style '{style}'. Must be one of: {', '.join(STYLES)}")

        opacity = max(0.0, min(1.0, opacity))
        size = qr_image.size[0]
        bg = background.convert("RGB").resize((size, size), Image.LANCZOS)
        qr = qr_image.convert("RGB")

        if style == "overlay":
            return self._blend_overlay(qr, bg, opacity)
        elif style == "halftone":
            return self._blend_halftone(qr, bg, opacity)
        else:
            return self._blend_artistic(qr, bg, opacity)

    def blend_from_paths(
        self,
        qr_data: str,
        bg_path: str,
        output_path: str,
        opacity: float = 0.5,
        style: str = "overlay",
        qr_size: int = 512,
    ) -> Image.Image:
        qr_image = self._generator.generate(qr_data, size=qr_size)
        background = Image.open(bg_path)
        result = self.blend(qr_image, background, opacity=opacity, style=style)
        result.save(output_path)
        return result

    def _blend_overlay(
        self,
        qr: Image.Image,
        bg: Image.Image,
        opacity: float,
    ) -> Image.Image:
        return Image.blend(bg, qr, alpha=opacity)

    def _blend_halftone(
        self,
        qr: Image.Image,
        bg: Image.Image,
        opacity: float,
    ) -> Image.Image:
        qr_gray = np.array(qr.convert("L"))
        bg_arr = np.array(bg, dtype=np.float64)
        size = qr.size[0]

        # Detect module grid from the QR image.
        # Scan the first row to find transitions and infer module size.
        module_size = self._detect_module_size(qr_gray, size)
        modules_count = size // module_size

        result = np.array(bg, dtype=np.float64).copy()

        for row in range(modules_count):
            for col in range(modules_count):
                y0 = row * module_size
                x0 = col * module_size
                y1 = min(y0 + module_size, size)
                x1 = min(x0 + module_size, size)

                region = bg_arr[y0:y1, x0:x1]
                center = qr_gray[y0 + module_size // 2, x0 + module_size // 2]
                is_dark = center < 128

                if is_dark:
                    factor = 1.0 - opacity * 0.7
                    result[y0:y1, x0:x1] = region * factor
                else:
                    factor = 1.0 + opacity * 0.5
                    result[y0:y1, x0:x1] = np.minimum(region * factor, 255.0)

        return Image.fromarray(result.astype(np.uint8))

    def _blend_artistic(
        self,
        qr: Image.Image,
        bg: Image.Image,
        opacity: float,
    ) -> Image.Image:
        dark_color, light_color = self._extract_dominant_pair(bg)

        qr_gray = np.array(qr.convert("L"))

        # Build a color-mapped QR using the dominant palette.
        dark = np.array(dark_color, dtype=np.uint8)
        light = np.array(light_color, dtype=np.uint8)
        mask = (qr_gray < 128).astype(np.float64)

        colored_qr = np.zeros((*qr_gray.shape, 3), dtype=np.float64)
        for c in range(3):
            colored_qr[:, :, c] = mask * dark[c] + (1.0 - mask) * light[c]

        # Add subtle texture from background.
        bg_arr = np.array(bg, dtype=np.float64)
        bg_texture = bg_arr - bg_arr.mean()
        texture_strength = (1.0 - opacity) * 0.3

        result = colored_qr + bg_texture * texture_strength
        result = np.clip(result, 0, 255)

        return Image.fromarray(result.astype(np.uint8))

    def _detect_module_size(self, qr_gray: np.ndarray, size: int) -> int:
        # Sample the middle row and find runs of same-value pixels.
        mid = size // 2
        row = qr_gray[mid, :]
        binary = (row < 128).astype(np.uint8)

        run_lengths: list[int] = []
        current = binary[0]
        length = 1
        for i in range(1, len(binary)):
            if binary[i] == current:
                length += 1
            else:
                run_lengths.append(length)
                current = binary[i]
                length = 1
        run_lengths.append(length)

        if not run_lengths:
            return max(1, size // 21)

        # Module size is the GCD-like smallest common run length.
        # Use median of small runs as estimate.
        run_lengths.sort()
        min_run = run_lengths[0]
        return max(1, min_run)

    def _extract_dominant_pair(
        self,
        image: Image.Image,
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        # Downsample for speed, quantize to find dominant colors.
        small = image.resize((64, 64), Image.LANCZOS)
        pixels = np.array(small).reshape(-1, 3).astype(np.float64)

        # Simple k=2 clustering: split by luminance.
        lum = 0.299 * pixels[:, 0] + 0.587 * pixels[:, 1] + 0.114 * pixels[:, 2]
        median_lum = np.median(lum)

        dark_mask = lum <= median_lum
        light_mask = ~dark_mask

        if dark_mask.sum() == 0:
            dark_color = (0, 0, 0)
        else:
            dark_color = tuple(int(v) for v in pixels[dark_mask].mean(axis=0))

        if light_mask.sum() == 0:
            light_color = (255, 255, 255)
        else:
            light_color = tuple(int(v) for v in pixels[light_mask].mean(axis=0))

        return dark_color, light_color  # type: ignore[return-value]
