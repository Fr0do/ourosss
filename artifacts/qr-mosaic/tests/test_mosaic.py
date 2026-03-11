import pytest
import numpy as np
from PIL import Image

from qr_mosaic import QRGenerator, MosaicBlender


@pytest.fixture
def blender():
    return MosaicBlender()


@pytest.fixture
def qr_image():
    return QRGenerator().generate("test-mosaic", size=512)


def make_test_background(width=512, height=512):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            arr[y, x] = [
                int(255 * x / width),
                int(255 * y / height),
                128,
            ]
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def background():
    return make_test_background()


class TestBlend:
    def test_blend_overlay(self, blender, qr_image, background):
        result = blender.blend(qr_image, background, style="overlay")
        assert isinstance(result, Image.Image)
        assert result.size == qr_image.size

    def test_blend_halftone(self, blender, qr_image, background):
        result = blender.blend(qr_image, background, style="halftone")
        assert isinstance(result, Image.Image)
        assert result.size == qr_image.size

    def test_blend_artistic(self, blender, qr_image, background):
        result = blender.blend(qr_image, background, style="artistic")
        assert isinstance(result, Image.Image)
        assert result.size == qr_image.size

    def test_blend_opacity_range(self, blender, qr_image, background):
        for opacity in (0.0, 0.5, 1.0):
            result = blender.blend(qr_image, background, opacity=opacity)
            assert isinstance(result, Image.Image)
            assert result.size == qr_image.size

    def test_blend_from_paths(self, blender, tmp_path):
        bg = make_test_background()
        bg_path = tmp_path / "bg.png"
        bg.save(str(bg_path))

        output_path = tmp_path / "output.png"

        result = blender.blend_from_paths(
            qr_data="test-blend-paths",
            bg_path=str(bg_path),
            output_path=str(output_path),
            opacity=0.5,
            style="overlay",
            qr_size=512,
        )

        assert isinstance(result, Image.Image)
        assert output_path.exists()

    def test_invalid_style(self, blender, qr_image, background):
        with pytest.raises(ValueError):
            blender.blend(qr_image, background, style="nonexistent")
