#!/usr/bin/env python3
"""Turn a photo into ASCII art for a GitHub profile README. Standard library only.

    image-to-ascii.py photo.png                    # braille portrait, 40 chars wide
    image-to-ascii.py photo.png --width 36 --mode ascii
    image-to-ascii.py photo.png --invert           # for light-background READMEs
    image-to-ascii.py photo.png --contrast 1.4 --threshold 0.5

Modes:
  braille  each character holds a 2x4 dot grid (U+2800 block): the most detail; renders
           well in GitHub code blocks.
  ascii    classic ramp " .:-=+*#%@": works everywhere, less detail.

Input: PNG (8-bit RGB/RGBA/gray, non-interlaced). Other formats are converted first with
`sips` (macOS), `magick` (ImageMagick) or Pillow if one is available. Transparent pixels
count as background, so cut the person out first for a clean portrait (see cutout.swift).
Output: plain text on stdout, ready for a ```text block.
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib


# ---------- loading ----------

def to_png(path):
    if path.lower().endswith(".png"):
        return path
    out = os.path.join(tempfile.mkdtemp(), "in.png")
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "png", path, "--out", out], check=True, capture_output=True)
        return out
    if shutil.which("magick"):
        subprocess.run(["magick", path, out], check=True)
        return out
    try:
        from PIL import Image  # type: ignore
        Image.open(path).save(out)
        return out
    except ImportError:
        sys.exit("error: input isn't PNG and no converter found (install ImageMagick or Pillow, or pass a .png)")


def read_png(path):
    """Return (width, height, rows) with rows of (luma 0..1, alpha 0..1) tuples."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("error: not a PNG file")
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace:
                sys.exit("error: only 8-bit, non-interlaced PNG is supported; re-save the image")
        elif typ == b"PLTE":
            sys.exit("error: palette PNGs aren't supported; re-save as RGB")
        elif typ == b"IDAT":
            idat += body
        pos += n + 12
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * ch
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        px = []
        for x in range(w):
            v = line[x * ch:(x + 1) * ch]
            if ch in (1, 2):
                luma = v[0] / 255
            else:
                luma = (0.299 * v[0] + 0.587 * v[1] + 0.114 * v[2]) / 255
            alpha = (v[-1] / 255) if ch in (2, 4) else 1.0
            px.append((luma, alpha))
        rows.append(px)
    return w, h, rows


def resample(rows, w, h, tw, th):
    """Box-filter resize to tw x th; returns luma grid where background (alpha 0) -> None."""
    out = []
    for ty in range(th):
        y0, y1 = int(ty * h / th), max(int((ty + 1) * h / th), int(ty * h / th) + 1)
        line = []
        for tx in range(tw):
            x0, x1 = int(tx * w / tw), max(int((tx + 1) * w / tw), int(tx * w / tw) + 1)
            s = a = 0.0; n = 0
            for yy in range(y0, min(y1, h)):
                for xx in range(x0, min(x1, w)):
                    l, al = rows[yy][xx]; s += l * al; a += al; n += 1
            line.append(None if a / max(n, 1) < 0.5 else s / a)
        out.append(line)
    return out


# ---------- rendering ----------

def braille(grid, threshold, invert):
    h, w = len(grid), len(grid[0])
    # dots are "ink": dark pixels on a dark terminal read as light, so ink = bright by default
    val = [[(0.0 if v is None else (1 - v if invert else v)) for v in row] for row in grid]
    ink = [[False] * w for _ in range(h)]
    for y in range(h):  # Floyd–Steinberg dithering
        for x in range(w):
            old = val[y][x]
            on = old >= threshold and grid[y][x] is not None
            ink[y][x] = on
            err = old - (1.0 if on else 0.0)
            for dx, dy, k in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] is not None:
                    val[ny][nx] += err * k
    bits = ((0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80))
    lines = []
    for cy in range(0, h - 3, 4):
        s = []
        for cx in range(0, w - 1, 2):
            code = 0
            for dx, dy, b in bits:
                if ink[cy + dy][cx + dx]:
                    code |= b
            s.append(chr(0x2800 + code))  # blank cells stay U+2800 so code blocks keep their width
        lines.append("".join(s))
    return lines


def ramp(grid, invert):
    chars = " .:-=+*#%@"
    out = []
    for row in grid:
        s = ""
        for v in row:
            if v is None:
                s += " "
                continue
            t = v if invert else 1 - v
            s += chars[min(int(t * len(chars)), len(chars) - 1)]
        out.append(s.rstrip())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--width", type=int, default=40, help="output width in characters (default 40)")
    ap.add_argument("--mode", choices=["braille", "ascii"], default="braille")
    ap.add_argument("--invert", action="store_true", help="for light backgrounds")
    ap.add_argument("--contrast", type=float, default=1.25)
    ap.add_argument("--threshold", type=float, default=0.5)
    a = ap.parse_args()

    w, h, rows = read_png(to_png(a.image))
    # stretch contrast around the subject's mean brightness
    vals = [l for r in rows for (l, al) in r if al > 0.5] or [0.5]
    mean = sum(vals) / len(vals)
    rows = [[(min(max((l - mean) * a.contrast + 0.5, 0), 1), al) for (l, al) in r] for r in rows]

    if a.mode == "braille":
        tw = a.width * 2
        th = int(tw * h / w)  # braille dots are roughly square
        th -= th % 4
        lines = braille(resample(rows, w, h, tw, th), a.threshold, a.invert)
    else:
        tw = a.width
        th = max(int(tw * h / w * 0.5), 1)  # terminal cells are about 2:1
        lines = ramp(resample(rows, w, h, tw, th), a.invert)
    while lines and not lines[-1].strip("⠀ "):
        lines.pop()
    while lines and not lines[0].strip("⠀ "):
        lines.pop(0)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
