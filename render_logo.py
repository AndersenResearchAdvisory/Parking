#!/usr/bin/env python3

import math
import struct
import zlib
from pathlib import Path


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def make_canvas(width, height, color):
    r, g, b, a = color
    row = bytearray()
    for _ in range(width):
      row.extend((r, g, b, a))
    return [bytearray(row) for _ in range(height)]


def blend_pixel(row, x, color):
    if x < 0:
        return
    i = x * 4
    src_r, src_g, src_b, src_a = color
    if src_a <= 0:
        return
    alpha = src_a / 255.0
    inv = 1.0 - alpha
    row[i] = int(src_r * alpha + row[i] * inv)
    row[i + 1] = int(src_g * alpha + row[i + 1] * inv)
    row[i + 2] = int(src_b * alpha + row[i + 2] * inv)
    row[i + 3] = 255


def fill_rect(canvas, x0, y0, x1, y1, color):
    height = len(canvas)
    width = len(canvas[0]) // 4
    x0 = max(0, int(x0))
    y0 = max(0, int(y0))
    x1 = min(width, int(x1))
    y1 = min(height, int(y1))
    for y in range(y0, y1):
        row = canvas[y]
        for x in range(x0, x1):
            blend_pixel(row, x, color)


def fill_ellipse(canvas, cx, cy, rx, ry, color):
    height = len(canvas)
    width = len(canvas[0]) // 4
    min_x = max(0, int(cx - rx))
    max_x = min(width - 1, int(cx + rx))
    min_y = max(0, int(cy - ry))
    max_y = min(height - 1, int(cy + ry))
    rx2 = rx * rx
    ry2 = ry * ry
    for y in range(min_y, max_y + 1):
        dy = y + 0.5 - cy
        for x in range(min_x, max_x + 1):
            dx = x + 0.5 - cx
            if (dx * dx) / rx2 + (dy * dy) / ry2 <= 1.0:
                blend_pixel(canvas[y], x, color)


def fill_rounded_rect(canvas, x0, y0, x1, y1, radius, color):
    height = len(canvas)
    width = len(canvas[0]) // 4
    min_x = max(0, int(x0))
    max_x = min(width - 1, int(x1))
    min_y = max(0, int(y0))
    max_y = min(height - 1, int(y1))
    radius = max(0, radius)
    inner_left = x0 + radius
    inner_right = x1 - radius
    inner_top = y0 + radius
    inner_bottom = y1 - radius
    r2 = radius * radius if radius else 1

    for y in range(min_y, max_y + 1):
        py = y + 0.5
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            inside = False
            if inner_left <= px <= inner_right:
                inside = y0 <= py <= y1
            elif inner_top <= py <= inner_bottom:
                inside = x0 <= px <= x1
            else:
                cx = inner_left if px < inner_left else inner_right
                cy = inner_top if py < inner_top else inner_bottom
                inside = (px - cx) ** 2 + (py - cy) ** 2 <= r2
            if inside:
                blend_pixel(canvas[y], x, color)


def fill_polygon(canvas, points, color):
    if not points:
        return
    height = len(canvas)
    width = len(canvas[0]) // 4
    min_y = max(0, int(min(p[1] for p in points)))
    max_y = min(height - 1, int(max(p[1] for p in points)))

    for y in range(min_y, max_y + 1):
        py = y + 0.5
        intersections = []
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            if y1 == y2:
                continue
            if py < min(y1, y2) or py >= max(y1, y2):
                continue
            x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            intersections.append(x)
        intersections.sort()
        for i in range(0, len(intersections), 2):
            if i + 1 >= len(intersections):
                break
            start = max(0, int(math.floor(intersections[i])))
            end = min(width - 1, int(math.ceil(intersections[i + 1])))
            row = canvas[y]
            for x in range(start, end + 1):
                blend_pixel(row, x, color)


def stroke_ellipse(canvas, cx, cy, rx, ry, thickness, color):
    height = len(canvas)
    width = len(canvas[0]) // 4
    min_x = max(0, int(cx - rx))
    max_x = min(width - 1, int(cx + rx))
    min_y = max(0, int(cy - ry))
    max_y = min(height - 1, int(cy + ry))
    outer_rx2 = rx * rx
    outer_ry2 = ry * ry
    inner_rx = max(1, rx - thickness)
    inner_ry = max(1, ry - thickness)
    inner_rx2 = inner_rx * inner_rx
    inner_ry2 = inner_ry * inner_ry
    for y in range(min_y, max_y + 1):
        dy = y + 0.5 - cy
        for x in range(min_x, max_x + 1):
            dx = x + 0.5 - cx
            outer = (dx * dx) / outer_rx2 + (dy * dy) / outer_ry2
            inner = (dx * dx) / inner_rx2 + (dy * dy) / inner_ry2
            if outer <= 1.0 and inner >= 1.0:
                blend_pixel(canvas[y], x, color)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def hex_rgba(value, alpha=255):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def paint_background(canvas):
    top = hex_rgba("EAF6FF")
    bottom = hex_rgba("BCDcff".upper())
    height = len(canvas)
    width = len(canvas[0]) // 4

    for y in range(height):
        t = y / max(1, height - 1)
        row_color = (
            lerp(top[0], bottom[0], t),
            lerp(top[1], bottom[1], t),
            lerp(top[2], bottom[2], t),
            255,
        )
        for x in range(width):
            i = x * 4
            canvas[y][i] = row_color[0]
            canvas[y][i + 1] = row_color[1]
            canvas[y][i + 2] = row_color[2]
            canvas[y][i + 3] = 255

    # Soften the corners to match Apple-style icon framing.
    rounded = make_canvas(width, height, (0, 0, 0, 0))
    fill_rounded_rect(rounded, 32, 32, 992, 992, 236, (255, 255, 255, 255))
    for y in range(height):
        row = canvas[y]
        mask = rounded[y]
        for x in range(width):
            if mask[x * 4 + 3] == 0:
                i = x * 4
                row[i] = 234
                row[i + 1] = 246
                row[i + 2] = 255


def paint_logo(canvas):
    ring_dark = hex_rgba("B7C7D6")
    ring_light = hex_rgba("F7FBFF")
    badge_blue = hex_rgba("123251")
    badge_blue_hi = hex_rgba("2B5784")
    white = hex_rgba("F4F8FC")
    red = hex_rgba("D92F34")
    gold = hex_rgba("F0C44C")
    gold_hi = hex_rgba("F7DE8F")
    line_blue = hex_rgba("3D6388", 150)
    navy_shadow = hex_rgba("0D2133", 90)

    fill_ellipse(canvas, 512, 512, 226, 226, ring_dark)
    fill_ellipse(canvas, 504, 500, 218, 218, ring_light)
    fill_ellipse(canvas, 512, 512, 198, 198, badge_blue)
    fill_ellipse(canvas, 512, 452, 170, 134, badge_blue_hi)
    fill_ellipse(canvas, 512, 548, 184, 120, navy_shadow)
    stroke_ellipse(canvas, 512, 512, 182, 182, 6, line_blue)

    # Tighter SAAB wordmark.
    fill_rect(canvas, 372, 338, 392, 414, white)
    fill_rect(canvas, 392, 338, 446, 356, white)
    fill_rect(canvas, 392, 368, 442, 386, white)
    fill_rect(canvas, 388, 396, 448, 414, white)

    fill_rect(canvas, 458, 338, 478, 414, white)
    fill_rect(canvas, 478, 338, 528, 356, white)
    fill_rect(canvas, 478, 368, 528, 386, white)
    fill_rect(canvas, 528, 338, 548, 414, white)

    fill_rect(canvas, 562, 338, 582, 414, white)
    fill_rect(canvas, 582, 338, 632, 356, white)
    fill_rect(canvas, 582, 368, 632, 386, white)
    fill_rect(canvas, 632, 338, 652, 414, white)

    fill_rect(canvas, 666, 338, 686, 414, white)
    fill_polygon(canvas, [(686, 338), (718, 338), (736, 354), (736, 374), (720, 388), (738, 402), (738, 414), (706, 414), (686, 398)], white)

    # Cleaner griffin silhouette with a more classic curling neck.
    fill_polygon(canvas, [(430, 620), (456, 574), (506, 546), (566, 548), (614, 574), (638, 614), (640, 658), (626, 704), (592, 748), (548, 772), (500, 776), (504, 736), (536, 726), (566, 706), (590, 676), (600, 636), (592, 606), (570, 588), (538, 582), (502, 590), (474, 608), (454, 638)], red)
    fill_polygon(canvas, [(404, 636), (430, 594), (456, 610), (446, 636), (460, 666), (438, 694), (404, 704), (382, 674), (388, 650)], red)
    fill_polygon(canvas, [(538, 590), (566, 562), (608, 554), (640, 568), (654, 590), (646, 612), (624, 626), (596, 630), (566, 626), (542, 614)], red)

    # Crown
    fill_polygon(canvas, [(592, 506), (618, 466), (644, 506), (674, 500), (666, 530), (694, 548), (666, 566), (674, 596), (644, 590), (622, 628), (600, 590), (568, 596), (578, 566), (550, 548), (578, 530)], gold)
    fill_ellipse(canvas, 644, 506, 10, 10, gold_hi)


def resize_nearest(src_rows, src_w, src_h, dst_w, dst_h):
    out = []
    for y in range(dst_h):
        sy = min(src_h - 1, int(y * src_h / dst_h))
        row = bytearray(dst_w * 4)
        src_row = src_rows[sy]
        for x in range(dst_w):
            sx = min(src_w - 1, int(x * src_w / dst_w))
            si = sx * 4
            di = x * 4
            row[di : di + 4] = src_row[si : si + 4]
        out.append(row)
    return out


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
        raw.append(0)
        raw.extend(row)
    idat = zlib.compress(bytes(raw), 9)

    png = bytearray(PNG_SIG)
    png.extend(chunk(b"IHDR", ihdr))
    png.extend(chunk(b"IDAT", idat))
    png.extend(chunk(b"IEND", b""))
    path.write_bytes(png)


def main():
    project_dir = Path(__file__).resolve().parent
    size = 1024
    canvas = make_canvas(size, size, (234, 246, 255, 255))
    paint_background(canvas)
    paint_logo(canvas)

    outputs = {
        "thumbnail.png": (1024, 1024),
        "apple-touch-icon-v5.png": (180, 180),
        "apple-touch-icon.png": (180, 180),
        "icon-192-v5.png": (192, 192),
        "icon-192.png": (192, 192),
        "icon-512-v5.png": (512, 512),
        "icon-512.png": (512, 512),
    }

    for filename, (width, height) in outputs.items():
        rows = canvas if width == size and height == size else resize_nearest(canvas, size, size, width, height)
        write_png_rgba(project_dir / filename, width, height, rows)
        print(f"Wrote {filename}")


if __name__ == "__main__":
    main()
