"""Rebuild the self-hosted animated README banner with Pillow.

Run from the repository root: python tools/generate_banner.py
No external image servers, tracking pixels, or network calls.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1100, 340
BG, PANEL, LIME, INK, MUTED = '#0B1415', '#142121', '#C7F28A', '#F0F5E9', '#B0C0B7'


def font(size, serif=False):
    names = (['georgiai.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'] if serif else
             ['segoeuib.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def generate():
    frames = []
    for frame in range(60):
        t = frame / 60 * math.tau
        image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        d = ImageDraw.Draw(image)
        d.rounded_rectangle((1, 1, WIDTH - 2, HEIGHT - 2), radius=24, outline='#39504A', width=2)
        d.rounded_rectangle((40, 33, 260, 62), radius=14, fill=PANEL, outline='#39504A')
        d.ellipse((53, 44, 61, 52), fill=LIME)
        d.text((72, 38), 'YOUR SHOPPING STUDIO', fill=MUTED, font=font(13))
        d.text((39, 79), 'ShopImpact', fill=INK, font=font(62))
        d.text((43, 159), 'A little more intentional.', fill=LIME, font=font(30, True))
        d.text((43, 218), 'TRACK YOUR SPEND.  EXPLORE YOUR FOOTPRINT.', fill=MUTED, font=font(14))
        d.text((43, 245), 'DISCOVER   /   REPAIR   /   REUSE   /   REPEAT', fill=MUTED, font=font(13))
        d.ellipse((735, 30, 1035, 303), fill=PANEL)
        d.ellipse((701, 79, 1065, 259), outline='#39504A', width=2)
        dx, dy = 883 + 182 * math.cos(t), 169 + 90 * math.sin(t)
        d.ellipse((dx - 6, dy - 6, dx + 6, dy + 6), fill=LIME)
        offset = int(math.sin(t) * 7)
        d.arc((835, 64 + offset, 930, 155 + offset), 180, 360, fill=INK, width=7)
        d.polygon([(800, 117 + offset), (963, 117 + offset), (948, 256 + offset), (815, 256 + offset)], fill=LIME)
        d.ellipse((845, 154 + offset, 885, 208 + offset), fill='#23694F')
        d.ellipse((883, 147 + offset, 924, 202 + offset), fill='#498454')
        d.line((883, 176 + offset, 883, 225 + offset), fill='#142617', width=3)
        d.rounded_rectangle((708, 93 - offset, 784, 147 - offset), radius=12, fill=BG, outline='#39504A', width=2)
        d.line([(727, 119 - offset), (738, 129 - offset), (765, 106 - offset)], fill=LIME, width=4)
        d.rounded_rectangle((956, 231 - offset, 1055, 280 - offset), radius=12, fill=BG, outline='#39504A', width=2)
        for i in range(4):
            h = 11 + i * 5 + math.sin(t + i) * 3
            d.rounded_rectangle((973 + i * 18, 267 - h - offset, 981 + i * 18, 267 - offset), radius=3, fill=LIME)
        # Seamless travelling dashes along the footer.
        for x in range(-30, WIDTH, 42):
            pos = x + frame / 60 * 42
            d.line((pos, 315, pos + 16, 315), fill='#39504A', width=2)
        frames.append(image)
    output = ROOT / 'assets' / 'shopimpact-banner.gif'
    output.parent.mkdir(exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=70,
                   loop=0, optimize=True, disposal=1)
    print(f'{output.name}: {output.stat().st_size:,} bytes, {len(frames)} frames')


if __name__ == '__main__':
    generate()
