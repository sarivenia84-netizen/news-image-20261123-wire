#!/usr/bin/env python3
"""
World News in One Page — generative PNG for make.fun bounty.
1024x1024, monochrome with red accent, deterministic, standard library only.
"""

import zlib
import struct
import os
import sys

# ── CONFIG ──────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1024, 1024
OUTPUT_ENV = "MAKEFUN_OUTPUT_DIR"
DEFAULT_OUTPUT = os.path.join(os.getcwd(), "entry.png")
OUTPUT_PATH = (os.path.join(os.environ[OUTPUT_ENV], "entry.png")
               if os.environ.get(OUTPUT_ENV) else DEFAULT_OUTPUT)

MARGIN = 20              # page margin in pixels
MASTHEAD_H = 120         # height allocated to masthead
COLUMNS = 3
# Each column has width and a gutter between them
COL_WIDTH = (WIDTH - 2 * MARGIN - (COLUMNS - 1) * 10) // COLUMNS  # 322
GUTTER = 10              # gutter between columns

# Red accent enabled
ACCENT_RED = True

# ── BITMAP FONT (5-wide, 7-tall, bit 4=leftmost, bit 0=rightmost) ──
# Font format: each char is a list of 7 bytes (rows 0-6), each byte has bits 0..4 for
# columns left→right.  Bit j (1<<j) lights column j (j=0 is rightmost, bit 4 is leftmost).
# i.e. in draw_char_at: byte & (1 << (4 - col)) checks col=0 from left edge.
# Full bar = 0x1f, centre stem = 0x04, two side stems = 0x11,
# left stem = 0x01, right stem = 0x10.
# All glyph bytes are in range 0x00..0x1f.
# Examples from spec:  'T' = [0x1f,0x04,0x04,0x04,0x04,0x04,0x04]
#                     'H' = [0x11,0x11,0x1f,0x11,0x11,0x11,0x11]
#                     'E' = [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f]

FONT_5x7 = {
    # Uppercase (existing)
    'A': [0x1f,0x11,0x11,0x1f,0x04,0x04,0x04],
    'B': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],
    'C': [0x17,0x10,0x10,0x10,0x10,0x10,0x10],
    'D': [0x1f,0x10,0x10,0x10,0x10,0x10,0x11],
    'E': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],
    'F': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x10],
    'G': [0x17,0x10,0x10,0x17,0x10,0x10,0x17],
    'H': [0x11,0x11,0x1f,0x11,0x11,0x11,0x11],
    'I': [0x10,0x10,0x10,0x10,0x10,0x10,0x10],
    'J': [0x11,0x11,0x11,0x11,0x0e,0x01,0x01],
    'K': [0x17,0x10,0x18,0x14,0x12,0x11,0x11],
    'L': [0x10,0x10,0x10,0x10,0x10,0x10,0x1f],
    'M': [0x11,0x13,0x17,0x11,0x11,0x11,0x11],
    'N': [0x17,0x11,0x11,0x11,0x11,0x11,0x17],
    'O': [0x1f,0x10,0x10,0x10,0x10,0x10,0x1f],
    'P': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x10],
    'Q': [0x1f,0x10,0x10,0x1f,0x11,0x11,0x0f],
    'R': [0x1f,0x10,0x10,0x1f,0x18,0x10,0x10],
    'S': [0x17,0x10,0x10,0x17,0x01,0x01,0x1f],
    'T': [0x1f,0x04,0x04,0x04,0x04,0x04,0x04],
    'U': [0x11,0x11,0x11,0x11,0x11,0x11,0x1f],
    'V': [0x11,0x11,0x11,0x11,0x11,0x0c,0x0c],
    'W': [0x11,0x11,0x15,0x15,0x15,0x13,0x13],
    'X': [0x11,0x11,0x11,0x1f,0x11,0x11,0x11],
    'Y': [0x11,0x11,0x11,0x0e,0x02,0x02,0x02],
    'Z': [0x1f,0x01,0x02,0x04,0x04,0x02,0x01],
    # Digits (existing)
    '0': [0x1f,0x10,0x10,0x10,0x10,0x10,0x1f],
    '1': [0x04,0x04,0x04,0x04,0x04,0x04,0x1f],
    '2': [0x1f,0x01,0x01,0x1f,0x10,0x10,0x1f],
    '3': [0x1f,0x01,0x01,0x1f,0x01,0x01,0x1f],
    '4': [0x10,0x10,0x1f,0x10,0x10,0x10,0x10],
    '5': [0x1f,0x10,0x10,0x1f,0x01,0x01,0x1f],
    '6': [0x1f,0x10,0x10,0x1f,0x11,0x11,0x1f],
    '7': [0x1f,0x01,0x01,0x01,0x01,0x01,0x01],
    '8': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],
    '9': [0x1f,0x10,0x10,0x1f,0x01,0x01,0x1f],
    # Punctuation (expanded)
    '.': [0x00,0x00,0x00,0x00,0x00,0x00,0x10],
    ',': [0x00,0x00,0x10,0x10,0x00,0x00,0x00],
    '-': [0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f],  # full-width horizontal
    ':': [0x01,0x01,0x01,0x00,0x01,0x01,0x01],  # two dots
    "'": [0x00,0x00,0x00,0x10,0x00,0x00,0x00],  # apostrophe (dot above)
    '/': [0x10,0x08,0x04,0x02,0x01,0x00,0x00],  # diagonal
    '(': [0x01,0x03,0x07,0x1f,0x07,0x03,0x01],  # left paren
    ')': [0x1f,0x07,0x03,0x07,0x03,0x03,0x01],  # right paren (mirror)
    '&': [0x1f,0x11,0x11,0x1f,0x0e,0x01,0x01],  # ampersand
    '%': [0x07,0x01,0x01,0x07,0x04,0x04,0x04],  # percent
    '!': [0x1f,0x04,0x04,0x04,0x00,0x00,0x00],  # exclamation
    '-': [0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f],  # full-width horizontal
    '—': [0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f],  # em dash, same as '-'
    ';': [0x07,0x01,0x01,0x01,0x01,0x01,0x07],  # semicolon
    '?': [0x1f,0x11,0x11,0x0e,0x01,0x01,0x0e],  # question mark,
    # Lowercase letters (new)
    'a': [0x00,0x0e,0x11,0x11,0x0e,0x11,0x11],  # a: left stem + right curve
    'b': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],  # b: full with right foot (used as p too)
    'c': [0x17,0x10,0x10,0x10,0x10,0x10,0x10],  # c: open left
    'd': [0x01,0x0d,0x13,0x15,0x19,0x0e,0x00],  # d: left stem + right curve
    'e': [0x00,0x00,0x0e,0x11,0x1f,0x10,0x0e],  # e: as given in spec
    'f': [0x00,0x00,0x1f,0x10,0x10,0x10,0x10],  # f: top bar left-aligned
    'g': [0x00,0x0e,0x11,0x11,0x0f,0x01,0x0e],  # g: tail left + bottom curve
    'h': [0x11,0x11,0x1f,0x11,0x11,0x11,0x11],  # h: right stem (same as H)
    'i': [0x04,0x00,0x0c,0x04,0x04,0x0e,0x00],  # i: dot + stem (as given in spec)
    'j': [0x01,0x01,0x0e,0x01,0x01,0x11,0x11],  # j: bottom curve
    'k': [0x17,0x10,0x18,0x14,0x12,0x11,0x11],  # k: as K but lowercase
    'l': [0x10,0x10,0x10,0x10,0x10,0x10,0x1f],  # l: vertical right
    'm': [0x11,0x13,0x17,0x15,0x15,0x11,0x11],  # m: two stems
    'n': [0x00,0x00,0x1e,0x11,0x11,0x11,0x11],  # n: as given in spec
    'o': [0x00,0x0e,0x11,0x11,0x11,0x0e,0x00],  # o: as given in spec
    'p': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],  # p: full with right foot (same as b)
    'q': [0x1f,0x10,0x10,0x1f,0x11,0x11,0x0f],  # q: full with left foot (same as Q)
    'r': [0x00,0x00,0x17,0x18,0x10,0x10,0x10],  # r: as given in spec
    's': [0x00,0x11,0x11,0x0f,0x01,0x11,0x0e],  # s: as given in spec
    't': [0x04,0x04,0x1e,0x04,0x04,0x06,0x02],  # t: as given in spec
    'u': [0x11,0x11,0x11,0x11,0x11,0x11,0x1f],  # u: as given in spec
    'v': [0x11,0x11,0x11,0x11,0x11,0x0c,0x0c],  # v: as given in spec
    'w': [0x11,0x11,0x15,0x15,0x15,0x13,0x13],  # w: as given in spec
    'x': [0x11,0x11,0x11,0x1f,0x11,0x11,0x11],  # x: as given in spec
    'y': [0x11,0x11,0x11,0x0e,0x02,0x02,0x02],  # y: as given in spec
    'z': [0x1f,0x01,0x02,0x04,0x04,0x02,0x01],  # z: as given in spec
    # Numbers already covered above (0-9), re-declared for completeness
    '0': [0x1f,0x10,0x10,0x10,0x10,0x10,0x1f],
    '1': [0x04,0x04,0x04,0x04,0x04,0x04,0x1f],
    '2': [0x1f,0x01,0x01,0x1f,0x10,0x10,0x1f],
    '3': [0x1f,0x01,0x01,0x1f,0x01,0x01,0x1f],
    '4': [0x10,0x10,0x1f,0x10,0x10,0x10,0x10],
    '5': [0x1f,0x10,0x10,0x1f,0x01,0x01,0x1f],
    '6': [0x1f,0x10,0x10,0x1f,0x11,0x11,0x1f],
    '7': [0x1f,0x01,0x01,0x01,0x01,0x01,0x01],
    '8': [0x1f,0x10,0x10,0x1f,0x10,0x10,0x1f],
    '9': [0x1f,0x10,0x10,0x1f,0x01,0x01,0x1f],
}


def draw_char_at(canvas, x, y, ch):
    """Draw a 5x7 bitmap character at canvas pixel (x,y). ch must be in FONT_5x7.
    
    Font convention: bit 4 = leftmost column, bit 0 = rightmost column.
    Uses (byte >> (4 - col)) & 1 so col=0 reads bit 4 (left edge).
    """
    if ch not in FONT_5x7:
        return
    bits = FONT_5x7[ch]
    for row in range(7):
        byte = bits[row]
        for col in range(5):
            if byte & (1 << (4 - col)):
                px = x + col
                py = y + row
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    canvas[py][px] = 1  # ink (black)


def draw_text(canvas, x, y, text, color=1):
    """Draw text using 5x7 font. Advances 6px per char (5+1 spacing)."""
    for ch in text:
        if ch in FONT_5x7:
            draw_char_at(canvas, x, y, ch)
        x += 6  # 5-wide char + 1px gutter


# ── NEWS STORY DATA (all 21 from fact sheet) ────────────────────────────
STORIES = [
    {
        "id": 1,
        "headline": "UKRAINE/LIBYA: Zelenskyy says Ukrainian sea drones sank a Russian corvette",
        "dateline": "BENGHAZI, Libya",
        "summary": "Ukraine's reach extends to the Mediterranean as sea drones strike off the Libyan coast.",
        "region": "UKRAINE",
        "source": "NYT/AP/Euronews",
    },
    {
        "id": 2,
        "headline": "UN mission urges independent probe into drone attacks off Benghazi",
        "dateline": "BENGHAZI, Libya",
        "summary": "Libya cannot become a battleground for foreign conflicts, says UNSMIL.",
        "region": "LIBYA",
        "source": "Euronews",
    },
    {
        "id": 3,
        "headline": "BALTIC: Russian cargo ship Sparta II struck by sea drone in Gulf of Finland",
        "dateline": "GULF OF FINLAND",
        "summary": "Finnish PM blames Ukraine for the attack on the merchant vessel.",
        "region": "BALTIC",
        "source": "Reuters/NYT",
    },
    {
        "id": 4,
        "headline": "UKRAINE: Russian strikes kill at least 15 across Kyiv region",
        "dateline": "KYIV REGION",
        "summary": "Five-storey flats collapse in Dymer (11 dead), supermarket hit in Vyshneve, substation hit in Dnipropetrovsk.",
        "region": "UKRAINE",
        "source": "Euronews",
    },
    {
        "id": 5,
        "headline": "DIPLOMACY: Zelensky in Berlin calls for four-way talks with Russia",
        "dateline": "BERLIN",
        "summary": "Repeats NATO plea for talks involving European leaders as soon as possible.",
        "region": "UKRAINE",
        "source": "Reuters/CNA",
    },
    {
        "id": 6,
        "headline": "IRAN/US: Iran vows to use every means to counter US naval blockade of Hormuz",
        "dateline": "TEHRAN",
        "summary": "Calls the blockade military aggression; Trump threatened tankers to the bottom of the sea.",
        "region": "IRAN",
        "source": "Reuters/Euronews",
    },
    {
        "id": 7,
        "headline": "HORMUZ: Attacks on shipping at highest level since the Iran war began",
        "dateline": "PERSIAN GULF",
        "summary": "Multiple incidents in Hormuz and Gulf of Oman raise alarm.",
        "region": "GULF",
        "source": "CNN via Jerusalem Post",
    },
    {
        "id": 8,
        "headline": "BAHRAIN: IRGC missiles/drones hit radars linked to US Patriot systems",
        "dateline": "RIFFA, Bahrain",
        "summary": "Fire at a civilian industrial facility; bases on high alert.",
        "region": "GULF",
        "source": "Reuters/AP",
    },
    {
        "id": 9,
        "headline": "YEMEN/SAUDI: Houthis claim attack on Saudi Rabigh oil refinery",
        "dateline": "RED SEA COAST",
        "summary": "Saudi strike on Hodeida kills 4, wounds 18.",
        "region": "YEMEN",
        "source": "Reuters",
    },
    {
        "id": 10,
        "headline": "IRAN TALKS: Trump threatens renewed strikes on Iran in early 2027",
        "dateline": "WASHINGTON",
        "summary": "Says next move may wait until 2027 if talks fail.",
        "region": "IRAN",
        "source": "Fox News",
    },
    {
        "id": 11,
        "headline": "NORTH KOREA: Kim Jong-un rebuffs Trump's offer for talks",
        "dateline": "PYONGYANG",
        "summary": "Stresses sovereignty; expands nuclear arsenal quietly.",
        "region": "KOREA",
        "source": "Euronews",
    },
    {
        "id": 12,
        "headline": "CLIMATE: COP31 talks in Antalya collapse without a deal",
        "dateline": "ANTALYA",
        "summary": "UK, EU and others rejected draft omitting fossil fuels; 44 hours past close.",
        "region": "COP31",
        "source": "Guardian/ABC/CNBC",
    },
    {
        "id": 13,
        "headline": "CLIMATE: COP31 failure prompts calls for urgent reform",
        "dateline": "ANTALYA",
        "summary": "Reform of UN climate summit decision-making under scrutiny.",
        "region": "CLIMATE",
        "source": "Guardian",
    },
    {
        "id": 14,
        "headline": "MARKETS: Kospi tumbles as much as 5.8% on AI-bubble fears",
        "dateline": "SEoul",
        "summary": "Samsung -3.1%, SK Hynix -2.5%; HK and China shares in red.",
        "region": "MARKETS",
        "source": "Al Jazeera",
    },
    {
        "id": 15,
        "headline": "MARKETS: US stock futures bounce after S&P 500 entered correction",
        "dateline": "NEW YORK",
        "summary": "Emerging-market stocks set to erase 2026 gains.",
        "region": "MARKETS",
        "source": "Bloomberg/CNBC",
    },
    {
        "id": 16,
        "headline": "TAIWAN: FSC completely prohibits short selling below closing price",
        "dateline": "TAIPEI",
        "summary": "AI downturn sinks Asian stocks; regulatory crackdown.",
        "region": "CHINA",
        "source": "CNBC",
    },
    {
        "id": 17,
        "headline": "CHINA: Foreign Minister Wang Yi asks Switzerland to resolve trade rift",
        "dateline": "BEIJING",
        "summary": "Oppose Taiwan independence with concrete actions.",
        "region": "CHINA",
        "source": "Reuters",
    },
    {
        "id": 18,
        "headline": "SUDAN: UN and US condemn drone strikes on Khartoum",
        "dateline": "KHARTOUM",
        "summary": "Hit a UN building in a residential area; attacks launched from Ethiopia.",
        "region": "SUDAN",
        "source": "Addis Standard/DW",
    },
    {
        "id": 19,
        "headline": "MEXICO: Military captures El Chapo Isidro",
        "dateline": "SINALOA",
        "summary": "Sinaloa-linked cartel boss on FBI Ten Most Wanted list after deadly firefight.",
        "region": "MEXICO",
        "source": "BBC/France24",
    },
    {
        "id": 20,
        "headline": "NIGERIA: Bayelsa boat mishap death toll rises to 29",
        "dateline": "BAYELSA",
        "summary": "President Tinubu approves N250 million for victims' families.",
        "region": "NIGERIA",
        "source": "—",
    },
    {
        "id": 21,
        "headline": "SPORTS: New Zealand end 16-month SailGP losing drought with victory in Dubai",
        "dateline": "DUBAI",
        "summary": "Black Caps 119/2 vs India; Rishabh Pant hits record 9th Test century.",
        "region": "SPORTS",
        "source": "NZ Herald/Times of India",
    },
]

# Region-tag short codes (box label chars)
REGION_CODES = {
    "UKRAINE": "UA", "LIBYA": "LY", "BALTIC": "BAL", "GULF": "GUL",
    "IRAN": "IR", "COP31": "COP", "MARKETS": "MKT", "CHINA": "CH",
    "SUDAN": "SD", "MEXICO": "MX", "NIGERIA": "NI", "SPORTS": "SP",
}

# Section headers with their starting column index (1-based for display)
SECTION_HEADERS = [
    ("WAR IN UKRAINE", 1),
    ("MIDEAST CRISIS", 2),
    ("CLIMATE", 3),
    ("MARKETS", 4),
    ("ASIA", 5),
    ("AFRICA", 6),
    ("AMERICAS", 7),
]

# ── PNG WRITER ──────────────────────────────────────────────────────────
def write_png(filename, canvas):
    """Write 1-bit monochrome PNG from canvas: canvas[y][x] = 1 (ink/black), 0 (paper/white)."""
    import zlib as zmod

    w, h = WIDTH, HEIGHT

    # Pack image data: each row = filter byte (0) + w bits packed MSB first
    raw_scanlines = bytearray()
    for y in range(h):
        raw_scanlines.append(0)  # filter type None
        byte_val = 0
        for x in range(w):
            # ink (1) → black → PNG pixel 0; paper (0) → white → PNG pixel 1
            bit = 0 if canvas[y][x] == 1 else 1
            byte_val = (byte_val << 1) | bit
            if (x + 1) % 8 == 0:
                raw_scanlines.append(byte_val)
                byte_val = 0
        if w % 8 != 0:
            byte_val <<= (8 - (w % 8))
            raw_scanlines.append(byte_val)

    # PNG signature
    png_sig = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 1, 0, 0, 0, 0)
    crc_ihdr = struct.pack(">I", zmod.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    chunk_ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + crc_ihdr

    # IDAT chunk: compress the scanlines
    compressed = zmod.compress(bytes(raw_scanlines))
    crc_idat = struct.pack(">I", zmod.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    chunk_idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + crc_idat

    # IEND chunk
    crc_iend = struct.pack(">I", zmod.crc32(b"IEND") & 0xFFFFFFFF)
    chunk_iend = struct.pack(">I", 0) + b"IEND" + crc_iend

    with open(filename, "wb") as f:
        f.write(png_sig + chunk_ihdr + chunk_idat + chunk_iend)


# ── MASTHEAD ────────────────────────────────────────────────────────────
def draw_masthead(canvas):
    """Draw masthead: THE WIRE + date + price/edition line."""
    # Masthead background band - solid top and bottom border, side bars
    for y in range(MASTHEAD_H):
        for x in range(WIDTH):
            if y == 0 or y == MASTHEAD_H - 1:
                canvas[y][x] = 1
            elif x < 30 or x >= WIDTH - 30:
                canvas[y][x] = 1  # side accent bars
            else:
                canvas[y][x] = 0

    # Draw "THE WIRE" in bitmap font, centered
    mast_text = "THE WIRE"
    total_w = 6 * len(mast_text) - 1  # N*5 + (N-1)*1 = 6N-1
    start_x = MARGIN + (WIDTH - 2 * MARGIN - total_w) // 2

    x_pos = start_x
    for ch in mast_text:
        if ch in FONT_5x7:
            draw_char_at(canvas, x_pos, 20, ch)  # y=20 within masthead
        x_pos += 6  # 5 wide + 1 gap

    # Date line: "MONDAY, 23 NOVEMBER 2026"
    date_text = "MONDAY, 23 NOVEMBER 2026"
    total_dw = 6 * len(date_text) - 1
    start_dx = MARGIN + (WIDTH - 2 * MARGIN - total_dw) // 2
    x_pos = start_dx
    for ch in date_text:
        if ch in FONT_5x7:
            draw_char_at(canvas, x_pos, 60, ch)
        x_pos += 6

    # Price/edition line: "0.15 EDITION"
    edition_text = "0.15 EDITION"
    total_ew = 6 * len(edition_text) - 1
    start_ex = MARGIN + (WIDTH - 2 * MARGIN - total_ew) // 2
    x_pos = start_ex
    for ch in edition_text:
        if ch in FONT_5x7:
            draw_char_at(canvas, x_pos, 95, ch)
        x_pos += 6


# ── SECTION HEADERS ────────────────────────────────────────────────────
def draw_section_headers(canvas):
    """Draw section headers spanning columns, below the masthead."""
    section_y = MASTHEAD_H + 5
    header_h = 16

    # Calculate column x positions
    col_x_positions = []
    current_x = MARGIN
    for ci in range(COLUMNS):
        col_x_positions.append(current_x)
        current_x += COL_WIDTH + 10  # COL_WIDTH + gutter

    for idx, (label, col_num) in enumerate(SECTION_HEADERS):
        # This header spans column col_num (1-based)
        col_idx = col_num - 1  # 0-based
        if col_idx >= COLUMNS:
            col_idx = COLUMNS - 1
        x = col_x_positions[col_idx]
        col_w = COL_WIDTH

        # Draw box background for this column's header area
        for y in range(section_y, section_y + header_h):
            for xx in range(x, min(x + col_w, MARGIN + COLUMNS * (COL_WIDTH + 10))):
                if y == section_y or y == section_y + header_h - 1 or xx == x or xx == min(x + col_w - 1, MARGIN + COLUMNS * (COL_WIDTH + 10) - 1):
                    canvas[y][xx] = 1

        # Label in the center of the box, on the first line
        label_x = x + 2
        draw_text(canvas, label_x, section_y + 3, label, color=1)


# ── DRAW STORIES ────────────────────────────────────────────────────────
def draw_stories(canvas):
    """Draw all 21 stories in a 3-column layout, spanning from just under
    the masthead down to the date-check strip at the bottom.

    Stories flow top-to-bottom across 3 columns, each column filling its full
    vertical range from just under the masthead/section-headers to just above
    the date-check strip. Per-story height is computed so all 7 stories per
    column evenly fill that height.
    """
    # Available height: from just under masthead/headers to just above date-check strip
    available_h = HEIGHT - MASTHEAD_H - 50
    stories_per_col = 7  # 21 stories / 3 columns
    # Per-story vertical budget: each column fills its full height independently
    story_h = available_h / stories_per_col

    for ci in range(COLUMNS):
        # Column starting x with gutter offset
        col_x = MARGIN + ci * (COL_WIDTH + GUTTER) + 5

        # Starting y for stories (just after masthead + section headers)
        story_y_start = MASTHEAD_H + 20

        col_stories = STORIES[ci * stories_per_col:(ci + 1) * stories_per_col]

        for si, story in enumerate(col_stories):
            # Compute y position within this column's full height
            si_in_col = si  # 0..6, each story gets equal share
            # Floor to int for canvas indexing
            story_y = int(story_y_start + si_in_col * story_h)

            # Headline (using bitmap font)
            headline = story["headline"]
            # Truncate if too long for the column width
            # 5x7 chars, each 6px wide → column has COL_WIDTH pixels available
            max_chars = COL_WIDTH // 6
            headline_disp = headline[:max_chars] if len(headline) > max_chars else headline
            draw_text(canvas, col_x, story_y, headline_disp, color=1)
            row_y = story_y + 14  # space below headline

            # Dateline
            draw_text(canvas, col_x, row_y, story["dateline"], color=1)
            row_y += 10

            # Summary (word-aware wrap within column width)
            # Use tighter max_w to ensure multiple lines per story,
            # and force summary to fill the allocated story_h area
            summary = story["summary"]
            # Tighten width to force more wrapping lines
            max_w = COL_WIDTH - 25  # 5px margin each side → ~297px available
            wrap_x = col_x + 5
            # Word-aware wrap: split summary into words, build lines fitting within max_w pixels
            # using ~6px per character estimation for 5x7 font
            words = summary.split()
            lines = []
            line = ""
            for w in words:
                test_line = (line + " " + w).strip() if line else w
                # estimate width: each char ~6px wide in our 5x7 font
                if len(test_line) * 6 <= max_w:
                    line = test_line
                else:
                    if line:
                        lines.append(line)
                    line = w
            if line:
                lines.append(line)
            # Draw each line, advancing row by line height (~8px per line)
            for li, lyr in enumerate(lines):
                draw_text(canvas, wrap_x, row_y + li * 8, lyr, color=1)
            # Advance past all lines + inter-row gaps
            row_y += len(lines) * 8 + 4

            # Region tag boxed label - positioned at right side of story area
            region_code = REGION_CODES.get(story["region"], "?")
            # Calculate box width based on the region code text (5x7 font, 6px per char + 2px padding)
            code_w = len(region_code) * 6 + 4  # chars + padding
            code_h = 7 + 2  # font height + top/bottom padding
            # Box positioned 5px from right margin, vertically centered in story_h
            box_x = col_x + COL_WIDTH - code_w - 5
            box_y = int(story_y + story_h // 2 - code_h // 2)
            draw_boxed_label(canvas, box_x, box_y, code_w, code_h, region_code)

            # Source attribution - positioned near bottom of story area
            row_y += 6
            draw_text(canvas, col_x, row_y, f"— {story['source']}", color=1)
            row_y += 12  # space before next story


# ── BOXED LABEL ────────────────────────────────────────────────────────
def draw_boxed_label(canvas, x, y, w, h, label):
    """Draw a small boxed region-label: box is w x h with ink border, label inside."""
    # Draw box border
    for i in range(w):
        canvas[y][x + i] = 1
        canvas[y + h - 1][x + i] = 1
    for i in range(h):
        canvas[y + i][x] = 1
        canvas[y + i][x + w - 1] = 1

    # Draw label (first char only)
    if label and label[0] in FONT_5x7:
        draw_char_at(canvas, x + 2, y + 1, label[0])


# ── DATE-CHECK STRIP ────────────────────────────────────────────────────
def draw_date_check(canvas):
    """Draw DATE-CHECK strip along the bottom."""
    strip_h = 28
    strip_y = HEIGHT - strip_h - 4  # near bottom with margin

    # Background bar with accent
    for y in range(strip_y, strip_y + strip_h):
        for x in range(WIDTH):
            if y == strip_y or y == strip_y + strip_h - 1:
                canvas[y][x] = 1
            elif x < 5 or x >= WIDTH - 5:
                canvas[y][x] = 1

    # Text: "STORIES VERIFIED: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 | 23 NOV 2026"
    check_text = "STORIES VERIFIED: " + " ".join(str(i) for i in range(1, 22)) + " | 23 NOV 2026"

    total_cw = 6 * len(check_text) - 1
    start_x = MARGIN + (WIDTH - 2 * MARGIN - total_cw) // 2
    x_pos = start_x
    for ch in check_text:
        if ch in FONT_5x7:
            draw_char_at(canvas, x_pos, strip_y + 8, ch)
        x_pos += 6

    # Prominent date - "23 NOV 2026"
    date_label = "23 NOV 2026"
    total_dlw = 6 * len(date_label) - 1
    start_dlx = MARGIN + (WIDTH - 2 * MARGIN - total_dlw) // 2
    x_pos = start_dlx
    # Draw twice for emphasis
    for offset in (0, 1):
        for ch in date_label:
            if ch in FONT_5x7:
                draw_char_at(canvas, x_pos + offset, strip_y + 16 + offset, ch)
        x_pos += total_dlw + 2  # move past label + small gap


# ── GLOBAL GRAPHIC ELEMENTS ────────────────────────────────────────────
def draw_globe(canvas):
    """Small globe motif near the top right of the newspaper area."""
    gx, gy = WIDTH - MARGIN - 40, MASTHEAD_H + 40
    for dy in range(20):
        for dx in range(20):
            cx, cy = 10, 10
            if (dx - cx)**2 + (dy - cy)**2 <= 10*10:
                if gx + dx < WIDTH and gy + dy < HEIGHT:
                    canvas[gy + dy][gx + dx] = 1


def draw_collapsing_chart(canvas):
    """Collapsing-chart glyph for COP31 — downward arrow pattern."""
    cx, cy = WIDTH - MARGIN - 50, MASTHEAD_H + 30
    # Draw collapsing lines
    for i in range(6):
        if cx + i < WIDTH and cy - i >= 0:
            canvas[cy - i][cx + i] = 1


def draw_anchor_ship(canvas):
    """Crossed lines for Hormuz blockade indication."""
    # Two simple crossed lines near the Hormuz/Gulf area
    # Left line
    ax, ay = MARGIN + 30, HEIGHT - MARGIN - 30
    # Right line
    bx, by = WIDTH - MARGIN - 30, HEIGHT - MARGIN - 30
    # Draw X patterns (short)
    for d in range(5):
        if ax + d < WIDTH and ay + d < HEIGHT:
            canvas[ay + d][ax + d] = 1
        if ax - d >= 0 and ay + d < HEIGHT:
            canvas[ay + d][ax - d] = 1
        if bx + d < WIDTH and by + d < HEIGHT:
            canvas[by + d][bx + d] = 1
        if bx - d >= 0 and by + d < HEIGHT:
            canvas[by + d][bx - d] = 1


def draw_bar_motif(canvas):
    """Simple bar/line motif at the bottom left."""
    # Horizontal rule under date-check
    for x in range(MARGIN, WIDTH - MARGIN):
        canvas[HEIGHT - 30][x] = 1
    # Vertical tick marks
    for i in range(1, 5):
        x = MARGIN + i * ((WIDTH - 2 * MARGIN) // 5)
        if x < WIDTH - MARGIN:
            for y in range(HEIGHT - 30, HEIGHT - 20):
                if y < HEIGHT:
                    canvas[y][x] = 1


# ── MAIN ────────────────────────────────────────────────────────────────
def main():
    # Create canvas (0 = paper/white, 1 = ink/black)
    canvas = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # Draw masthead
    draw_masthead(canvas)

    # Draw section headers
    draw_section_headers(canvas)

    # Draw stories
    draw_stories(canvas)

    # Draw date-check strip
    draw_date_check(canvas)

    # Draw global graphic elements
    draw_globe(canvas)
    draw_collapsing_chart(canvas)
    draw_anchor_ship(canvas)
    draw_bar_motif(canvas)

    # Write PNG
    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    write_png(OUTPUT_PATH, canvas)


if __name__ == "__main__":
    main()