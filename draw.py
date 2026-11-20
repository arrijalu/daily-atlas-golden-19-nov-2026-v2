#!/usr/bin/env python3
import os
import sys
import hashlib
from PIL import Image, ImageDraw, ImageFont

# Ensure paths relative to draw.py
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
if not os.path.exists(FONT_SERIF_ITALIC):
    FONT_SERIF_ITALIC = FONT_SERIF
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colors
PAPER = (247, 243, 232)
CARD = (255, 253, 246)
INK = (22, 28, 26)
GREY = (104, 100, 90)
ACCENT = (27, 78, 66)
TEAL = (44, 96, 88)
NAVY = (38, 58, 92)
BORDER = (196, 190, 176)
DC_RED = (172, 62, 44)

CONTINENT_COLORS = {
    "Americas": (168, 62, 44),
    "Europe": (58, 84, 128),
    "Mideast": (186, 122, 38),
    "Africa": (122, 106, 52),
    "Asia": (116, 80, 148),
    "Oceania": (44, 124, 134),
}

# Tracking sets for assertions
drawn_stories = set()
used_artworks = set()
clip_failures = 0

def wrap(text, font, max_width, draw_obj):
    words = text.split()
    if not words:
        return [""]
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        w = draw_obj.textlength(test_line, font=font)
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def block(x, y, w, text, font, line_height, max_y, draw_obj, fill=INK):
    global clip_failures
    lines = wrap(text, font, w, draw_obj)
    cur_y = y
    for line in lines:
        if cur_y + line_height > max_y:
            clip_failures += 1
            print(f"CLIP FAIL: cur_y={cur_y}, line_height={line_height}, max_y={max_y} for text: {line}")
        draw_obj.text((x, cur_y), line, font=font, fill=fill)
        cur_y += line_height
    return cur_y

def chip(draw, cx, cy, r, n, fill=ACCENT, font=None):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    if font is None:
        font = ImageFont.truetype(FONT_SANS_BOLD, int(r * 1.4))
    text = str(n)
    draw.text((cx, cy), text, font=font, fill=(255, 255, 255), anchor="mm")

# World map data mask
MAP_MASK = [
    [(8,11), (27,30), (48,50), (59,61)],
    [(1,6), (9,23), (26,31), (44,70)],
    [(1,7), (8,25), (27,31), (38,70)],
    [(2,8), (9,26), (28,30), (37,70)],
    [(3,8), (10,26), (31,31), (37,70)],
    [(5,8), (11,25), (32,33), (34,70)],
    [(10,24), (32,32), (33,69)],
    [(10,23), (32,45), (46,66)],
    [(10,23), (33,44), (45,66)],
    [(10,23), (33,43), (44,63)],
    [(10,22), (32,38), (39,47), (48,64)],
    [(11,21), (33,53), (55,62)],
    [(11,17), (33,48), (49,53), (54,60)],
    [(13,16), (33,45), (49,52), (55,60)],
    [(11,11), (34,45), (50,51), (56,58)],
    [(34,44), (46,47), (56,58), (60,61)],
    [(34,45), (56,62)],
    [(35,45), (58,63)],
    [(17,22), (35,45), (58,64)],
    [(17,23), (37,44), (60,66)],
    [(18,23), (38,44), (64,68)],
    [(18,24), (38,44), (60,67)],
    [(18,24), (39,44), (46,46), (60,68)],
    [(18,24), (39,44), (46,46), (59,68)],
    [(18,23), (39,44), (46,46), (59,67)],
    [(18,23), (40,44), (60,66)],
    [(18,22), (40,43), (61,65)],
    [(18,22), (40,43), (61,65), (71,71)],
    [(19,21), (40,42), (62,64)],
    [(19,21), (40,42), (62,63), (71,72)],
    [(19,20), (63,63)],
    [(19,20), (70,71)],
    [(19,19)],
    [(19,19)],
    [(19,19)],
    [(19,19)]
]

def get_continent(lon, lat):
    if lon < -30:
        return "Americas"
    elif lon >= 112 and lat < -11:
        return "Oceania"
    elif lon >= 52:
        return "Asia"
    elif lat >= 42:
        return "Europe"
    elif lon >= 20 and lat >= 12:
        return "Mideast"
    elif lat >= 35:
        return "Europe"
    else:
        return "Africa"

# Story Data
FEATURED_STORIES = [
    {
        "n": 1,
        "kick": "CHINA · APEC SUMMIT",
        "tag": "FIRST-EVER TRILATERAL",
        "tag_col": NAVY,
        "chip": "CONFIRMED · REUTERS/AP",
        "head": "Trump, Xi, Putin: first three-way summit",
        "summ": "90 minutes in Shenzhen; a joint declaration on nuclear-risk dialogue, UN reform and oil supply.",
        "kind": "summit",
        "continent": "Asia",
    },
    {
        "n": 2,
        "kick": "THE HAGUE · WORLD COURT",
        "tag": "ROHINGYA JUDGMENT",
        "tag_col": ACCENT,
        "chip": "CONFIRMED · ICJ",
        "head": "ICJ: Myanmar committed genocide",
        "summ": "A 9–6 ruling — the first time the Court has found a state responsible for genocide. Reparations ordered.",
        "kind": "court",
        "continent": "Europe",
    },
    {
        "n": 3,
        "kick": "GAMES · LAUNCH DAY",
        "tag": "13 YEARS AFTER GTA V",
        "tag_col": (16, 22, 34),
        "chip": "CONFIRMED · SENSOR TOWER",
        "head": "GTA VI is out: launch day lands",
        "summ": "Midnight launch on PS5 and Xbox; ~17M copies and $1.65B in pre-sales estimated; 212 GB install.",
        "kind": "games",
        "continent": "Americas",
    },
]

GRID_STORIES = [
    {
        "n": 4, "kick": "IRAN · GULF", "head": "Tehran: two supertankers hit mines, ablaze",
        "summ": "IRGC claim; AP could not confirm.", "kind": "tanker", "chip": "CLAIM - IRGC", "continent": "Mideast"
    },
    {
        "n": 5, "kick": "UKRAINE · WAR", "head": "Crimean Bridge struck a third time",
        "summ": "Putin rules out a truce, vows a harsher reply.", "kind": "bridge", "chip": "CONFIRMED - REUTERS", "continent": "Europe"
    },
    {
        "n": 6, "kick": "BANGLADESH · UNREST", "head": "Nationwide shutdown; two killed",
        "summ": "97 Border Guard platoons deployed.", "kind": "lockdown", "chip": "CONFIRMED - REUTERS", "continent": "Asia"
    },
    {
        "n": 7, "kick": "CLIMATE · COP31", "head": "Talks go to the wire, draft thins",
        "summ": "Fossil language out; $120bn target missing.", "kind": "climate", "chip": "CONFIRMED - REUTERS", "continent": "Mideast"
    },
    {
        "n": 8, "kick": "S. KOREA · EXAMS", "head": "Exam-day dragnet catches 98",
        "summ": "Emergency alerts flushed out hidden phones.", "kind": "exam", "chip": "CONFIRMED - KJD", "continent": "Asia"
    },
    {
        "n": 9, "kick": "ASIA · MARKETS", "head": "Hang Seng −1.95% at a 4-month low",
        "summ": "Taiwan −4.4%; ASX falls a sixth day.", "kind": "markets", "chip": "CONFIRMED - EXCHANGES", "continent": "Asia"
    },
    {
        "n": 10, "kick": "TECH · IPO", "head": "Anthropic debuts as ANT",
        "summ": "Priced Wed at $83 — a record $81.3bn raise.", "kind": "ipo", "chip": "CONFIRMED - WIRES", "continent": "Americas"
    },
    {
        "n": 11, "kick": "AUSTRALIA · JOBS", "head": "Jobless hits 4.9%, a 4-year high",
        "summ": "Employment falls 43,500 in October.", "kind": "jobs", "chip": "CONFIRMED - ABS", "continent": "Oceania"
    },
    {
        "n": 12, "kick": "US · LABOUR", "head": "Jobless claims edge up to 203,000",
        "summ": "Continuing claims jump 70,000 to 1.76M.", "kind": "claims", "chip": "CONFIRMED - REUTERS", "continent": "Americas"
    },
    {
        "n": 13, "kick": "INDIA · WEATHER", "head": "Cyclone Akvan closes on the coast",
        "summ": "Landfall due Friday; 72,000 evacuated.", "kind": "cyclone", "chip": "CONFIRMED - IMD", "continent": "Asia"
    },
    {
        "n": 14, "kick": "TURKEY · LAW", "head": "İmamoğlu degree revocation upheld",
        "summ": "Council of State rules; sentence was Wed.", "kind": "diploma", "chip": "CONFIRMED - TURKISH MINUTE", "continent": "Mideast"
    },
    {
        "n": 15, "kick": "US · WEATHER", "head": "Storm sags south; LA on flood alert",
        "summ": "SF's record rain fell Wednesday.", "kind": "storm", "chip": "CONFIRMED - BLOOMBERG", "continent": "Americas"
    },
]

BRIEFS = [
    (16, "Berlin", "Ukraine's allies meet — Merz hosts Macron, Burnham, Tusk, Meloni, Rutte and US envoys Witkoff & Kushner"),
    (17, "Russia", "fires 98 drones and Onyx missiles overnight; 4 killed, 36 injured across Ukraine in the past day"),
    (18, "Gaza", "army says the Yellow Line operation is complete; movement restored, Salahudeen road reopened"),
    (19, "Record", "589M children — nearly 1 in 4 — lived in war zones in 2025, Save the Children counts"),
    (20, "BOJ's", "Ueda: rate hikes will continue; yen near 160 to the dollar, December move expected"),
    (21, "Walmart", "beats: Q3 revenue $188.8B, up 5.2%; full-year guidance raised again"),
    (22, "Lenovo", "posts record $30.2B quarter on AI servers, up 48%; AI revenue $10.8B"),
    (23, "Nigeria's", "Tinubu asks parliament to decriminalise attempted suicide"),
    (24, "India-Japan", "2+2 opens in Tokyo; missile and maritime tech cooperation agreed"),
    (25, "Seoul", "entertainment stocks surge — CJ ENM +20% — on hopes China's content ban is thawing"),
    (26, "Lame-duck", "scramble in Washington: Dec 11 funding deadline, 17 Senate days left"),
    (27, "Ash", "Barty and Shingo Kunieda elected to the Tennis Hall of Fame; induction next August"),
    (28, "ATP", "Finals: Shelton beats Jodar 7-6, 7-5 in the Turin group stage"),
    (29, "Lula", "no hurry to name the cabinet for his new term starting in January"),
    (30, "A", "sugar from a gut bacterium boosts visceral-fat burning, Duke-NUS researchers find"),
    (31, "Liverpool", "wins £1M to advance a new antibiotic class for drug-resistant pneumonia"),
    (32, "Alipay+", "links 50+ global e-wallets to Brazil's Pix instant payments"),
    (33, "Delhi", "schools reopen as GRAP III pollution curbs are lifted on cleaner air"),
]

PIN_DATA = {
    1: (114.05, 22.55, 0, -9, "Asia"),
    2: (4.3, 52.07, -6, -6, "Europe"),
    3: (-80.2, 25.8, 0, -6, "Americas"),
    4: (56.3, 26.6, 4, 0, "Mideast"),
    5: (36.6, 45.3, 6, -4, "Europe"),
    6: (90.4, 23.8, 6, 0, "Asia"),
    7: (30.7, 36.9, -8, -6, "Mideast"),
    8: (126.98, 37.57, 0, -9, "Asia"),
    9: (114.2, 22.3, 13, 7, "Asia"),
    10: (-74.0, 40.7, -4, -9, "Americas"),
    11: (149.1, -35.3, 0, -6, "Oceania"),
    12: (-77.0, 38.9, -12, -8, "Americas"),
    13: (80.3, 15.9, 6, 4, "Asia"),
    14: (32.9, 39.9, -8, 6, "Mideast"),
    15: (-118.2, 34.05, -6, -6, "Americas"),
    16: (13.4, 52.5, 8, -6, "Europe"),
    17: (30.5, 50.4, 8, 4, "Europe"),
    18: (34.3, 31.4, -10, 8, "Mideast"),
    19: (31.95, 31.95, 8, 10, "Mideast"),
    20: (139.7, 35.7, 0, -8, "Asia"),
    21: (-94.2, 36.4, 0, -6, "Americas"),
    22: (114.2, 22.3, -15, -9, "Asia"),
    23: (7.5, 9.1, 0, 0, "Africa"),
    24: (139.7, 35.7, 13, 6, "Asia"),
    25: (126.98, 37.57, 11, 8, "Asia"),
    26: (-77.0, 38.9, 13, 8, "Americas"),
    27: (144.97, -37.8, 0, -6, "Oceania"),
    28: (7.7, 45.1, -8, -10, "Europe"),
    29: (-47.9, -15.8, 0, 4, "Americas"),
    30: (103.8, 1.35, 0, 4, "Asia"),
    31: (-2.98, 53.4, -8, -6, "Europe"),
    32: (-46.6, -23.55, 0, 4, "Americas"),
    33: (77.2, 28.6, -8, -6, "Asia"),
}

def draw_scene_strip(draw, x, y, w, h, kind):
    draw.rectangle([x, y, x + w, y + h], fill=(240, 238, 230))
    if kind == "tanker":
        draw.rectangle([x, y + h/2, x + w, y + h], fill=(44, 92, 140))
        draw.polygon([(x + w*0.3, y + h*0.7), (x + w*0.7, y + h*0.7), (x + w*0.65, y + h*0.5), (x + w*0.35, y + h*0.5)], fill=(30, 30, 30))
        draw.ellipse([x + w*0.5 - 4, y + h*0.3, x + w*0.5 + 4, y + h*0.5], fill=(210, 100, 30))
    elif kind == "bridge":
        draw.rectangle([x, y + h*0.6, x + w, y + h*0.7], fill=(100, 100, 100))
        draw.rectangle([x + w*0.2, y + h*0.2, x + w*0.25, y + h*0.8], fill=(70, 70, 70))
        draw.rectangle([x + w*0.75, y + h*0.2, x + w*0.8, y + h*0.8], fill=(70, 70, 70))
        draw.line([x + w*0.2, y + h*0.3, x + w*0.5, y + h*0.6], fill=(172, 62, 44), width=2)
    elif kind == "lockdown":
        for yy in range(int(y + 4), int(y + h), 6):
            draw.line([x + 4, yy, x + w - 4, yy], fill=(180, 180, 180))
        draw.rectangle([x + w/2 - 6, y + h/2 - 6, x + w/2 + 6, y + h/2 + 6], fill=(200, 160, 40))
    elif kind == "climate":
        cx, cy, cr = x + w/2, y + h/2, h*0.35
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=(27, 78, 66), width=2)
        draw.arc([cx - cr, cy - cr, cx + cr, cy + cr], 0, 360, fill=(27, 78, 66))
    elif kind == "exam":
        draw.rectangle([x + w/2 - 8, y + 4, x + w/2 + 8, y + h - 4], fill=(255, 255, 255), outline=(100, 100, 100))
        draw.line([x + w/2 - 6, y + h/2, x + w/2 + 6, y + h/2], fill=(172, 62, 44), width=2)
    elif kind == "markets":
        draw.line([x + 10, y + 8, x + w*0.4, y + h - 8], fill=(172, 62, 44), width=2)
        font = ImageFont.truetype(FONT_SANS_BOLD, 14)
        draw.text((x + w*0.45, y + 6), "−1.95%", font=font, fill=(172, 62, 44))
    elif kind == "ipo":
        font = ImageFont.truetype(FONT_SANS_BOLD, 18)
        draw.text((x + 12, y + 6), "$83", font=font, fill=ACCENT)
        font_sm = ImageFont.truetype(FONT_SANS, 10)
        draw.text((x + 55, y + 10), "ANTHROPIC IPO", font=font_sm, fill=INK)
    elif kind == "jobs":
        draw.rectangle([x + 15, y + 10, x + 35, y + 26], outline=ACCENT, width=2)
        font = ImageFont.truetype(FONT_SANS_BOLD, 14)
        draw.text((x + 42, y + 8), "4.9%", font=font, fill=ACCENT)
    elif kind == "claims":
        draw.line([x + 10, y + h - 8, x + w*0.5, y + 8], fill=(200, 120, 30), width=2)
        font = ImageFont.truetype(FONT_SANS_BOLD, 13)
        draw.text((x + w*0.52, y + 8), "203,000", font=font, fill=INK)
    elif kind == "cyclone":
        cx, cy = x + w/2, y + h/2
        draw.arc([cx - 15, cy - 15, cx + 15, cy + 15], 0, 270, fill=(44, 92, 140), width=2)
        font = ImageFont.truetype(FONT_SANS_BOLD, 12)
        draw.text((x + 10, y + 10), "72,000", font=font, fill=ACCENT)
    elif kind == "diploma":
        draw.rectangle([x + 15, y + 8, x + 35, y + 24], fill=(255, 255, 255), outline=INK)
        font = ImageFont.truetype(FONT_SANS_BOLD, 11)
        draw.text((x + 42, y + 10), "İmamoğlu", font=font, fill=INK)
    elif kind == "storm":
        font = ImageFont.truetype(FONT_SANS_BOLD, 13)
        draw.text((x + 15, y + 10), "LA / SF", font=font, fill=(70, 90, 110))
    else:
        draw.rectangle([x + 10, y + 10, x + w - 10, y + h - 10], fill=TEAL)

def render():
    global clip_failures
    img = Image.new("RGB", (1024, 1024), PAPER)
    draw = ImageDraw.Draw(img)

    # 1. MASTHEAD
    draw.text((24, 3), "THE WORLD IN ONE DAY · THE DAILY ATLAS", font=ImageFont.truetype(FONT_SANS_BOLD, 12.5), fill=ACCENT)
    draw.text((1000, 3), "33 STORIES · ONE PAGE", font=ImageFont.truetype(FONT_SANS_BOLD, 12.5), fill=INK, anchor="rt")

    date_font = ImageFont.truetype(FONT_SERIF_BOLD, 54)
    draw.text((512, 18), "Thursday 19 November 2026", font=date_font, fill=ACCENT, anchor="ma")

    dek_font = ImageFont.truetype(FONT_SERIF, 12.5)
    draw.text((512, 78), "Trump, Xi and Putin share one table · The World Court finds genocide in Myanmar · A 13-year wait for a game ends", font=dek_font, fill=INK, anchor="ma")

    draw.line([24, 98, 1000, 98], fill=ACCENT, width=3)
    draw.line([24, 103, 1000, 103], fill=ACCENT, width=1)

    # 2. REGION BAR (y ~ 107 to 127)
    regions = [
        ("ASIA", 11, CONTINENT_COLORS["Asia"]),
        ("MIDDLE EAST", 5, CONTINENT_COLORS["Mideast"]),
        ("EUROPE", 6, CONTINENT_COLORS["Europe"]),
        ("AFRICA", 1, CONTINENT_COLORS["Africa"]),
        ("AMERICAS", 8, CONTINENT_COLORS["Americas"]),
        ("OCEANIA", 2, CONTINENT_COLORS["Oceania"]),
    ]
    total_stories = sum(c for _, c, _ in regions)
    assert total_stories == 33

    rx = 24
    r_width = 976
    r_height = 20
    r_y = 107

    for name, count, col in regions:
        seg_w = int(r_width * (count / 33.0))
        draw.rectangle([rx, r_y, rx + seg_w, r_y + r_height], fill=col)
        text = f"{name} {count}"
        draw.text((rx + seg_w / 2, r_y + r_height / 2), text, font=ImageFont.truetype(FONT_SANS_BOLD, 9), fill=(255, 255, 255), anchor="mm")
        rx += seg_w

    # 3. STAT STRIP (y ~ 133 to 173)
    stats = [
        ("3", "presidents at one table"),
        ("9–6", "the genocide ruling"),
        ("$81.3bn", "Anthropic's record IPO"),
        ("551,864", "S. Korea's exam"),
        ("−1.95%", "Hang Seng close"),
        ("589M", "children in war zones"),
    ]

    sx = 24
    s_width = 976
    cell_w = s_width / 6.0
    s_y = 133
    s_h = 40

    for i, (fig, cap) in enumerate(stats):
        cx = sx + i * cell_w + cell_w / 2
        draw.rectangle([sx + i * cell_w, s_y, sx + (i + 1) * cell_w - 4, s_y + s_h], fill=CARD, outline=BORDER)
        draw.text((cx, s_y + 13), fig, font=ImageFont.truetype(FONT_SANS_BOLD, 14), fill=ACCENT, anchor="mm")
        draw.text((cx, s_y + 28), cap, font=ImageFont.truetype(FONT_SANS, 8), fill=INK, anchor="mm")

    # 4. FEATURED TILES (3 cards, each 317 wide, 172 high)
    fy = 178
    feat_card_w = 317
    feat_card_h = 172

    for i, story in enumerate(FEATURED_STORIES):
        cx = 24 + i * 329
        drawn_stories.add(story["n"])
        used_artworks.add(story["kind"])

        draw.rectangle([cx, fy, cx + feat_card_w, fy + feat_card_h], fill=CARD, outline=BORDER)

        art_path = f"assets/{story['kind']}.jpg"
        if os.path.exists(art_path):
            art_img = Image.open(art_path)
            target_w, target_h = feat_card_w, 89
            src_w, src_h = art_img.size
            target_aspect = target_w / target_h
            src_aspect = src_w / src_h
            if src_aspect > target_aspect:
                new_w = int(src_h * target_aspect)
                left = (src_w - new_w) // 2
                art_img = art_img.crop((left, 0, left + new_w, src_h))
            else:
                new_h = int(src_w / target_aspect)
                top = (src_h - new_h) // 2
                art_img = art_img.crop((0, top, src_w, top + new_h))
            art_img = art_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            img.paste(art_img, (cx, fy))

        tag_y = fy + 65
        draw.rectangle([cx, tag_y, cx + feat_card_w, fy + 89], fill=story["tag_col"])
        draw.rectangle([cx, tag_y, cx + 5, fy + 89], fill=ACCENT if story["tag_col"] != ACCENT else INK)
        draw.text((cx + 14, tag_y + 12), story["tag"], font=ImageFont.truetype(FONT_SANS_BOLD, 10.5), fill=(255, 255, 255), anchor="lm")

        chip(draw, cx + 18, fy + 101, 9.5, story["n"], fill=ACCENT)
        draw.text((cx + 34, fy + 101), story["kick"], font=ImageFont.truetype(FONT_SANS_BOLD, 9.5), fill=ACCENT, anchor="lm")

        f_src = ImageFont.truetype(FONT_SANS_BOLD, 7.5)
        pw = int(draw.textlength(story["chip"], font=f_src)) + 14
        pill_left = cx + feat_card_w - 8 - pw
        draw.rounded_rectangle([pill_left, fy + 93, cx + feat_card_w - 8, fy + 109], radius=7, fill=(90, 88, 80))
        draw.text((pill_left + pw/2, fy + 101), story["chip"], font=f_src, fill=(255, 255, 255), anchor="mm")

        head_font = ImageFont.truetype(FONT_SERIF_BOLD, 13)
        summ_font = ImageFont.truetype(FONT_SERIF, 9)
        block(cx + 10, fy + 114, feat_card_w - 20, story["head"], head_font, 15, fy + 142, draw)
        block(cx + 10, fy + 145, feat_card_w - 20, story["summ"], summ_font, 11, fy + 170, draw)

    # Ink rule below featured row
    gy = fy + feat_card_h + 8
    draw.line([24, gy - 4, 1000, gy - 4], fill=INK, width=1)

    # 5. GRID TILES (12 cards, 4 columns x 3 rows; card 238 wide, 88 high)
    grid_start_y = gy
    card_w = 238
    card_h = 88

    for i, story in enumerate(GRID_STORIES):
        col = i % 4
        row = i // 4
        cx = 24 + col * 246
        cy = grid_start_y + row * 92
        drawn_stories.add(story["n"])

        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=CARD, outline=BORDER)
        draw_scene_strip(draw, cx, cy, card_w, 30, story["kind"])

        chip(draw, cx + 13, cy + 41, 6, story["n"], fill=ACCENT)
        draw.text((cx + 24, cy + 41), story["kick"], font=ImageFont.truetype(FONT_SANS_BOLD, 7.5), fill=ACCENT, anchor="lm")

        f_grid_src = ImageFont.truetype(FONT_SANS_BOLD, 7)
        sc_col = DC_RED if story["chip"].startswith("CLAIM") else GREY
        draw.text((cx + 230, cy + 41), story["chip"], font=f_grid_src, fill=sc_col, anchor="rm")

        gh_font = ImageFont.truetype(FONT_SERIF_BOLD, 10.5)
        gs_font = ImageFont.truetype(FONT_SERIF, 8)
        block(cx + 8, cy + 48, card_w - 16, story["head"], gh_font, 11.5, cy + 72, draw)
        block(cx + 8, cy + 73, card_w - 16, story["summ"], gs_font, 9, cy + 86, draw)

    # Bottom Band rule
    by = grid_start_y + 3 * 92 + 2
    draw.line([24, by, 1000, by], fill=INK, width=1)
    hy = by + 6

    # 6. BOTTOM BAND: Map (RIGHT) & Briefs (LEFT, 2 columns)
    draw.text((24, hy), "ALSO ON THURSDAY 19 NOVEMBER 2026", font=ImageFont.truetype(FONT_SANS_BOLD, 11), fill=INK)
    draw.text((700, hy), "WHERE IT HAPPENED", font=ImageFont.truetype(FONT_SANS_BOLD, 11), fill=ACCENT)

    legend_items = [
        ("Americas", CONTINENT_COLORS["Americas"]),
        ("Europe", CONTINENT_COLORS["Europe"]),
        ("Mideast", CONTINENT_COLORS["Mideast"]),
        ("Africa", CONTINENT_COLORS["Africa"]),
        ("Asia", CONTINENT_COLORS["Asia"]),
        ("Oceania", CONTINENT_COLORS["Oceania"]),
    ]
    leg_x = 380
    for name, col in legend_items:
        draw.ellipse([leg_x, hy + 3, leg_x + 7, hy + 10], fill=col)
        draw.text((leg_x + 10, hy + 6), name, font=ImageFont.truetype(FONT_SANS, 8), fill=INK, anchor="lm")
        leg_x += len(name) * 7 + 16

    briefs_y = hy + 22
    col_w = 310
    col_x_list = [24, 350]
    col_briefs = [BRIEFS[:9], BRIEFS[9:]]

    max_briefs_bottom = briefs_y
    f_brief = ImageFont.truetype(FONT_SANS, 9)

    for c_idx, c_list in enumerate(col_briefs):
        bx = col_x_list[c_idx]
        by_cur = briefs_y
        for n, place, text in c_list:
            drawn_stories.add(n)
            chip(draw, bx + 7, by_cur + 6, 6.5, n, fill=ACCENT)
            full_text = f"{n}. {place} — {text}"
            lines = wrap(full_text, f_brief, col_w - 20, draw)
            cur_line_y = by_cur
            for l_idx, line in enumerate(lines):
                draw.text((bx + 18, cur_line_y), line, font=f_brief, fill=INK)
                cur_line_y += 11
            for dot_x in range(int(bx), int(bx + col_w), 6):
                draw.point((dot_x, cur_line_y + 2), fill=BORDER)
            by_cur = cur_line_y + 6
            if by_cur > max_briefs_bottom:
                max_briefs_bottom = by_cur

    band_h = max(215, max_briefs_bottom - briefs_y + 10)

    my = hy + 22
    mw = 300
    mh = band_h
    mx = 700

    draw.rectangle([mx, my, mx + mw, my + mh], fill=(240, 238, 230), outline=BORDER)

    rows = len(MAP_MASK)
    cell_h_map = mh / rows
    cell_w_map = mw / 73.0

    for r_idx, row_spans in enumerate(MAP_MASK):
        lat = 78 - (r_idx + 0.5) * (134 / 36.0)
        for start_c, end_c in row_spans:
            for c_idx in range(start_c, end_c + 1):
                lon = -168 + (c_idx + 0.5) * (360 / 73.0)
                cont = get_continent(lon, lat)
                col = CONTINENT_COLORS.get(cont, GREY)
                muted_col = tuple(int(c * 0.52 + PAPER[0] * 0.48) for c in col)
                cx_cell = mx + c_idx * cell_w_map
                cy_cell = my + r_idx * cell_h_map
                draw.rectangle([cx_cell, cy_cell, cx_cell + cell_w_map + 0.6, cy_cell + cell_h_map + 0.6], fill=muted_col)

    for s_id, (lon, lat, dx, dy, cont) in PIN_DATA.items():
        px = mx + (lon + 168) / 360.0 * mw + dx
        py = my + (78 - lat) / 134.0 * mh + dy
        p_col = CONTINENT_COLORS.get(cont, ACCENT)
        chip(draw, px, py, 7, s_id, fill=p_col, font=ImageFont.truetype(FONT_SANS_BOLD, 7.5))

    # 7. DATE CHECK STRIP
    dc_y = my + band_h + 8
    dc_h = 36
    draw.rectangle([24, dc_y, 1000, dc_y + dc_h], fill=CARD, outline=DC_RED, width=2)

    draw.rectangle([24, dc_y, 86, dc_y + dc_h], fill=DC_RED)
    draw.text((55, dc_y + 11), "DATE", font=ImageFont.truetype(FONT_SANS_BOLD, 10.5), fill=(255, 255, 255), anchor="mm")
    draw.text((55, dc_y + 25), "CHECK", font=ImageFont.truetype(FONT_SANS_BOLD, 10.5), fill=(255, 255, 255), anchor="mm")

    dc_text = "Left out on purpose — they broke on other days: Nvidia's record quarter (Tue 17 Nov) · Siberia An-12 crash, 19 killed (Tue 17 Nov) · Nasser Hospital strike (Thu 12 Nov) · IAEA Yongbyon warning (Wed 18 Nov) · İmamoğlu jailed (Wed 18 Nov) · Webb 'Bao' paper (Wed 18 Nov) · 'human', word of the year (Wed 18 Nov)."
    f_dc = ImageFont.truetype(FONT_SANS, 8.5)
    block(96, dc_y + 6, 890, dc_text, f_dc, 11, dc_y + dc_h - 4, draw, fill=INK)

    # 8. FOOTER
    fy2 = dc_y + dc_h + 8
    draw.line([24, fy2, 1000, fy2], fill=INK, width=1)
    draw.text((512, fy2 + 6), "CLAIM = one side's account, not independently confirmed.", font=ImageFont.truetype(FONT_SERIF_ITALIC, 9.5), fill=INK, anchor="ma")
    draw.text((512, fy2 + 20), "Every story happened or was first reported on Thursday 19 November 2026 · Disputed claims are attributed · Sources: Reuters · AP · AFP · Yonhap · ABS · IMD · ICJ · Save the Children", font=ImageFont.truetype(FONT_SANS, 8), fill=GREY, anchor="ma")

    # Final assertions
    assert clip_failures == 0, f"CLIP FAILURES DETECTED: {clip_failures}"
    assert len(drawn_stories) == 33, f"Expected 33 drawn stories, got {len(drawn_stories)}: {drawn_stories}"
    assert len(used_artworks) == 3, f"Expected 3 used artworks, got {used_artworks}"

    out_path = "entry.png"
    img.save(out_path, format="PNG")

    file_size = os.path.getsize(out_path)
    assert img.size == (1024, 1024), f"Wrong size: {img.size}"
    assert file_size <= 1048576, f"File too large: {file_size} bytes"

    print(f"Successfully generated {out_path}: {img.size}, {file_size} bytes, sha256: {hashlib.sha256(open(out_path, 'rb').read()).hexdigest()}")

if __name__ == "__main__":
    render()
