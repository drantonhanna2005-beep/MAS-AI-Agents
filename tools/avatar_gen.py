"""توليد مقطعي الـ avatar (idle / talk) كإطارات ثم ترميزهما MP4.

المخرجات: web/assets/avatar/{idle.mp4, talk.mp4, poster.jpg}

التشغيل:  python tools/avatar_gen.py
المتطلبات: pillow + imageio-ffmpeg (يحمل ffmpeg تلقائياً)
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg

W = 1024          # مساحة الرسم (تُصغّر لاحقاً)
OUT = 512         # مقاس الفيديو النهائي
FPS = 30
SECONDS = 4
FRAMES = FPS * SECONDS

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "web" / "assets" / "avatar"
TMP = Path(__file__).resolve().parent / "frames"

BG_IN = (18, 32, 53)
BG_OUT = (7, 11, 19)
SKIN_TOP = (250, 221, 196)
SKIN_BOT = (226, 180, 138)
SKIN_DARK = (205, 155, 113)
HAIR = (32, 38, 51)
SHIRT_TOP = (62, 124, 242)
SHIRT_BOT = (26, 64, 148)
GOLD = (217, 176, 106)

# هندسة أساسية (كل الأرقام على مساحة 1024)
HEAD = (322, 208, 702, 648)          # cx=512, cy=428
EYE_Y = 430
MOUTH_Y = 556


def bez(points, n=60):
    p0, p1, p2, p3 = points
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        out.append((x, y))
    return out


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (1, size[1]))
    d = ImageDraw.Draw(img)
    for y in range(size[1]):
        k = y / max(1, size[1] - 1)
        d.point((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return img.resize(size, Image.BILINEAR)


def make_bg():
    base = vertical_gradient((W, W), BG_IN, BG_OUT)
    halo = Image.new("L", (W, W), 0)
    ImageDraw.Draw(halo).ellipse((120, -160, 904, 620), fill=120)
    halo = halo.filter(ImageFilter.GaussianBlur(150))
    base = Image.composite(Image.new("RGB", (W, W), (79, 140, 255)), base,
                           halo.point(lambda v: int(v * 0.6)))
    ring = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for a in range(0, 360, 9):
        x = 512 + 452 * math.cos(math.radians(a))
        y = 512 + 452 * math.sin(math.radians(a))
        rd.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(79, 140, 255, 42))
    return Image.alpha_composite(base.convert("RGBA"), ring)


def draw_chest(offset_y=0.0):
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # الكتفان: منحنى واسع ينزل خارج الإطار
    top = bez(((70, 1060), (150, 790), (352, 726), (512, 726)), 80) + \
          bez(((512, 726), (672, 726), (874, 790), (954, 1060)), 80)
    poly = top + [(954, W), (70, W)]
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    layer.paste(vertical_gradient((W, W), SHIRT_TOP, SHIRT_BOT), (0, 0), mask)

    # فتحة الرقبة (قاعدة داكنة)
    d.polygon([(430, 736), (594, 736), (512, 902)], fill=(15, 37, 84, 255))
    # ياقة على شكل حرف V
    d.line([(430, 736), (512, 902)], fill=(36, 80, 170, 255), width=9, joint="curve")
    d.line([(594, 736), (512, 902)], fill=(36, 80, 170, 255), width=9, joint="curve")
    # ظل تحت الذقن على الصدر
    shade = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(shade).ellipse((392, 690, 632, 806), fill=(0, 0, 0, 105))
    shade = shade.filter(ImageFilter.GaussianBlur(30))
    layer = Image.alpha_composite(layer, shade)
    if offset_y:
        layer = layer.transform((W, W), Image.AFFINE, (1, 0, 0, 0, 1, -offset_y), resample=Image.BICUBIC)
    return layer


def draw_head(mouth=0.0, blink=0.0, brow=0.0, tilt=0.0):
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # الرقبة
    d.polygon([(430, 588), (594, 588), (610, 750), (414, 750)], fill=SKIN_DARK + (255,))
    d.polygon([(430, 588), (512, 642), (594, 588), (594, 700), (512, 722), (430, 700)],
              fill=(214, 164, 120, 210))

    # الأذنان
    d.ellipse((306, 392, 358, 492), fill=(233, 189, 151, 255))
    d.ellipse((666, 392, 718, 492), fill=(233, 189, 151, 255))

    # الرأس
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).ellipse(HEAD, fill=255)
    layer.paste(vertical_gradient((W, W), SKIN_TOP, SKIN_BOT), (0, 0), mask)

    # ظل خفيف على الجانب الأيمن + إضاءة الحافة اليسرى
    sh = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((560, 250, 780, 660), fill=(126, 84, 52, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(38))
    sh.putalpha(Image.composite(sh.split()[3], Image.new("L", (W, W), 0), mask))
    layer = Image.alpha_composite(layer, sh)

    rim = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(rim).arc((334, 220, 692, 636), 150, 230, fill=(178, 205, 255, 120), width=9)
    rim = rim.filter(ImageFilter.GaussianBlur(7))
    rim.putalpha(Image.composite(rim.split()[3], Image.new("L", (W, W), 0), mask))
    layer = Image.alpha_composite(layer, rim)

    # فرشاة جديدة بعد التركيب
    d = ImageDraw.Draw(layer)

    # الشعر: قبعة تغطي الجبهة والجانبين
    hair = bez(((326, 424), (300, 300), (368, 204), (512, 202)), 60) + \
           bez(((512, 202), (656, 204), (724, 300), (698, 424)), 60) + \
           bez(((698, 424), (676, 348), (636, 312), (576, 300)), 40) + \
           bez(((576, 300), (520, 290), (462, 300), (404, 336)), 40) + \
           bez(((404, 336), (364, 364), (338, 392), (326, 424)), 40)
    d.polygon(hair, fill=HAIR + (255,))
    # لمعة خفيفة على الشعر
    d.arc((344, 214, 680, 420), 205, 305, fill=(74, 85, 105, 110), width=10)
    # خصلة شعر جانبية ناعمة
    d.polygon(bez(((338, 372), (356, 320), (402, 288), (444, 288)), 30) +
              [(446, 304), (376, 380)], fill=(44, 51, 66, 255))

    # الحواجب (هادئة)
    lift = -8 * brow
    d.arc((388, 358 + lift, 464, 388 + lift), 196, 344, fill=(44, 34, 25, 255), width=9)
    d.arc((560, 358 + lift, 636, 388 + lift), 196, 344, fill=(44, 34, 25, 255), width=9)

    # العينان
    for cx in (426, 598):
        d.ellipse((cx - 22, EYE_Y - 25, cx + 22, EYE_Y + 25), fill=(29, 36, 51, 255))
        d.ellipse((cx - 9, EYE_Y - 19, cx + 2, EYE_Y - 8), fill=(255, 255, 255, 235))
        d.ellipse((cx - 19, EYE_Y + 5, cx - 12, EYE_Y + 12), fill=(255, 255, 255, 95))
    if blink > 0:
        lid = int(50 * blink)
        for cx in (426, 598):
            d.ellipse((cx - 26, EYE_Y - 29, cx + 26, EYE_Y - 29 + lid), fill=SKIN_TOP + (255,))

    # الأنف
    d.line(bez(((512, 444), (512, 496), (512, 510), (532, 518)), 26),
           fill=(206, 152, 112, 255), width=9, joint="curve")

    # الفم
    mw = 50
    if mouth > 0.08:
        mh = 8 + 30 * mouth
        d.ellipse((512 - mw, MOUTH_Y - mh / 2, 512 + mw, MOUTH_Y + mh / 2), fill=(138, 58, 70, 255))
        d.rectangle((512 - mw + 9, MOUTH_Y - mh / 2 + 3, 512 + mw - 9, MOUTH_Y - mh / 2 + 11),
                    fill=(252, 247, 241, 255))
        d.ellipse((512 - mw + 15, MOUTH_Y + mh / 2 - 15, 512 + mw - 15, MOUTH_Y + mh / 2 - 1),
                  fill=(168, 80, 90, 255))
    else:
        # ابتسامة هادئة
        d.arc((512 - mw - 4, MOUTH_Y - 22, 512 + mw + 4, MOUTH_Y + 16), 18, 162,
              fill=(132, 58, 68, 255), width=7)

    # وجنتان
    for cx in (392, 632):
        blush = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        ImageDraw.Draw(blush).ellipse((cx - 36, 476, cx + 36, 516), fill=(224, 141, 126, 40))
        blush = blush.filter(ImageFilter.GaussianBlur(16))
        layer = Image.alpha_composite(layer, blush)
    d = ImageDraw.Draw(layer)

    # السماعة: شريط يلتف حول أعلى الرأس
    d.arc((320, 190, 704, 612), 180, 360, fill=GOLD + (255,), width=11)
    for x0, x1 in ((300, 352), (672, 724)):
        d.rounded_rectangle((x0, 392, x1, 486), radius=22, fill=(31, 41, 56, 255),
                            outline=GOLD + (255,), width=5)
        d.rounded_rectangle((x0 + 8, 414, x1 - 8, 464), radius=12, fill=(46, 60, 80, 255))
    # ذراع الميكروفون

    if tilt:
        layer = layer.rotate(tilt, resample=Image.BICUBIC, center=(512, 720))
    return layer


def vignette(img):
    v = Image.new("L", (W, W), 0)
    ImageDraw.Draw(v).ellipse((-240, -300, W + 240, W + 300), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (W, W), (0, 0, 0, 120))
    return Image.composite(img, Image.alpha_composite(img, dark), v)


def frame(i, talking: bool):
    t = i / FRAMES * 2 * math.pi
    chest_y = 2.4 * math.sin(t)

    if talking:
        beat = i / FPS * 2.6 * math.pi
        mouth = 0.5 + 0.5 * math.sin(beat)
        mouth = 0.1 + 0.9 * (mouth ** 1.4)
        mouth *= 0.72 + 0.28 * math.sin(t * 3.2)
        brow = max(0.0, math.sin(t * 1.7)) * 0.9
        tilt = -1.0 + 0.8 * math.sin(t * 1.2)
    else:
        mouth = 0.0
        brow = 0.0
        tilt = 0.6 * math.sin(t)

    phase = (i % FRAMES) / FRAMES
    blink = 0.0
    for at in (0.18, 0.62):
        dist = abs(phase - at)
        if dist < 0.035:
            blink = max(blink, 1 - dist / 0.035)

    img = make_bg()
    img = Image.alpha_composite(img, draw_chest(chest_y))
    img = Image.alpha_composite(img, draw_head(mouth=mouth, blink=blink, brow=brow, tilt=tilt))
    img = vignette(img)
    return img.convert("RGB").resize((OUT, OUT), Image.LANCZOS)


def encode(frames_dir: Path, out: Path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", str(frames_dir / "f_%03d.png"),
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "23", "-movflags", "+faststart", "-an", str(out),
    ]
    subprocess.run(cmd, check=True)


def render(name: str, talking: bool):
    d = TMP / name
    d.mkdir(parents=True, exist_ok=True)
    for i in range(FRAMES):
        frame(i, talking).save(d / f"f_{i:03d}.png", optimize=True)
    out = ASSETS / f"{name}.mp4"
    encode(d, out)
    return out


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    frame(0, False).save(ASSETS / "poster.jpg", quality=90, optimize=True)
    print("poster", ASSETS / "poster.jpg")
    print("idle", render("idle", False))
    print("talk", render("talk", True))


if __name__ == "__main__":
    main()
