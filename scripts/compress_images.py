#!/usr/bin/env python3
"""
Compress images under a source folder and write optimized copies to a destination folder.

Usage:
  python scripts/compress_images.py --src img --dst img/optimized --quality 85 --png-palette

This script uses Pillow (PIL). It preserves directory structure and does not overwrite
originals unless `--overwrite` is specified.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from PIL import Image


def process_image(src_path: Path, dst_path: Path, quality: int, png_palette: bool, max_width: int | None, max_height: int | None, overwrite: bool) -> bool:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    if dst_path.exists() and not overwrite:
        return False

    try:
        with Image.open(src_path) as im:
            im_format = im.format or src_path.suffix.replace('.', '').upper()

            # Optionally resize if requested
            if max_width or max_height:
                w, h = im.size
                new_w = min(w, max_width) if max_width else w
                new_h = min(h, max_height) if max_height else h
                if new_w != w or new_h != h:
                    im.thumbnail((new_w, new_h), Image.LANCZOS)

            if im_format in ('JPEG', 'JPG'):
                im = im.convert('RGB')
                im.save(dst_path, 'JPEG', quality=quality, optimize=True, progressive=True)
            elif im_format == 'PNG':
                if png_palette:
                    im_conv = im.convert('P', palette=Image.ADAPTIVE)
                    im_conv.save(dst_path, 'PNG', optimize=True)
                else:
                    im.save(dst_path, 'PNG', optimize=True)
            else:
                # For other formats, just copy as-is (Pillow will re-encode)
                im.save(dst_path)
    except Exception as e:
        print(f"Failed: {src_path} -> {dst_path}: {e}")
        return False
    return True


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.webp')


def main() -> None:
    p = argparse.ArgumentParser(description='Compress images recursively')
    p.add_argument('--src', default='img', help='Source images folder')
    p.add_argument('--dst', default='img/optimized', help='Destination folder for optimized images')
    p.add_argument('--quality', type=int, default=85, help='JPEG quality (1-95)')
    p.add_argument('--png-palette', action='store_true', help='Convert PNGs to palette-based (smaller)')
    p.add_argument('--max-width', type=int, default=None, help='Maximum width (pixels) to downscale large images')
    p.add_argument('--max-height', type=int, default=None, help='Maximum height (pixels) to downscale large images')
    p.add_argument('--overwrite', action='store_true', help='Overwrite destination files if they exist')

    args = p.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    if not src.exists():
        print(f"Source folder does not exist: {src}")
        raise SystemExit(1)

    total = 0
    saved = 0
    for root, _, files in os.walk(src):
        for name in files:
            sp = Path(root) / name
            if not is_image_file(sp):
                continue
            rel = sp.relative_to(src)
            dp = dst / rel
            total += 1
            ok = process_image(sp, dp, args.quality, args.png_palette, args.max_width, args.max_height, args.overwrite)
            if ok:
                saved += 1
                print(f"Optimized: {sp} -> {dp}")

    print(f"Processed {total} images, optimized {saved} files written to {dst}")


if __name__ == '__main__':
    main()
