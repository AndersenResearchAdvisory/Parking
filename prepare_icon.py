#!/usr/bin/env python3

import math
import struct
import sys
import zlib
from pathlib import Path


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png_rgba(path: Path):
    data = path.read_bytes()
    if not data.startswith(PNG_SIG):
        raise ValueError("Input is not a PNG file.")

    pos = len(PNG_SIG)
    width = height = None
    bit_depth = color_type = None
    idat_parts = []

    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("Invalid PNG structure.")
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        start = pos + 8
        end = start + length
        chunk_data = data[start:end]
        pos = end + 4  # skip CRC

        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif ctype == b"IDAT":
            idat_parts.append(chunk_data)
        elif ctype == b"IEND":
            break

    if width is None or height is None:
        raise ValueError("Missing IHDR.")
    if bit_depth != 8:
        raise ValueError("Only 8-bit PNG files are supported.")
    if color_type not in (6, 2):
        raise ValueError("Only RGB/RGBA PNG files are supported.")

    compressed = b"".join(idat_parts)
    raw = zlib.decompress(compressed)

    bpp = 4 if color_type == 6 else 3
    stride = width * bpp
    rows = []
    i = 0
    prev = bytearray(stride)

    for _ in range(height):
        f = raw[i]
        i += 1
        row = bytearray(raw[i : i + stride])
        i += stride

        if f == 1:  # Sub
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + left) & 0xFF
        elif f == 2:  # Up
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif f == 3:  # Average
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                up = prev[x]
                row[x] = (row[x] + ((left + up) // 2)) & 0xFF
        elif f == 4:  # Paeth
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + paeth(a, b, c)) & 0xFF
        elif f != 0:
            raise ValueError(f"Unsupported PNG filter type: {f}")

        prev = row
        rows.append(row)

    rgba_rows = []
    if color_type == 6:
        rgba_rows = rows
    else:
        for row in rows:
            out = bytearray(width * 4)
            for x in range(width):
                src = x * 3
                dst = x * 4
                out[dst] = row[src]
                out[dst + 1] = row[src + 1]
                out[dst + 2] = row[src + 2]
                out[dst + 3] = 255
            rgba_rows.append(out)

    return width, height, rgba_rows


def find_alpha_bounds(width: int, height: int, rows):
    min_x, min_y = width, height
    max_x, max_y = -1, -1

    for y in range(height):
        row = rows[y]
        for x in range(width):
            a = row[x * 4 + 3]
            if a > 0:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x == -1:
        return 0, 0, width - 1, height - 1
    return min_x, min_y, max_x, max_y


def crop_rows(rows, min_x, min_y, max_x, max_y):
    out = []
    for y in range(min_y, max_y + 1):
        row = rows[y]
        start = min_x * 4
        end = (max_x + 1) * 4
        out.append(bytearray(row[start:end]))
    return out


def center_on_square(rows, content_w: int, content_h: int, margin_ratio: float):
    scale_area = max(0.1, min(0.95, 1.0 - (2 * margin_ratio)))
    side = max(content_w, content_h)
    canvas = int(math.ceil(side / scale_area))
    canvas = max(canvas, side)

    x_off = (canvas - content_w) // 2
    y_off = (canvas - content_h) // 2

    out = [bytearray(canvas * 4) for _ in range(canvas)]

    for y in range(content_h):
        src = rows[y]
        dst = out[y + y_off]
        start = x_off * 4
        dst[start : start + len(src)] = src

    return canvas, canvas, out


def write_png_rgba(path: Path, width: int, height: int, rows):
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type 0 (None)
        raw.extend(row)
    idat = zlib.compress(bytes(raw), 9)

    png = bytearray(PNG_SIG)
    png.extend(chunk(b"IHDR", ihdr))
    png.extend(chunk(b"IDAT", idat))
    png.extend(chunk(b"IEND", b""))
    path.write_bytes(png)


def main():
    if len(sys.argv) not in (3, 4):
        print("Usage: prepare_icon.py <input.png> <output.png> [margin_ratio]")
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    margin = float(sys.argv[3]) if len(sys.argv) == 4 else 0.14

    w, h, rows = read_png_rgba(src)
    min_x, min_y, max_x, max_y = find_alpha_bounds(w, h, rows)
    cropped = crop_rows(rows, min_x, min_y, max_x, max_y)
    cw = max_x - min_x + 1
    ch = max_y - min_y + 1
    out_w, out_h, centered = center_on_square(cropped, cw, ch, margin)
    write_png_rgba(dst, out_w, out_h, centered)
    print(f"Prepared icon: {dst} ({out_w}x{out_h})")


if __name__ == "__main__":
    main()
