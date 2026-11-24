#!/usr/bin/env python3
import os
import struct
import zlib

W = H = 1024
PAPER = (246, 243, 235)
INK = (25, 27, 30)
RED = (172, 39, 44)
GRAY = (90, 94, 91)
WHITE = (255, 253, 247)

# Hand-drawn 5x7 glyphs; each string reads left to right.
_GLYPHS = {
'A':('01110','10001','10001','11111','10001','10001','10001'),'B':('11110','10001','10001','11110','10001','10001','11110'),
'C':('01111','10000','10000','10000','10000','10000','01111'),'D':('11110','10001','10001','10001','10001','10001','11110'),
'E':('11111','10000','10000','11110','10000','10000','11111'),'F':('11111','10000','10000','11110','10000','10000','10000'),
'G':('01111','10000','10000','10111','10001','10001','01111'),'H':('10001','10001','10001','11111','10001','10001','10001'),
'I':('11111','00100','00100','00100','00100','00100','11111'),'J':('00111','00010','00010','00010','10010','10010','01100'),
'K':('10001','10010','10100','11000','10100','10010','10001'),'L':('10000','10000','10000','10000','10000','10000','11111'),
'M':('10001','11011','10101','10101','10001','10001','10001'),'N':('10001','11001','10101','10011','10001','10001','10001'),
'O':('01110','10001','10001','10001','10001','10001','01110'),'P':('11110','10001','10001','11110','10000','10000','10000'),
'Q':('01110','10001','10001','10001','10101','10010','01101'),'R':('11110','10001','10001','11110','10100','10010','10001'),
'S':('01111','10000','10000','01110','00001','00001','11110'),'T':('11111','00100','00100','00100','00100','00100','00100'),
'U':('10001','10001','10001','10001','10001','10001','01110'),'V':('10001','10001','10001','10001','10001','01010','00100'),
'W':('10001','10001','10001','10101','10101','11011','10001'),'X':('10001','10001','01010','00100','01010','10001','10001'),
'Y':('10001','10001','01010','00100','00100','00100','00100'),'Z':('11111','00001','00010','00100','01000','10000','11111'),
'0':('01110','10001','10011','10101','11001','10001','01110'),'1':('00100','01100','00100','00100','00100','00100','01110'),
'2':('01110','10001','00001','00110','01000','10000','11111'),'3':('11110','00001','00001','01110','00001','00001','11110'),
'4':('00010','00110','01010','10010','11111','00010','00010'),'5':('11111','10000','11110','00001','00001','10001','01110'),
'6':('00110','01000','10000','11110','10001','10001','01110'),'7':('11111','00001','00010','00100','01000','01000','01000'),
'8':('01110','10001','10001','01110','10001','10001','01110'),'9':('01110','10001','10001','01111','00001','00010','01100'),
' ':('00000',)*7,'-':('00000','00000','00000','11111','00000','00000','00000'),
'.':('00000','00000','00000','00000','00000','00110','00110'),',':('00000','00000','00000','00000','00110','00110','00100'),
':':('00000','00110','00110','00000','00110','00110','00000'),"'":('00100','00100','01000','00000','00000','00000','00000'),
'/':('00001','00010','00010','00100','01000','01000','10000'),'+':('00000','00100','00100','11111','00100','00100','00000'),
'%':('11001','11010','00010','00100','01000','01011','10011'),'?':('01110','10001','00001','00110','00100','00000','00100'),
'&':('01100','10010','10100','01000','10101','10010','01101'),'"':('01010','01010','00000','00000','00000','00000','00000')}
FONT = {c: tuple(sum((v == '1') << (4-i) for i, v in enumerate(row)) for row in rows) for c, rows in _GLYPHS.items()}

# Independent dated clauses from the supplied 23 November fact sheet.
STORIES = [
('UKRAINE/LIBYA','23 NOV 2026','NYT/AP/EURONEWS','ZELENSKYY SAYS DRONES SANK RUSSIAN CORVETTE'),
('LIBYA','23 NOV 2026','NYT/AP/EURONEWS','UKRAINIAN DRONES HIT CARGO SHIP OFF BENGHAZI'),
('LIBYA / UN','23 NOV 2026','EURONEWS','UNSMIL URGES INDEPENDENT DRONE ATTACK PROBE'),
('LIBYA / UN','23 NOV 2026','EURONEWS','UN SAYS LIBYA MUST NOT BE FOREIGN BATTLEGROUND'),
('BALTIC','22-23 NOV 2026','REUTERS/NYT','SPARTA II STRUCK BY SEA DRONE IN GULF OF FINLAND'),
('BALTIC','22-23 NOV 2026','REUTERS/NYT','FINNISH PM BLAMES UKRAINE FOR SHIP ATTACK'),
('UKRAINE','23 NOV 2026','EURONEWS','RUSSIAN STRIKES KILL AT LEAST 15 IN KYIV REGION'),
('UKRAINE','23 NOV 2026','EURONEWS','DYMER FLATS COLLAPSE; 11 PEOPLE REPORTED DEAD'),
('UKRAINE','23 NOV 2026','EURONEWS','SUPERMARKET HIT IN VYSHNEVE, REPORT SAYS'),
('UKRAINE','23 NOV 2026','EURONEWS','DNIPROPETROVSK SUBSTATION HIT IN STRIKES'),
('DIPLOMACY','23 NOV 2026','REUTERS/CNA','ZELENSKY CALLS IN BERLIN FOR FOUR-WAY TALKS'),
('DIPLOMACY','23 NOV 2026','REUTERS/CNA','UKRAINIAN LEADER SEEKS TALKS WITH EUROPEAN LEADERS'),
('IRAN / US','23 NOV 2026','REUTERS/EURONEWS','TEHRAN VOWS EVERY MEANS AGAINST HORMUZ BLOCKADE'),
('IRAN / US','23 NOV 2026','REUTERS/EURONEWS','IRAN CALLS US NAVAL BLOCKADE MILITARY AGGRESSION'),
('IRAN / US','23 NOV 2026','REUTERS/EURONEWS','TRUMP THREATENS TANKERS OVER HORMUZ STANDOFF'),
('HORMUZ','23 NOV 2026','CNN / JERUSALEM POST','SHIPPING ATTACKS AT HIGHEST LEVEL SINCE IRAN WAR'),
('GULF','23 NOV 2026','CNN / JERUSALEM POST','INCIDENTS REPORTED IN GULF OF OMAN'),
('BAHRAIN','22-23 NOV 2026','REUTERS/AP','IRGC DRONES AND MISSILES HIT RADARS NEAR BASES'),
('BAHRAIN','22-23 NOV 2026','REUTERS/AP','RIFFA AND AWALI RADARS LINKED TO PATRIOT SYSTEMS'),
('BAHRAIN','22-23 NOV 2026','REUTERS/AP','FIRE REPORTED AT CIVILIAN INDUSTRIAL FACILITY'),
('YEMEN / SAUDI','22-23 NOV 2026','REUTERS','HOUTHIS CLAIM ATTACK ON RABIGH OIL REFINERY'),
('YEMEN','22-23 NOV 2026','REUTERS','SAUDI STRIKE ON HODEIDA KILLS FOUR, WOUNDS 18'),
('IRAN TALKS','23 NOV 2026','FOX NEWS','TRUMP THREATENS RENEWED IRAN STRIKES IN 2027'),
('IRAN TALKS','23 NOV 2026','FOX NEWS','TRUMP SAYS NEXT MOVE MAY WAIT UNTIL 2027'),
('NORTH KOREA','23 NOV 2026','EURONEWS','KIM JONG-UN REBUFFS TRUMP OFFER OF TALKS'),
('NORTH KOREA','23 NOV 2026','EURONEWS','KIM STRESSES SOVEREIGNTY AND EXPANDS ARSENAL'),
('CLIMATE','23 NOV 2026','GUARDIAN/ABC/CNBC','COP31 TALKS IN ANTALYA COLLAPSE WITHOUT DEAL'),
('CLIMATE','23 NOV 2026','GUARDIAN/ABC/CNBC','UK AND EU REJECT DRAFT OMITTING FOSSIL FUELS'),
('CLIMATE','23 NOV 2026','GUARDIAN/ABC/CNBC','UN CLIMATE DEBATE RAN 44 HOURS PAST CLOSING'),
('CLIMATE','23 NOV 2026','GUARDIAN','COP31 FAILURE SPARKS CALLS FOR SUMMIT REFORM'),
]


def render():
    image = bytearray(PAPER * (W * H))

    def rect(x, y, w, h, color):
        pixel = bytes(color)
        for yy in range(max(0, y), min(H, y+h)):
            left, right = max(0, x), min(W, x+w)
            if right > left:
                start, end = (yy*W+left)*3, (yy*W+right)*3
                image[start:end] = pixel * (right-left)

    def text(x, y, value, color=INK, scale=1, max_chars=100):
        for char in value.upper()[:max_chars]:
            glyph = FONT.get(char, FONT['?'])
            for gy, bits in enumerate(glyph):
                for gx in range(5):
                    if bits & (16 >> gx):
                        rect(x+gx*scale, y+gy*scale, scale, scale, color)
            x += 6*scale

    def wrap(value, width):
        lines, line = [], ''
        for word in value.split():
            candidate = (line + ' ' + word).strip()
            if len(candidate) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    rect(0, 0, W, H, PAPER)
    rect(0, 0, W, 10, INK)
    rect(0, 10, W, 3, RED)
    text(28, 25, 'THE WIRE', INK, 6)
    text(586, 45, '23 NOVEMBER 2026', RED, 2)
    rect(28, 88, 968, 2, INK)
    text(28, 101, 'WORLD NEWS  /  30 DATED DISPATCHES', INK, 2)
    text(28, 128, 'MONDAY EDITION  -  REPORTING DATES SHOWN ON EACH STORY', GRAY, 1)

    cols, rows = 5, 6
    x0, y0, cw, ch, gx, gy = 24, 153, 188, 128, 10, 7
    for index, (region, date, source, headline) in enumerate(STORIES):
        row, col = divmod(index, cols)
        x, y = x0 + col*(cw+gx), y0 + row*(ch+gy)
        rect(x, y, cw, ch, WHITE)
        rect(x, y, cw, 3, RED if index < 10 else (35, 69, 102))
        text(x+7, y+8, region, RED, 1, 29)
        rect(x+7, y+19, cw-14, 1, (211, 207, 197))
        for line_no, line in enumerate(wrap(headline, 28)[:3]):
            text(x+7, y+26+line_no*10, line, INK, 1, 29)
        text(x+7, y+76, 'DATE  '+date, GRAY, 1, 29)
        text(x+7, y+90, 'SOURCE  '+source, GRAY, 1, 29)
        text(x+7, y+109, 'DATE CHECKED', (35, 69, 102), 1, 29)

    footer_y = y0 + rows*(ch+gy) + 5
    rect(24, footer_y, 976, 2, INK)
    text(28, footer_y+10, 'THE WIRE  |  WORLD DESK  |  SOURCES: REUTERS, AP, EURONEWS AND OTHERS', GRAY, 1)
    text(28, footer_y+24, 'DATE-CHECK: ALL DISPATCH DATES REFER TO 22-23 NOVEMBER 2026 REPORTING', GRAY, 1)
    scanlines = bytearray()
    stride = W*3
    for yy in range(H):
        scanlines.append(0)
        scanlines.extend(image[yy*stride:(yy+1)*stride])

    def chunk(kind, data):
        payload = kind + data
        return struct.pack('>I', len(data)) + payload + struct.pack('>I', zlib.crc32(payload) & 0xffffffff)

    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(scanlines, 7)) + chunk(b'IEND', b''))
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, 'entry.png')
    with open(output_path, 'wb') as output:
        output.write(png)
    print('wrote %s (%d bytes; %d stories)' % (output_path, len(png), len(STORIES)))


if __name__ == '__main__':
    render()
