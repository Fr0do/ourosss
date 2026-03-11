import pytest
from PIL import Image

from qr_mosaic import QRGenerator


@pytest.fixture
def gen():
    return QRGenerator()


class TestGenerate:
    def test_generate_returns_image(self, gen):
        img = gen.generate("hello")
        assert isinstance(img, Image.Image)
        assert img.size == (512, 512)

    def test_generate_different_sizes(self, gen):
        for size in (256, 512, 1024):
            img = gen.generate("test", size=size)
            assert img.size == (size, size)

    def test_generate_bytes_png(self, gen):
        data = gen.generate_bytes("test", fmt="PNG")
        assert isinstance(data, bytes)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_generate_bytes_jpeg(self, gen):
        data = gen.generate_bytes("test", fmt="JPEG")
        assert isinstance(data, bytes)
        assert data[:2] == b"\xff\xd8"

    def test_error_correction_levels(self, gen):
        for level in ("L", "M", "Q", "H"):
            img = gen.generate("test", error_correction=level)
            assert isinstance(img, Image.Image)

    def test_generate_url(self, gen):
        img = gen.generate("https://example.com/path?q=1&r=2")
        assert isinstance(img, Image.Image)
        assert img.size == (512, 512)

    def test_generate_long_text(self, gen):
        long_text = "Lorem ipsum dolor sit amet, " * 20
        img = gen.generate(long_text)
        assert isinstance(img, Image.Image)
        assert img.size == (512, 512)
