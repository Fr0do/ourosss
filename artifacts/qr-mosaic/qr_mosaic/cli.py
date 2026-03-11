import argparse

from .generator import QRGenerator
from .mosaic import MosaicBlender, STYLES


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="qr-mosaic",
        description="Generate QR codes and blend them with images.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    gen_parser = subparsers.add_parser("generate", help="Generate a plain QR code")
    gen_parser.add_argument("--data", required=True, help="Data to encode")
    gen_parser.add_argument("--output", required=True, help="Output image path")
    gen_parser.add_argument("--size", type=int, default=512, help="Image size in pixels")
    gen_parser.add_argument(
        "--error-correction",
        choices=["L", "M", "Q", "H"],
        default="H",
        help="Error correction level",
    )

    # --- mosaic ---
    mos_parser = subparsers.add_parser("mosaic", help="Blend QR code with a background image")
    mos_parser.add_argument("--data", required=True, help="Data to encode in QR")
    mos_parser.add_argument("--background", required=True, help="Background image path")
    mos_parser.add_argument("--output", required=True, help="Output image path")
    mos_parser.add_argument("--size", type=int, default=512, help="QR size in pixels")
    mos_parser.add_argument("--opacity", type=float, default=0.5, help="Blend opacity (0.0-1.0)")
    mos_parser.add_argument(
        "--style",
        choices=list(STYLES),
        default="overlay",
        help="Blending style",
    )

    args = parser.parse_args()

    if args.command == "generate":
        gen = QRGenerator()
        img = gen.generate(
            data=args.data,
            size=args.size,
            error_correction=args.error_correction,
        )
        img.save(args.output)
        print(f"QR code saved to {args.output}")

    elif args.command == "mosaic":
        blender = MosaicBlender()
        blender.blend_from_paths(
            qr_data=args.data,
            bg_path=args.background,
            output_path=args.output,
            opacity=args.opacity,
            style=args.style,
            qr_size=args.size,
        )
        print(f"Mosaic saved to {args.output}")


if __name__ == "__main__":
    main()
