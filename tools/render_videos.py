import subprocess, math, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 15
N = FPS * DUR
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed.ttf"
SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PALETTES = {
    "dawn":   ([12, 18, 45], [48, 40, 92], [196, 118, 70], [255, 190, 120]),
    "ocean":  ([6, 22, 34], [18, 64, 84], [176, 150, 88], [255, 214, 140]),
    "royal":  ([24, 8, 36], [70, 28, 74], [190, 96, 80], [255, 170, 120]),
    "sky":    ([14, 34, 74], [52, 96, 150], [220, 170, 110], [255, 225, 170]),
}

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= maxw: cur = test
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def render(spec, out):
    top, mid, bot, glowc = [np.array(c) for c in PALETTES[spec["palette"]]]
    y = np.linspace(0, 1, H)[:, None]
    grad = np.where(y < 0.6, top + (mid - top) * (y / 0.6), mid + (bot - mid) * ((y - 0.6) / 0.4))
    base = np.repeat(grad[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = (np.clip(1 - np.sqrt((xx - W / 2) ** 2 + ((yy - H * 0.82) * 0.8) ** 2) / 900, 0, 1) ** 2).astype(np.float32)
    rays = Image.new("L", (W, H), 0); d = ImageDraw.Draw(rays)
    cx, cy = W / 2, H * 0.86
    for i in range(14):
        a = math.radians(-170 + i * 12); a2 = a + math.radians(4); L = 2600
        d.polygon([(cx, cy), (cx + L * math.cos(a), cy + L * math.sin(a)), (cx + L * math.cos(a2), cy + L * math.sin(a2))], fill=40)
    rays_np = np.array(rays.filter(ImageFilter.GaussianBlur(25)), dtype=np.float32)[:, :, None] / 255
    glow3 = glow[:, :, None] * glowc.astype(np.float32) * 0.55
    rays3 = rays_np * np.array([255, 220, 170], dtype=np.float32)

    rng = np.random.default_rng(abs(hash(spec["ref"])) % 1000)
    stars = [(rng.integers(0, W), rng.integers(0, int(H * 0.55)), rng.random() * 2 + 1, rng.random() * 6.28) for _ in range(90)]

    # cross layer precomputed
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(c)
    x, ty = W // 2 - 40, 300
    cd.rectangle([x - 9, ty, x + 9, ty + 210], fill=(255, 236, 200, 255))
    cd.rectangle([x - 70, ty + 55, x + 70, ty + 73], fill=(255, 236, 200, 255))
    halo = c.filter(ImageFilter.GaussianBlur(18))
    cross = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cross.alpha_composite(halo); cross.alpha_composite(halo); cross.alpha_composite(c)
    cross_np = np.array(cross, dtype=np.float32)

    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = 60
    while True:
        f_main = ImageFont.truetype(SERIF_B, size)
        lines = wrap(tmp, spec["verse"], f_main, 740)
        if len(lines) * size * 1.45 <= 760 or size <= 48: break
        size -= 4
    lh = int(size * 1.45)
    f_ref = ImageFont.truetype(SERIF_I, 52); f_cta = ImageFont.truetype(SERIF, 48)
    f_page = ImageFont.truetype(SANS, 40); f_big = ImageFont.truetype(SERIF_B, 72)
    big_lines = wrap(tmp, spec["close"], f_big, 740)
    block_h = len(lines) * lh + 90
    y0 = 600 + (820 - block_h) // 2
    reveal_end = 7.0
    starts = [2.1 + i * (reveal_end - 2.1) / max(1, len(lines)) for i in range(len(lines))]
    f_hook = ImageFont.truetype(SERIF_B, 70)
    hook_lines = wrap(tmp, spec.get("hook", ""), f_hook, 760) if spec.get("hook") else []
    f_share = ImageFont.truetype(SANS, 42)

    def text_c(draw, txt, yc, font, fill, alpha):
        w = draw.textlength(txt, font=font)
        draw.text(((W - w) / 2 - 40 + 3, yc + 4), txt, font=font, fill=(0, 0, 0, int(140 * alpha)))
        draw.text(((W - w) / 2 - 40, yc), txt, font=font, fill=fill + (int(255 * alpha),))

    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "21", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(N):
        t = fi / FPS
        pulse = 0.85 + 0.15 * math.sin(t * 1.3)
        frame = base + glow3 * pulse + rays3 * pulse * (0.8 + 0.2 * math.sin(t * 0.9))
        ca = (1.0 if hook_lines else ease(t / 1.2)) * (0.9 + 0.1 * pulse)
        a = cross_np[:, :, 3:4] / 255 * ca
        frame = frame * (1 - a) + cross_np[:, :, :3] * a
        img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")
        sd = ImageDraw.Draw(img)
        for sx, sy, ss, ph in stars:
            v = int(255 * (0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 2 + ph))))
            sd.ellipse([sx - ss, sy - ss, sx + ss, sy + ss], fill=(v, v, min(255, v + 20), 255))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        fo = 1 - ease((t - 9.6) / 0.6) if t < 10.5 else 0
        for i, txt in enumerate(lines):
            al = ease((t - starts[i]) / 0.8) * fo
            if al > 0: text_c(ld, txt, y0 + i * lh + (1 - ease((t - starts[i]) / 0.8)) * 40, f_main, (255, 248, 235), al)
        al = ease((t - 7.8) / 0.8) * fo
        if al > 0: text_c(ld, "— " + spec["ref"], y0 + len(lines) * lh + 30, f_ref, (255, 214, 150), al)
        if t >= 10.2:
            al = ease((t - 10.2) / 0.8)
            for j, bl in enumerate(big_lines):
                text_c(ld, bl, 780 + j * 95 + (1 - al) * 30, f_big, (255, 248, 235), al)
            text_c(ld, spec["sub"], 780 + len(big_lines) * 95 + 40, f_cta, (255, 214, 150), ease((t - 11.2) / 0.8))
        # hook: fully visible on the very first frame, fades out as the verse starts
        if hook_lines and t < 2.4:
            ha = 1.0 if t < 1.7 else 1 - ease((t - 1.7) / 0.6)
            hy = 760 - len(hook_lines) * 50
            for j, hl in enumerate(hook_lines):
                text_c(ld, hl, hy + j * 100, f_hook, (255, 236, 190), ha)
        if t >= 12.2:
            text_c(ld, "Send this to someone who needs it", 1180, f_share, (255, 240, 220), ease((t - 12.2) / 0.7))
        text_c(ld, "Trust Jesus and Be Saved", H - 470, f_page, (255, 240, 220), 0.9 if hook_lines else ease((t - 0.5) / 1.0) * 0.9)
        img.alpha_composite(layer)
        proc.stdin.write(img.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()

if __name__ == "__main__":
    specs = json.load(open(sys.argv[1])); outdir = sys.argv[2]
    idx = [int(i) for i in sys.argv[3].split(",")] if len(sys.argv) > 3 else range(len(specs))
    for i in idx:
        s = specs[i]
        render(s, f"{outdir}/{s['file']}.mp4"); print("done", s["file"], flush=True)
