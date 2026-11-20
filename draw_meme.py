#!/usr/bin/env python3
"""Draw the gta6-meme-x-01 meme from scratch with PIL + numpy.

Scene: a Vice City sunset street. Top caption tells the 13-year wait,
the middle caption tells the launch-day sick-leave joke, and make.fun's
ghost mascot (extracted from the official press-kit mark) stands in the
scene on the street next to an OUT OF OFFICE sign, with the make.fun
wordmark along the bottom. Deterministic: fixed seed, no clock, no
network. Run: python3 draw_meme.py  ->  writes meme.png (1024x1024).
"""
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1024, 1024
RNG = random.Random(20261120)

DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size):
    return ImageFont.truetype(DEJAVU_BOLD, size)


def vertical_gradient(stops):
    """stops: list of (y_fraction, (r, g, b)). Returns an RGB image."""
    ys = np.linspace(0, 1, H)
    cols = np.zeros((H, 3), dtype=np.float64)
    xs = [s[0] for s in stops]
    for ch in range(3):
        vals = [s[1][ch] for s in stops]
        cols[:, ch] = np.interp(ys, xs, vals)
    arr = np.repeat(cols[:, None, :], W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def center_text(draw, y, text, fnt, fill, stroke=0, stroke_fill=(0, 0, 0, 255)):
    bbox = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2 - bbox[0]
    draw.text((x, y), text, font=fnt, fill=fill,
              stroke_width=stroke, stroke_fill=stroke_fill)
    return y + (bbox[3] - bbox[1])


def draw_palm(draw, x, base_y, height, lean, color):
    """Simple flat palm silhouette: curved trunk + 6 fronds."""
    top_x = x + lean
    top_y = base_y - height
    segs = 8
    pts = []
    for i in range(segs + 1):
        t = i / segs
        px = x + (top_x - x) * t + 14 * t * t
        py = base_y - height * t
        pts.append((px, py))
    draw.line(pts, fill=color, width=13, joint="curve")
    for ang in (-150, -115, -80, -45, -10, 25):
        import math
        r = height * 0.42
        ex = top_x + r * math.cos(math.radians(ang))
        ey = top_y + r * math.sin(math.radians(ang)) * 0.55 + 26
        mx = top_x + r * 0.55 * math.cos(math.radians(ang))
        my = top_y + r * 0.55 * math.sin(math.radians(ang)) * 0.55 - 18
        draw.line([(top_x, top_y), (mx, my), (ex, ey)],
                  fill=color, width=9, joint="curve")


def extract_ghost(mark_path):
    """Cut the ghost (+coin) out of the press-kit mark's magenta disc.

    Mask = opaque pixels that are not disc-magenta. The coin's magenta
    fill is restored by refilling the coin circle (found from the white
    star's centroid and the black ring around it). Returns RGBA image.
    """
    mark = Image.open(mark_path).convert("RGBA")
    arr = np.asarray(mark).astype(np.int16)
    alpha = arr[:, :, 3]
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    magenta = (r > 140) & (g < 110) & (b > 50) & (b < 210) & ((r - b) > 40)
    mask = (alpha > 10) & (~magenta)
    # Cut the mark's outer black ring (a circle of radius ~420-472
    # around the mark's centre): it is not part of the ghost, and
    # keeping it makes the ghost read as a pasted badge instead of a
    # character standing in the scene. The ghost's own outline stays
    # within radius ~395 of the centre (a clean gap in the black-pixel
    # histogram between ~395 and ~420), so a 405 cut is safe.
    yy, xx = np.indices((1024, 1024))
    far = np.sqrt((xx - 512) ** 2 + (yy - 512) ** 2) > 405
    mask = mask & (~far)
    # White star pixels (coin's star) live inside the coin: restrict the
    # search to the coin's neighbourhood so the ghost's white body is
    # not mistaken for the star.
    white = (r > 240) & (g > 240) & (b > 240) & (alpha > 10)
    ys, xs = np.where(white & (np.indices((1024, 1024))[1] > 700)
                      & (np.indices((1024, 1024))[1] < 840)
                      & (np.indices((1024, 1024))[0] > 380)
                      & (np.indices((1024, 1024))[0] < 520))
    cy, cx = int(ys.mean()), int(xs.mean())
    # Coin ring: black pixels near the star. Their distances form two
    # humps (the coin ring ~120 and the ghost's own outline further
    # out); the coin ring is the tallest 5px bin under 150px.
    black = (r < 60) & (g < 60) & (b < 60) & (alpha > 10)
    yy, xx = np.where(black)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    near = d[(d > 40) & (d < 150)]
    bins = np.bincount((near // 5).astype(int))
    radius = int(np.argmax(bins) * 5 + 2) if len(bins) else 120
    # Refill the coin disc in the mask with the disc magenta.
    disc = mark.getpixel((512, 120))[:3]
    refill = Image.new("L", (1024, 1024), 0)
    rd = ImageDraw.Draw(refill)
    rd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    mask_img = Image.composite(
        Image.new("L", (1024, 1024), 255), mask_img, refill)
    out = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    out.paste(mark, (0, 0), mask_img)
    print(f"coin center=({cx},{cy}) radius={radius} disc={disc}")
    return out


def main():
    img = vertical_gradient([
        (0.00, (26, 8, 58)),     # deep purple night top
        (0.35, (123, 30, 110)),  # purple-magenta
        (0.60, (216, 17, 127)),  # magenta
        (0.80, (255, 94, 58)),   # orange
        (1.00, (255, 179, 71)),  # warm horizon
    ])
    draw = ImageDraw.Draw(img, "RGBA")

    # Sun with a soft glow, low in the sky, left of centre.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([170, 380, 460, 670], fill=(255, 233, 168, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img, "RGBA")
    draw.ellipse([215, 425, 415, 625], fill=(255, 233, 168, 255))
    # Sun stripes (retro striped sun): cut horizontal bands out of the sun.
    for yy in range(560, 625, 14):
        draw.rectangle([215, yy, 415, yy + 5], fill=(255, 179, 71, 255))

    # Skyline silhouette with lit windows.
    base_y = 770
    x = -20
    while x < W + 20:
        bw = RNG.randint(70, 130)
        bh = RNG.randint(90, 210)
        draw.rectangle([x, base_y - bh, x + bw, base_y], fill=(22, 8, 40, 255))
        for _ in range(bw * bh // 900):
            wx = RNG.randint(x + 8, x + bw - 14)
            wy = RNG.randint(base_y - bh + 10, base_y - 14)
            if RNG.random() < 0.55:
                draw.rectangle([wx, wy, wx + 7, wy + 9],
                               fill=(255, 209, 102, 255))
        x += bw + RNG.randint(4, 18)

    # Street.
    draw.rectangle([0, base_y, W, H], fill=(16, 7, 28, 255))
    draw.rectangle([0, base_y, W, base_y + 4], fill=(255, 94, 58, 255))
    # Faint lane dashes.
    for lx in range(40, W, 120):
        draw.rectangle([lx, 880, lx + 60, 888], fill=(120, 90, 140, 255))

    # Palm silhouettes framing the street.
    draw_palm(draw, 90, base_y + 6, 190, -30, (16, 7, 28, 255))
    draw_palm(draw, 985, base_y + 6, 150, 24, (16, 7, 28, 255))

    # Captions (top). Big, stroked, readable when shrunk.
    y = 52
    y = center_text(draw, y, "AFTER 13 YEARS\u2026", font(58),
                    (255, 255, 255, 255), stroke=4)
    y = center_text(draw, y + 8, "GTA 6 IS OUT", font(118),
                    (255, 214, 10, 255), stroke=7)
    y = center_text(draw, y + 14, "THE WHOLE OFFICE", font(54),
                    (255, 255, 255, 255), stroke=5)
    center_text(draw, y + 4, "CALLED IN SICK", font(54),
                (255, 255, 255, 255), stroke=5)

    # make.fun ghost, extracted from the press-kit mark, standing in the
    # scene on the right with a soft contact shadow.
    ghost = extract_ghost("/tmp/mark-1024.png")
    bbox = ghost.getbbox()
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    target_h = 380
    scale = target_h / gh
    ghost = ghost.resize((int(1024 * scale), int(1024 * scale)),
                         Image.LANCZOS)
    bbox = ghost.getbbox()
    gx = 800 - (bbox[0] + bbox[2]) // 2
    gy = 806 - bbox[3]
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([gx + 20, 800, gx + 320, 828], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    img.paste(shadow, (0, 0), shadow)
    img.paste(ghost, (gx, gy), ghost)

    # OUT OF OFFICE sign leaning on the street, left side.
    draw = ImageDraw.Draw(img, "RGBA")
    sx0, sy0, sx1, sy1 = 62, 812, 420, 918
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=14,
                           fill=(255, 255, 255, 255),
                           outline=(0, 0, 0, 255), width=5)
    d2 = ImageDraw.Draw(img, "RGBA")
    d2.text((241, sy0 + 8), "OUT OF", font=font(40), fill=(0, 0, 0, 255),
            anchor="ma")
    d2.text((241, sy0 + 52), "OFFICE", font=font(40), fill=(0, 0, 0, 255),
            anchor="ma")

    # Bottom wordmark: make.fun, big and centred, with a magenta bar.
    d3 = ImageDraw.Draw(img, "RGBA")
    center_text(d3, 946, "make.fun", font(64),
                (255, 255, 255, 255), stroke=4,
                stroke_fill=(120, 0, 60, 255))
    bar_w = 250
    d3.rectangle([(W - bar_w) // 2, 1014, (W + bar_w) // 2, 1022],
                 fill=(216, 17, 127, 255))

    img.convert("RGB").save("meme.png")
    print("wrote meme.png 1024x1024")


if __name__ == "__main__":
    main()
