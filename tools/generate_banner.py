"""Generate the self-hosted liquid-glass README cover. No network assets."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1440, 450
WHITE, MUTED, CYAN, VIOLET = '#F2F6FF', '#B9CAE8', '#80E7FF', '#C5ADFF'


def font(size, bold=False):
    candidates = ['segoeuib.ttf' if bold else 'segoeui.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def base_image():
    yy, xx = np.mgrid[:H, :W]
    blue = np.exp(-((xx - 900) ** 2 / 220000 + (yy - 150) ** 2 / 150000))
    purple = np.exp(-((xx - 1350) ** 2 / 130000 + (yy - 370) ** 2 / 60000))
    cyan = np.exp(-((xx - 450) ** 2 / 80000 + (yy - 440) ** 2 / 80000))
    rgb = np.stack([7 + 10 * blue + 34 * purple, 12 + 26 * blue + 12 * cyan,
                    25 + 58 * blue + 48 * purple + 12 * cyan], axis=-1).clip(0, 255).astype('uint8')
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image, 'RGBA')
    for x in range(0, W, 48):
        draw.line((x, 0, x, H), fill=(150, 185, 255, 8))
    for y in range(0, H, 48):
        draw.line((0, y, W, y), fill=(150, 185, 255, 8))
    draw.rounded_rectangle((1, 1, W - 2, H - 2), radius=26, outline=(158, 195, 255, 75), width=2)
    return image


def sphere():
    n = 250
    yy, xx = np.mgrid[:n, :n]
    x, y = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
    radius = x * x + y * y
    z = np.sqrt(np.maximum(0, 1 - radius))
    shine = np.exp(-((x + .45) ** 2 + (y + .5) ** 2) / .075)
    light = np.clip(.3 + .55 * z - .2 * x - .18 * y, 0, 1)
    rgb = np.stack([60 + 110 * (.5 + .5 * x), 130 + 65 * (.5 - .5 * y), 230 + 20 * z], axis=-1)
    rgb = rgb * light[..., None] + 140 * shine[..., None]
    rgba = np.concatenate([rgb.clip(0, 255), ((radius <= 1) * 255)[..., None]], axis=-1).astype('uint8')
    return Image.fromarray(rgba)


def card(image, box, title, value, subtitle, hue=CYAN):
    x, y, width, height = box
    draw = ImageDraw.Draw(image, 'RGBA')
    draw.rounded_rectangle((x + 3, y + 8, x + width + 3, y + height + 8), radius=20, fill=(0, 0, 0, 40))
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill=(26, 42, 70, 218), outline=(167, 207, 255, 100), width=1)
    draw.line((x + 24, y + 1, x + width - 24, y + 1), fill=(210, 235, 255, 150), width=1)
    draw.text((x + 20, y + 15), title, font=font(11, True), fill=MUTED)
    draw.text((x + 20, y + 37), value, font=font(25, True), fill=WHITE)
    draw.text((x + 20, y + height - 27), subtitle, font=font(11), fill=hue)


def generate():
    background, orb = base_image(), sphere()
    frames = []
    for index in range(64):
        phase = index / 64 * math.tau
        image = background.copy()
        draw = ImageDraw.Draw(image, 'RGBA')
        draw.rounded_rectangle((54, 38, 280, 71), radius=16, fill=(255, 255, 255, 13), outline=(177, 210, 255, 60))
        draw.ellipse((68, 50, 75, 57), fill=CYAN)
        draw.text((86, 46), 'PERSONAL IMPACT STUDIO', font=font(12, True), fill=MUTED)
        draw.text((54, 100), 'Your everyday.', font=font(66, True), fill=WHITE)
        draw.text((54, 177), 'Reimagined.', font=font(70, True), fill=CYAN)
        draw.text((58, 276), 'A clearer view. A lighter footprint.', font=font(23), fill=MUTED)
        draw.text((58, 321), 'SHOPIMPACTAI', font=font(14, True), fill=WHITE)
        draw.text((58, 351), 'DISCOVER   /   TRACK   /   REFLECT   /   REPEAT', font=font(12), fill=MUTED)
        draw.ellipse((868, 75, 1360, 379), outline=(153, 191, 255, 60), width=1)
        draw.ellipse((950, 33, 1282, 422), outline=(153, 191, 255, 35), width=1)
        floating = round(math.sin(phase) * 7)
        image.paste(orb, (985, 103 + floating), orb)
        draw = ImageDraw.Draw(image, 'RGBA')
        px, py = 1114 + 246 * math.cos(phase), 227 + 152 * math.sin(phase)
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=CYAN)
        card(image, (863, 70 - floating, 215, 115), 'THE IDEA', 'Think clearer.', 'A LITTLE MORE INTENTIONAL')
        card(image, (1190, 246 + floating, 194, 118), 'THE EVERYDAY', 'Shop lighter.', 'MORE MEANING. LESS IMPULSE.', VIOLET)
        card(image, (921, 310 - floating, 241, 110), 'THE EXPERIENCE', 'Liquid clarity.', 'DAYLIGHT  /  MIDNIGHT')
        draw = ImageDraw.Draw(image, 'RGBA')
        draw.line((56, 412, 690, 412), fill=(135, 177, 246, 60), width=1)
        glow_x = 56 + index / 63 * 634
        draw.ellipse((glow_x - 3, 409, glow_x + 3, 415), fill=CYAN)
        frames.append(image)
    # A shared palette prevents per-frame color drift and keeps the cover small.
    palette = frames[0].quantize(colors=128)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    output = ROOT / 'assets' / 'shopimpact-banner.gif'
    output.parent.mkdir(exist_ok=True)
    indexed[0].save(output, save_all=True, append_images=indexed[1:], duration=80, loop=0, optimize=True, disposal=1)
    (ROOT / 'test-results').mkdir(exist_ok=True)
    frames[0].save(ROOT / 'test-results' / 'banner-preview.png')
    print(f'{output.name}: {output.stat().st_size:,} bytes, {len(indexed)} frames')


if __name__ == '__main__':
    generate()
