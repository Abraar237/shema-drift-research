#!/usr/bin/env python3
"""Three concept GIFs in the script-bias site aesthetic: 840x840, ~80ms/frame,
white-cream card, flat bars, thin rules, monospace numerals, flowing dots,
seamless-ish loop with hold. Numbers from results/analysis.json."""

import json
import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "assets" / "gifs"
OUT.mkdir(parents=True, exist_ok=True)
A = json.loads((HERE.parent / "results" / "analysis.json").read_text())

W = H = 840
INK = (22, 19, 13)
INK2 = (58, 53, 43)
MUTED = (109, 102, 90)
FAINT = (164, 156, 140)
RULE = (231, 226, 213)
BG = (253, 252, 250)
SLATE = (21, 94, 140)
HOT = (179, 0, 107)
SHELF = (192, 100, 26)
GOOD = (28, 122, 85)

MENLO = "/System/Library/Fonts/Menlo.ttc"
HELV = "/System/Library/Fonts/Helvetica.ttc"


def F(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


f_title = F(MENLO, 30, 1)   # Menlo bold
f_sub = F(HELV, 15)
f_note = F(HELV, 13)
f_label = F(HELV, 17)
f_num = F(MENLO, 22)
f_big = F(MENLO, 44, 1)
f_mono = F(MENLO, 16)


def ease(t):
    return 0 if t <= 0 else 1 if t >= 1 else 0.5 - 0.5 * math.cos(math.pi * t)


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else 1.0


def card(d):
    d.rectangle([0, 0, W, H], fill=BG)
    d.rectangle([14, 14, W - 14, H - 14], outline=RULE, width=2)


def title_block(d, title, sub):
    d.text((W // 2, 62), title, font=f_title, fill=INK, anchor="mm")
    d.text((W // 2, 96), sub.upper(), font=f_sub, fill=MUTED, anchor="mm")


def footer(d, text):
    d.text((W // 2, H - 44), text.upper(), font=f_note, fill=FAINT, anchor="mm")


def hbar(d, x, y, w, h, frac, color, track=True):
    if track:
        d.rectangle([x, y, x + w, y + h], outline=RULE, width=2)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 5:
        d.rectangle([x + 2, y + 2, x + fw - 2, y + h - 2], fill=color)


def dot_path(d, pts, t, color, n=3):
    """flowing dots along a polyline, phase t in [0,1)"""
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    for k in range(n):
        dist = ((t + k / n) % 1.0) * total
        acc = 0
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            if acc + L >= dist:
                r = (dist - acc) / L
                x = pts[i][0] + r * (pts[i + 1][0] - pts[i][0])
                y = pts[i][1] + r * (pts[i + 1][1] - pts[i][1])
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color)
                break
            acc += L


def save(frames, name):
    frames[0].save(OUT / name, save_all=True, append_images=frames[1:],
                   duration=80, loop=0, optimize=True)
    print(name, len(frames), "frames,", (OUT / name).stat().st_size // 1024, "KB")


# ---------------- GIF 1: the drop ----------------

def gif1():
    fams = [("Gemini Flash", .992, .154, SLATE), ("Gemini Pro", .975, .108, GOOD),
            ("GPT-5.6-luna", .933, .383, HOT), ("Qwen2.5-7B", .867, .221, SHELF)]
    frames = []
    N = 110
    for fi in range(N):
        t = fi / N
        im = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(im)
        card(d)
        title_block(d, "The schema changed.", "nobody told the agent · task success, four families")
        y0 = 170
        for i, (name, base, drift, col) in enumerate(fams):
            y = y0 + i * 150
            d.text((60, y - 6), name, font=f_label, fill=INK2)
            # baseline bar
            g1 = seg(t, 0.05 + i * 0.04, 0.30 + i * 0.04)
            d.text((60, y + 22), "old schema everywhere", font=f_note, fill=MUTED)
            hbar(d, 260, y + 12, 440, 26, base * g1, tuple(int(c * 0.45 + 255 * 0.55) for c in col))
            d.text((716, y + 25), f"{base:.2f}"[1:] if base < 1 else "1.0", font=f_num,
                   fill=MUTED, anchor="lm")
            # drift bar
            g2 = seg(t, 0.42 + i * 0.05, 0.70 + i * 0.05)
            d.text((60, y + 62), "schema changed, agent not told", font=f_note, fill=MUTED)
            hbar(d, 260, y + 52, 440, 26, base + (drift - base) * g2 if g2 > 0 else 0, col,
                 track=True)
            val = base + (drift - base) * g2 if g2 > 0 else 0
            d.text((716, y + 65), f"{val:.2f}"[1:], font=f_num, fill=col, anchor="lm")
        appear = seg(t, 0.82, 0.9)
        if appear > 0:
            d.text((W // 2, 782), "55 to 87 points gone, every family, p < 5e-5",
                   font=f_label, fill=tuple(int(i + (h - i) * appear) for i, h in zip(BG, HOT)), anchor="mm")
        footer(d, "schemadrift-120 · 4,800 episodes · vizuara research")
        frames.append(im)
    save(frames, "the-drop.gif")


# ---------------- GIF 2: the call that never errors ----------------

def gif2():
    frames = []
    N = 110
    for fi in range(N):
        t = fi / N
        im = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(im)
        card(d)
        title_block(d, "The call that never errors", "default-change drift · the silent cell")
        # user request card
        d.rounded_rectangle([70, 140, 430, 215], radius=10, outline=RULE, width=2)
        d.text((90, 158), "user:", font=f_note, fill=MUTED)
        d.text((90, 180), '"Send $80.00 to @studio_nine"', font=f_mono, fill=INK)
        # agent call card
        g1 = seg(t, 0.08, 0.2)
        if g1 > 0:
            d.rounded_rectangle([70, 245, 430, 350], radius=10, outline=RULE, width=2)
            d.text((90, 262), "agent call (believes schema v1):", font=f_note, fill=MUTED)
            d.text((90, 288), "send_payment(", font=f_mono, fill=SLATE)
            d.text((110, 310), 'amount_cents=8000)', font=f_mono, fill=SLATE)
            d.text((90, 330), "currency omitted: default covers it", font=f_note, fill=FAINT)
        # schema note
        g2 = seg(t, 0.24, 0.34)
        if g2 > 0:
            d.rounded_rectangle([510, 200, 780, 290], radius=10, outline=HOT, width=2)
            d.text((530, 216), "SCHEMA v2 CHANGED:", font=f_note, fill=HOT)
            d.text((530, 240), 'default currency', font=f_mono, fill=INK2)
            d.text((530, 262), 'USD -> EUR', font=f_mono, fill=HOT)
        # validator
        g3 = seg(t, 0.38, 0.52)
        if g3 > 0:
            d.rounded_rectangle([300, 420, 550, 500], radius=10, outline=RULE, width=2)
            d.text((425, 442), "strict validator", font=f_label, fill=INK2, anchor="mm")
            stamp = seg(t, 0.5, 0.58)
            if stamp > 0:
                d.text((425, 474), "200 OK  nothing to catch", font=f_mono, fill=GOOD, anchor="mm")
        dot_path(d, [(250, 350), (250, 390), (425, 390), (425, 420)], t, SLATE)
        # executed
        g4 = seg(t, 0.6, 0.72)
        if g4 > 0:
            d.rounded_rectangle([220, 550, 630, 660], radius=10, outline=HOT, width=3)
            d.text((425, 578), "executed:", font=f_note, fill=MUTED, anchor="mm")
            amt = 80 * seg(t, 0.62, 0.75)
            d.text((425, 618), f"EUR {amt:5.2f}", font=f_big, fill=HOT, anchor="mm")
        g5 = seg(t, 0.8, 0.88)
        if g5 > 0:
            d.text((W // 2, 712), "the user asked for dollars. no error was ever raised.",
                   font=f_label, fill=INK, anchor="mm")
            d.text((W // 2, 742), "38 to 46% of default-change calls execute wrong under a strict validator",
                   font=f_note, fill=MUTED, anchor="mm")
        footer(d, "hand-audited: 24 of 24 confirmed wrong · schemadrift-120")
        frames.append(im)
    save(frames, "the-call-that-never-errors.gif")


# ---------------- GIF 3: the 28-token fix ----------------

def gif3():
    frames = []
    N = 120
    recov = [("Gemini Flash", .98, SLATE), ("Gemini Pro", .96, GOOD),
             ("Qwen2.5-7B", .06, SHELF), ("GPT-5.6-luna", -.06, HOT)]
    for fi in range(N):
        t = fi / N
        im = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(im)
        card(d)
        title_block(d, "A 28-token fix", "machine-readable schema diff vs full schema re-injection")
        # artifacts
        g1 = seg(t, 0.05, 0.2)
        full_h = int(190 * g1)
        d.rectangle([95, 330 - full_h, 240, 330], outline=RULE, width=2)
        if g1 > 0.4:
            d.rectangle([97, 330 - full_h + 2, 238, 328], fill=(234, 241, 247))
        d.text((167, 352), "full v2 schema", font=f_note, fill=MUTED, anchor="mm")
        d.text((167, 372), "206 tokens", font=f_num, fill=INK2, anchor="mm")
        g2 = seg(t, 0.2, 0.3)
        diff_h = int(190 * 28 / 206 * g2)
        d.rectangle([320, 330 - diff_h, 465, 330], outline=HOT, width=2)
        if g2 > 0.5:
            d.rectangle([322, 330 - diff_h + 2, 463, 328], fill=(249, 233, 242))
        d.text((392, 352), "the diff", font=f_note, fill=HOT, anchor="mm")
        d.text((392, 372), "28 tokens", font=f_num, fill=HOT, anchor="mm")
        if g2 > 0.9:
            d.text((392, 278), '{"currency": "USD"->"EUR"}', font=F(MENLO, 13), fill=HOT, anchor="mm")
        # recovery bars
        d.text((60, 430), "share of the drift damage each family recovers with the diff in context:",
               font=f_note, fill=MUTED)
        zero_x = 320
        for i, (name, r, col) in enumerate(recov):
            y = 470 + i * 62
            d.text((60, y + 4), name, font=f_label, fill=INK2)
            d.line([zero_x, y - 8, zero_x, y + 36], fill=FAINT, width=2)
            g = seg(t, 0.38 + i * 0.09, 0.55 + i * 0.09)
            v = r * g
            if v >= 0:
                d.rectangle([zero_x, y, zero_x + int(380 * v), y + 26], fill=col)
            else:
                d.rectangle([zero_x + int(380 * v), y, zero_x, y + 26], fill=col)
            d.text((zero_x + int(380 * max(v, 0)) + 14, y + 13), f"{v:+.2f}",
                   font=f_num, fill=col, anchor="lm")
        d.text((zero_x, 452), "0", font=f_note, fill=FAINT, anchor="mm")
        g5 = seg(t, 0.85, 0.93)
        if g5 > 0:
            d.text((W // 2, 748), "the cheapest fix only works for models that read it",
                   font=f_label, fill=INK, anchor="mm")
        footer(d, "recovery fraction of the drift-induced drop · schemadrift-120")
        frames.append(im)
    save(frames, "the-28-token-fix.gif")


if __name__ == "__main__":
    gif1()
    gif2()
    gif3()
