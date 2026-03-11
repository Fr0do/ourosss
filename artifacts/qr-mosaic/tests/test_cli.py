import subprocess
import sys

from PIL import Image


class TestCLIGenerate:
    def test_generate_command(self, tmp_path):
        output = tmp_path / "qr.png"
        result = subprocess.run(
            [
                sys.executable, "-m", "qr_mosaic.cli",
                "generate",
                "--data", "hello-cli-test",
                "--output", str(output),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()
        img = Image.open(str(output))
        assert img.size[0] > 0 and img.size[1] > 0


class TestCLIMosaic:
    def test_mosaic_command(self, tmp_path):
        bg = Image.new("RGB", (512, 512), color=(100, 150, 200))
        bg_path = tmp_path / "background.png"
        bg.save(str(bg_path))

        output = tmp_path / "mosaic.png"
        result = subprocess.run(
            [
                sys.executable, "-m", "qr_mosaic.cli",
                "mosaic",
                "--data", "hello-mosaic-test",
                "--background", str(bg_path),
                "--output", str(output),
                "--opacity", "0.6",
                "--style", "overlay",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()
        img = Image.open(str(output))
        assert img.size == (512, 512)
