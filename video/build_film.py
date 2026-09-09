#!/usr/bin/env python3
"""Research film: 1920x1080 @ 60fps, phrase-anchored to narration timestamps
(timing.json), script-bias visual system (cream card, flat bars, Menlo bold
titles, Helvetica labels, monospace numerals, continuous motion). Renders PNG
frames -> ffmpeg. Numbers from results/analysis.json."""

import json
import math
import pathlib
import shutil

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
T = json.load(open(HERE / "timing.json"))
FRAMES = HERE / "frames"

W, H, FPS = 1920, 1080, 60
INK = (22, 19, 13); INK2 = (58, 53, 43); MUTED = (109, 102, 90)
FAINT = (164, 156, 140); RULE = (231, 226, 213); BG = (253, 252, 250)
SLATE = (21, 94, 140); HOT = (179, 0, 107); SHELF = (192, 100, 26); GOOD = (28, 122, 85)
MENLO = "/System/Library/Fonts/Menlo.ttc"; HELV = "/System/Library/Fonts/Helvetica.ttc"


def F(p, s, i=0):
    return ImageFont.truetype(p, s, index=i)


f_h1 = F(MENLO, 72, 1); f_h2 = F(MENLO, 52, 1); f_sub = F(HELV, 30)
f_lab = F(HELV, 32); f_note = F(HELV, 24); f_eyebrow = F(HELV, 22)
f_num = F(MENLO, 40); f_big = F(MENLO, 120, 1); f_mono = F(MENLO, 34)
f_mid = F(MENLO, 64, 1)


def ease(x):
    return 0 if x <= 0 else 1 if x >= 1 else 0.5 - 0.5 * math.cos(math.pi * x)


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)


def mix(c1, c2, f):
    return tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


def base(d, t):
    d.rectangle([0, 0, W, H], fill=BG)
    d.rectangle([28, 28, W - 28, H - 28], outline=RULE, width=3)
    d.text((70, 62), "S C H E M A D R I F T - 1 2 0", font=f_eyebrow, fill=FAINT)
    d.text((W - 70, 62), "V I Z U A R A   R E S E A R C H", font=f_eyebrow, fill=FAINT, anchor="ra")
    # continuous motion: slow dot caravan along the bottom rule
    for k in range(7):
        x = 70 + ((t * 42 + k * 260) % (W - 140))
        d.ellipse([x - 4, H - 60, x + 4, H - 52], fill=mix(RULE, FAINT, 0.5))


def hbar(d, x, y, w, h, frac, color, outline=True):
    if outline:
        d.rectangle([x, y, x + w, y + h], outline=RULE, width=3)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 6:
        d.rectangle([x + 3, y + 3, x + fw - 3, y + h - 3], fill=color)


def counter(v, decimals=0):
    return f"{v:,.{decimals}f}"


# ---------------- scenes ----------------

def s1(d, t):  # cold open 0 - testbed
    g = seg(t, 0.3, 1.2)
    d.text((W // 2, 300), "The schema changed.", font=f_h1,
           fill=mix(BG, INK, g), anchor="mm")
    d.text((W // 2, 400), "Nobody told the agent.", font=f_h1,
           fill=mix(BG, HOT, seg(t, 1.0, 2.0)), anchor="mm")
    # schema card with live morph at promise_breaks
    g2 = seg(t, 3.0, 4.0)
    if g2 > 0:
        d.rounded_rectangle([560, 520, 1360, 830], radius=18, outline=RULE, width=3)
        d.text((600, 560), "send_payment(", font=f_mono, fill=mix(BG, SLATE, g2))
        m = seg(t, T["promise_breaks"] - 0.2, T["promise_breaks"] + 1.2)
        field = "memo" if m < 0.5 else "reference"
        col = SLATE if m < 0.5 else HOT
        d.text((640, 615), f'{field}="Lunch split",', font=f_mono, fill=mix(BG, col, g2))
        m2 = seg(t, T["promise_breaks"] + 1.0, T["promise_breaks"] + 2.2)
        d.text((640, 670), 'speed="instant",' if m2 < 0.5 else 'speed="realtime",',
               font=f_mono, fill=mix(BG, SLATE if m2 < 0.5 else HOT, g2))
        m3 = seg(t, T["promise_breaks"] + 2.0, T["promise_breaks"] + 3.2)
        d.text((640, 725), 'currency: default USD' if m3 < 0.5 else 'currency: default EUR',
               font=f_mono, fill=mix(BG, SLATE if m3 < 0.5 else HOT, g2))
        d.text((600, 780), ")", font=f_mono, fill=mix(BG, SLATE, g2))
    q = seg(t, T["question"], T["question"] + 1.2)
    if q > 0:
        d.text((W // 2, 940), "fail loudly, or keep going and do the wrong thing?",
               font=f_sub, fill=mix(BG, MUTED, q), anchor="mm")


def s2(d, t):  # testbed counters
    lt = t - T["testbed"]
    d.text((W // 2, 220), "SchemaDrift-120", font=f_h2, fill=INK, anchor="mm")
    stats = [("tools", 30, 0.5), ("frozen tasks", 120, 1.6), ("model families", 4, 5.8),
             ("episodes", 4800, 6.8)]
    for i, (k, v, at) in enumerate(stats):
        x = 330 + i * 330
        g = seg(lt, at, at + 1.0)
        d.rounded_rectangle([x - 140, 330, x + 140, 520], radius=16, outline=RULE, width=3)
        d.text((x, 405), counter(v * g), font=f_num if v > 999 else f_mid,
               fill=mix(BG, SLATE, seg(lt, at, at + 0.3)), anchor="mm")
        d.text((x, 480), k.upper(), font=f_note, fill=MUTED, anchor="mm")
    # five classes appear as the narration lists them
    cls = [("RENAME", "memo -> reference", 8.9), ("ENUM", '"instant" retired', 10.6),
           ("REQUIRED", "default deleted", 12.4), ("TYPE", '8000 -> "80.00"', 15.0),
           ("DEFAULT", "USD -> EUR", 17.3)]
    ct = t - T["classes"]
    for i, (name, ex, at) in enumerate(cls):
        x = 260 + i * 360
        g = seg(t - T["classes"], at - 8.9 + 0.001, at - 8.9 + 0.8) if False else seg(ct, [1.6, 3.3, 5.1, 7.6, 9.9][i], [2.4, 4.1, 5.9, 8.4, 10.7][i])
        if g > 0:
            d.rounded_rectangle([x - 160, 640, x + 160, 830], radius=14,
                                outline=mix(BG, HOT, g), width=3)
            d.text((x, 700), name, font=f_lab, fill=mix(BG, HOT, g), anchor="mm")
            d.text((x, 770), ex, font=f_note, fill=mix(BG, INK2, g), anchor="mm")


def s3(d, t):  # the damage
    d.text((W // 2, 200), "Old schema in the prompt. New schema at the API.",
           font=f_h2, fill=INK, anchor="mm")
    fams = [("Gemini Flash", .992, .154, SLATE, T["flash_num"]),
            ("Gemini Pro", .975, .108, GOOD, T["pro_num"]),
            ("GPT-5.6-luna", .933, .383, HOT, T["luna_num"]),
            ("Qwen2.5-7B", .867, .221, SHELF, T["qwen_num"])]
    for i, (name, b, dr, col, at) in enumerate(fams):
        y = 320 + i * 170
        d.text((180, y), name, font=f_lab, fill=INK2)
        g0 = seg(t, T["damage"] + 1.0 + i * 0.4, T["damage"] + 2.0 + i * 0.4)
        gf = seg(t, at + 0.6, at + 2.2)
        val = b * g0 + (dr - b * g0) * gf * (1 if g0 > 0.99 else 0)
        cur = b * g0 if gf == 0 else b + (dr - b) * gf
        hbar(d, 500, y - 10, 1050, 56, cur, col)
        d.text((1590, y + 18), f"{cur:.2f}"[1:], font=f_num, fill=col, anchor="lm")


def s4(d, t):  # silent map + payment
    d.text((W // 2, 190), "How much of it is silent?", font=f_h2, fill=INK, anchor="mm")
    rows = [("rename", "caught", T["strict_catches"] + 0.6),
            ("enum-tighten", "caught", T["strict_catches"] + 1.4),
            ("newly-required", "caught", T["strict_catches"] + 2.2),
            ("type-change", "caught", T["strict_catches"] + 3.0),
            ("default-change", "NOTHING TO CATCH", T["default_violates"] + 0.8)]
    for i, (name, verdict, at) in enumerate(rows):
        y = 300 + i * 92
        g = seg(t, at, at + 0.6)
        if g > 0:
            d.text((330, y), name, font=f_mono, fill=mix(BG, INK2, g))
            ok = verdict == "caught"
            d.text((900, y), "validator: " + verdict, font=f_lab,
                   fill=mix(BG, GOOD if ok else HOT, g))
    g2 = seg(t, T["payment"], T["payment"] + 1.0)
    if g2 > 0:
        d.rounded_rectangle([560, 800, 1360, 990], radius=18, outline=mix(BG, HOT, g2), width=4)
        amt = 80 * seg(t, T["payment"] + 0.4, T["payment"] + 2.0)
        d.text((W // 2, 860), '"Send $80.00"  ->  executed:', font=f_note,
               fill=mix(BG, MUTED, g2), anchor="mm")
        d.text((W // 2, 930), f"EUR {amt:5.2f}", font=f_mid, fill=mix(BG, HOT, g2), anchor="mm")
    g3 = seg(t, T["lenient"], T["lenient"] + 1.0)
    if g3 > 0:
        d.text((W // 2, 745), "and a lenient API silences renames and type changes too",
               font=f_sub, fill=mix(BG, MUTED, g3), anchor="mm")


def s5(d, t):  # audit
    d.text((W // 2, 210), "Hand-audited: 24 of 24 genuinely wrong", font=f_h2,
           fill=INK, anchor="mm")
    g1 = seg(t, T["invoice"], T["invoice"] + 0.5)
    if g1 > 0:
        d.rounded_rectangle([260, 330, 1660, 520], radius=18, outline=RULE, width=3)
        v = 2500 + (250000 - 2500) * seg(t, T["invoice"] + 0.3, T["invoice"] + 2.6)
        d.text((330, 395), "the invoice:", font=f_lab, fill=MUTED)
        d.text((1590, 400), "$" + counter(v), font=f_mid,
               fill=mix(SLATE, HOT, seg(t, T["invoice"] + 0.3, T["invoice"] + 2.6)), anchor="rm")
    g2 = seg(t, T["grant"], T["grant"] + 0.5)
    if g2 > 0:
        d.rounded_rectangle([260, 560, 1660, 750], radius=18, outline=RULE, width=3)
        d.text((330, 625), "the access grant:", font=f_lab, fill=MUTED)
        gg = seg(t, T["grant"] + 0.3, T["grant"] + 2.0)
        txt = "2 days" if gg < 0.5 else "4 months"
        d.text((1590, 630), txt, font=f_mid, fill=SLATE if gg < 0.5 else HOT, anchor="rm")
    g3 = seg(t, T["audit24"], T["audit24"] + 0.8)
    if g3 > 0:
        d.text((W // 2, 880), "accepted with no error. counted as successes.",
               font=f_sub, fill=mix(BG, INK, g3), anchor="mm")


def s6(d, t):  # levers
    d.text((W // 2, 190), "Three fixes, one drifted world", font=f_h2, fill=INK, anchor="mm")
    rows = [("raw-error retry", .34, SHELF, T["retry"] + 0.5),
            ("full new schema", .82, SLATE, T["fullschema"] + 0.5),
            ("28-token diff", .98, HOT, T["diff"] + 0.5)]
    for i, (name, v, col, at) in enumerate(rows):
        y = 300 + i * 150
        g = seg(t, at, at + 1.8)
        d.text((180, y), name, font=f_lab, fill=INK2)
        hbar(d, 560, y - 8, 1000, 56, v * g, col)
        d.text((1600, y + 20), f"{v * g:.2f}"[1:], font=f_num, fill=col, anchor="lm")
    d.text((560, 250), "share of the damage recovered (Gemini Flash)", font=f_note, fill=MUTED)
    g2 = seg(t, T["diff_beats"], T["diff_beats"] + 1.0)
    if g2 > 0:
        d.rounded_rectangle([260, 790, 1660, 960], radius=18, outline=mix(BG, HOT, g2), width=3)
        d.text((330, 830), "why the diff wins: the new schema deleted the old default.",
               font=f_lab, fill=mix(BG, INK2, g2))
        r = seg(t, T["remembers"], T["remembers"] + 0.8)
        d.text((330, 890), "the diff remembers the past.", font=f_lab, fill=mix(BG, HOT, r))


def s7(d, t):  # the catch
    d.text((W // 2, 200), "The catch: only some models read it", font=f_h2, fill=INK, anchor="mm")
    rows = [("Gemini Flash", .98, SLATE, T["catch"] + 0.4), ("Gemini Pro", .96, GOOD, T["catch"] + 0.8),
            ("Qwen2.5-7B", .06, SHELF, T["qwen_nothing"] + 0.4),
            ("GPT-5.6-luna", -.06, HOT, T["luna_negative"] + 0.4)]
    zero = 660
    for i, (name, v, col, at) in enumerate(rows):
        y = 330 + i * 140
        g = seg(t, at, at + 1.4)
        d.text((180, y), name, font=f_lab, fill=INK2)
        d.line([zero, y - 20, zero, y + 70], fill=FAINT, width=3)
        val = v * g
        if val >= 0:
            d.rectangle([zero, y, zero + int(900 * val), y + 52], fill=col)
        else:
            d.rectangle([zero + int(900 * val), y, zero, y + 52], fill=col)
        d.text((zero + int(900 * max(val, 0)) + 26, y + 26), f"{val:+.2f}", font=f_num,
               fill=col, anchor="lm")
    g2 = seg(t, T["luna_negative"] + 3.5, T["luna_negative"] + 4.5)
    if g2 > 0:
        d.text((W // 2, 950), "old-schema calls, with the change log sitting in the prompt",
               font=f_sub, fill=mix(BG, MUTED, g2), anchor="mm")


def s8(d, t):  # calling style
    d.text((W // 2, 210), "One more twist: immunity by habit", font=f_h2, fill=INK, anchor="mm")
    g = seg(t, T["fills"], T["fills"] + 1.5)
    pct = int(100 * g)
    d.text((640, 480), f"{pct}%", font=f_big, fill=HOT, anchor="mm")
    d.text((640, 610), "of optional parameters\nfilled explicitly (GPT-5.6-luna)", font=f_note,
           fill=MUTED, anchor="mm", align="center")
    g2 = seg(t, T["fills"] + 2.5, T["fills"] + 4.0)
    if g2 > 0:
        surv = 0.96 * g2
        d.text((1280, 480), f"{surv:.2f}"[1:], font=f_big, fill=GOOD, anchor="mm")
        d.text((1280, 610), "survival on required +\ndefault-change drift", font=f_note,
               fill=MUTED, anchor="mm", align="center")
    g3 = seg(t, T["fills"] + 5.0, T["fills"] + 6.0)
    if g3 > 0:
        d.text((W // 2, 800), "a model that writes the currency itself cannot be hurt by a changed default",
               font=f_sub, fill=mix(BG, INK2, g3), anchor="mm")


def s9(d, t):  # takeaway
    d.text((W // 2, 240), "The takeaway", font=f_h2, fill=INK, anchor="mm")
    lines = [("Ship a machine-readable diff with every version bump.", T["ship"], HOT),
             ("Monitor the calls that succeed, not just the ones that error.", T["monitor"], SLATE),
             ("Test whether your model reads diffs before you count on it.", T["test"], GOOD)]
    for i, (txt, at, col) in enumerate(lines):
        g = seg(t, at, at + 0.9)
        if g > 0:
            y = 420 + i * 150
            d.ellipse([230, y - 14, 258, y + 14], fill=mix(BG, col, g))
            d.text((300, y), txt, font=f_lab, fill=mix(BG, INK, g), anchor="lm")
    g4 = seg(t, T["end"] - 1.5, T["end"] - 0.5)
    if g4 > 0:
        d.text((W // 2, 950), "paper, code, and data: github.com/Abraar237/shema-drift-research",
               font=f_note, fill=mix(BG, MUTED, g4), anchor="mm")


SCENES = [
    (0.0, T["testbed"], s1),
    (T["testbed"], T["damage"], s2),
    (T["damage"], T["silent"], s3),
    (T["silent"], T["invoice"] - 0.4, s4),
    (T["invoice"] - 0.4, T["levers"], s5),
    (T["levers"], T["catch"], s6),
    (T["catch"], T["twist"], s7),
    (T["twist"], T["takeaway"], s8),
    (T["takeaway"], T["end"] + 2.0, s9),
]
XFADE = 0.5


def render_at(tt):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    base(d, tt)
    for (a, b, fn) in SCENES:
        if a <= tt < b:
            fn(d, tt)
            # crossfade into next scene
            nxt = [s for s in SCENES if s[0] == b]
            if nxt and tt > b - XFADE:
                im2 = Image.new("RGB", (W, H))
                d2 = ImageDraw.Draw(im2)
                base(d2, tt)
                nxt[0][2](d2, tt)
                im = Image.blend(im, im2, (tt - (b - XFADE)) / XFADE)
            break
    return im


def main():
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()
    total = int((T["end"] + 2.0) * FPS)
    for f in range(total):
        im = render_at(f / FPS)
        im.save(FRAMES / f"f{f:06d}.png", compress_level=1)
        if f % 600 == 0:
            print(f"{f}/{total}")
    print("frames done:", total)


if __name__ == "__main__":
    main()
