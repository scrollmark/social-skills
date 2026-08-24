#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Generate stylized sneaker-origin stills as SVG, then rasterize to PNG.

This is a local fallback for brand-origin shorts when paid image generation is
quota-blocked. It creates full-frame 9:16 editorial stills with a recurring
walking sneaker motif and distinct art direction per brand.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

W, H = 1080, 1920


PALETTES = {
    "converse-origin": {
        "bg": "#f2eadf", "ink": "#111827", "a": "#ef4444", "b": "#0f172a",
        "c": "#f8fafc", "muted": "#d9c7b9", "accent": "#facc15",
    },
    "nike-origin": {
        "bg": "#020617", "ink": "#f8fafc", "a": "#22d3ee", "b": "#fb923c",
        "c": "#111827", "muted": "#334155", "accent": "#a3e635",
    },
    "la-gear-origin": {
        "bg": "#16051f", "ink": "#fef3c7", "a": "#ff4fd8", "b": "#5eead4",
        "c": "#fde68a", "muted": "#4c1d95", "accent": "#facc15",
    },
    "sneaker-wars-2026": {
        "bg": "#08060b", "ink": "#f8fafc", "a": "#ff355d", "b": "#38bdf8",
        "c": "#f8fafc", "muted": "#312e81", "accent": "#facc15",
    },
}


SCENES = {
    "converse-origin": [
        ("hook", "zine tunnel", "canvas high-top", "music and court scraps"),
        ("era-1908", "rubber shop", "factory canvas", "handmade utility"),
        ("era-1917", "wood court", "basketball high-top", "practical grip"),
        ("era-1920s", "road clinic", "ankle patch", "game on the road"),
        ("era-1970s", "club floor", "scuffed black canvas", "off-court stage"),
        ("landing", "culture wall", "same shape", "many tribes"),
    ],
    "nike-origin": [
        ("hook", "grid portal", "performance runner", "track to arena"),
        ("era-1964", "cinder track", "sample runner", "import hustle"),
        ("era-1971", "design lab", "prototype runner", "new name"),
        ("era-waffle", "sole lab", "waffle traction", "grip geometry"),
        ("era-1985", "arena lights", "high top myth", "athlete story"),
        ("landing", "culture system", "future sneaker", "sport as status"),
    ],
    "la-gear-origin": [
        ("hook", "mall mirror", "chunky neon", "flash entrance"),
        ("era-1983", "palm storefront", "white leather", "L.A. fashion"),
        ("era-women", "display wall", "color lineup", "choice and color"),
        ("era-celebrity", "TV stage", "studio sneaker", "pop accessory"),
        ("era-lights", "roller rink", "light-up sole", "tiny billboard"),
        ("landing", "neon portal", "spectacle shoe", "entertainment first"),
    ],
    "sneaker-wars-2026": [
        ("hook", "museum dawn", "heritage canvas high top", "history of sneakers"),
        ("court", "court archive", "rubber toe basketball high top", "practical court shoe"),
        ("track", "lab tunnel", "waffle runner prototype", "traction becomes status"),
        ("mall", "neon mall", "chunky light up fashion sneaker", "fashion learns to walk"),
        ("signal", "2026 signal", "three rival sneakers", "drop day goes critical"),
        ("war", "sneaker war room", "armored battle sneaker", "the sneaker wars"),
        ("armageddon", "last runway", "apocalypse sneaker", "final walk"),
    ],
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sneaker(x: float, y: float, scale: float, p: dict, variant: str, lean: float) -> str:
    sx = scale
    sole_fill = p["c"]
    midsole = "#f8fafc" if p["c"].lower() != "#f8fafc" else "#fff7ed"
    outsole = p["ink"]
    if "armored" in variant or "apocalypse" in variant:
        sole_fill = "#111827"
        midsole = "#d1d5db"
        outsole = "#020617"
    chunky = "chunky" in variant or "light" in variant or "apocalypse" in variant
    high = "high" in variant or "canvas" in variant or "basketball" in variant or "heritage" in variant
    runner = "runner" in variant or "waffle" in variant or "prototype" in variant
    sole_h = 74 if chunky else 56
    body = p["a"]
    panel = p["b"] if runner or "light" in variant else p["muted"]
    toe = "#f8fafc" if "canvas" in variant or "rubber toe" in variant else p["c"]
    collar_y = 88 if high else 130
    tongue_top = 62 if high else 96
    sole = f"""
      <ellipse cx="{x+292*sx}" cy="{y+304*sx}" rx="{310*sx}" ry="{48*sx}" fill="#000" opacity=".28"/>
      <path d="M {x+42*sx} {y+248*sx}
               C {x+138*sx} {y+286*sx}, {x+444*sx} {y+300*sx}, {x+640*sx} {y+244*sx}
               L {x+622*sx} {y+(244+sole_h)*sx}
               C {x+448*sx} {y+(292+sole_h*.42)*sx}, {x+136*sx} {y+(286+sole_h*.26)*sx}, {x+36*sx} {y+(247+sole_h*.45)*sx} Z"
            fill="{midsole}" stroke="{outsole}" stroke-width="{9*sx}" stroke-linejoin="round"/>
      <path d="M {x+48*sx} {y+(286+sole_h*.18)*sx}
               C {x+160*sx} {y+(316+sole_h*.05)*sx}, {x+430*sx} {y+(326+sole_h*.02)*sx}, {x+616*sx} {y+(286+sole_h*.02)*sx}"
            fill="none" stroke="{outsole}" stroke-width="{8*sx}" opacity=".9"/>
      <g opacity=".95">
        {''.join(f'<rect x="{x+(92+i*78)*sx}" y="{y+(296+sole_h*.30)*sx}" width="{38*sx}" height="{18*sx}" rx="{5*sx}" fill="{outsole}"/>' for i in range(7))}
      </g>
    """
    upper = f"""
      <path d="M {x+72*sx} {y+244*sx}
               C {x+116*sx} {y+178*sx}, {x+183*sx} {y+144*sx}, {x+276*sx} {y+136*sx}
               C {x+332*sx} {y+64*sx}, {x+452*sx} {y+118*sx}, {x+504*sx} {y+170*sx}
               C {x+554*sx} {y+202*sx}, {x+602*sx} {y+212*sx}, {x+640*sx} {y+244*sx}
               C {x+504*sx} {y+272*sx}, {x+212*sx} {y+274*sx}, {x+72*sx} {y+244*sx} Z"
            fill="{body}" stroke="{outsole}" stroke-width="{10*sx}" stroke-linejoin="round"/>
      <path d="M {x+190*sx} {y+224*sx}
               C {x+260*sx} {y+142*sx}, {x+384*sx} {y+126*sx}, {x+482*sx} {y+184*sx}
               C {x+420*sx} {y+238*sx}, {x+286*sx} {y+250*sx}, {x+190*sx} {y+224*sx} Z"
            fill="{panel}" opacity=".58" stroke="{outsole}" stroke-width="{5*sx}"/>
      <path d="M {x+70*sx} {y+244*sx}
               C {x+94*sx} {y+184*sx}, {x+146*sx} {y+158*sx}, {x+206*sx} {y+174*sx}
               C {x+185*sx} {y+230*sx}, {x+128*sx} {y+254*sx}, {x+70*sx} {y+244*sx} Z"
            fill="{toe}" stroke="{outsole}" stroke-width="{8*sx}"/>
      <path d="M {x+428*sx} {y+136*sx}
               C {x+484*sx} {y+150*sx}, {x+526*sx} {y+180*sx}, {x+552*sx} {y+220*sx}"
            fill="none" stroke="{outsole}" stroke-width="{7*sx}" opacity=".55"/>
      <path d="M {x+284*sx} {y+134*sx}
               C {x+322*sx} {y+(tongue_top)*sx}, {x+374*sx} {y+(tongue_top+6)*sx}, {x+408*sx} {y+138*sx}
               L {x+390*sx} {y+222*sx}
               C {x+354*sx} {y+238*sx}, {x+302*sx} {y+230*sx}, {x+268*sx} {y+208*sx} Z"
            fill="{sole_fill}" stroke="{outsole}" stroke-width="{7*sx}" stroke-linejoin="round"/>
    """
    collar = ""
    if high:
        collar = f"""
          <path d="M {x+220*sx} {y+146*sx}
                   L {x+240*sx} {y+24*sx}
                   C {x+326*sx} {y+0*sx}, {x+416*sx} {y+44*sx}, {x+438*sx} {y+154*sx}
                   C {x+374*sx} {y+132*sx}, {x+288*sx} {y+128*sx}, {x+220*sx} {y+146*sx} Z"
                fill="{p['b']}" stroke="{outsole}" stroke-width="{9*sx}" stroke-linejoin="round"/>
          <circle cx="{x+332*sx}" cy="{y+82*sx}" r="{33*sx}" fill="{p['c']}" stroke="{outsole}" stroke-width="{6*sx}"/>
        """
    eyelets = "\n".join(
        f'<circle cx="{x+(292+i*35)*sx}" cy="{y+(159+i%2*10)*sx}" r="{7*sx}" fill="{outsole}"/>'
        for i in range(6)
    )
    laces = "\n".join(
        f'<path d="M {x+(292+i*35)*sx} {y+(160+i%2*10)*sx} L {x+(340+i*28)*sx} {y+(204-i%2*12)*sx}" stroke="{p["c"]}" stroke-width="{8*sx}" stroke-linecap="round" opacity=".96"/>'
        for i in range(6)
    )
    lights = ""
    if "neon" in variant or "light" in variant or "chunky" in variant:
        lights = "\n".join(
            f'<circle cx="{x+(150+i*80)*sx}" cy="{y+(278+sole_h*.18)*sx}" r="{13*sx}" fill="{p["b"]}" opacity=".95"/>'
            for i in range(6)
        )
    swooshless_speed = ""
    if "runner" in variant or "performance" in variant or "future" in variant:
        swooshless_speed = f"""
          <path d="M {x+126*sx} {y+238*sx} C {x+260*sx} {y+196*sx}, {x+430*sx} {y+184*sx}, {x+588*sx} {y+208*sx}"
                fill="none" stroke="{p['b']}" stroke-width="{20*sx}" stroke-linecap="round" opacity=".75"/>
          <path d="M {x+130*sx} {y+238*sx} C {x+252*sx} {y+220*sx}, {x+434*sx} {y+216*sx}, {x+600*sx} {y+232*sx}"
                fill="none" stroke="{p['c']}" stroke-width="{5*sx}" stroke-linecap="round" opacity=".8"/>
        """
    armor = ""
    if "armored" in variant or "apocalypse" in variant:
        armor = f"""
          <path d="M {x+176*sx} {y+122*sx} L {x+244*sx} {y+72*sx} L {x+270*sx} {y+146*sx} Z" fill="{p['accent']}" stroke="{outsole}" stroke-width="{6*sx}"/>
          <path d="M {x+490*sx} {y+166*sx} L {x+596*sx} {y+122*sx} L {x+558*sx} {y+220*sx} Z" fill="{p['accent']}" stroke="{outsole}" stroke-width="{6*sx}"/>
          <path d="M {x+104*sx} {y+106*sx} C {x+36*sx} {y+70*sx}, {x-44*sx} {y+68*sx}, {x-110*sx} {y+104*sx}"
                stroke="{p['a']}" stroke-width="{10*sx}" fill="none" stroke-linecap="round" opacity=".75"/>
        """
    return f'<g transform="rotate({lean} {x+330*sx} {y+175*sx})">{sole}{upper}{collar}{swooshless_speed}{eyelets}{laces}{lights}{armor}</g>'


def bg_elements(project: str, idx: int, p: dict, world: str) -> str:
    if project == "converse-origin":
        strips = []
        for i in range(9):
            y = 170 + i * 185 + (idx % 2) * 28
            strips.append(
                f'<path d="M -80 {y} C 250 {y-80}, 650 {y+90}, 1180 {y-35}" fill="none" stroke="{p["muted"]}" stroke-width="{42+i%3*14}" opacity=".48"/>'
            )
        dots = "\n".join(
            f'<circle cx="{(i*97+idx*41)%W}" cy="{(i*149+idx*83)%H}" r="{2+i%4}" fill="{p["ink"]}" opacity=".18"/>'
            for i in range(120)
        )
        return "".join(strips) + dots
    if project == "nike-origin":
        grid = []
        for x in range(-200, 1300, 120):
            grid.append(f'<line x1="{x}" y1="0" x2="{x+520}" y2="{H}" stroke="{p["muted"]}" stroke-width="3" opacity=".34"/>')
        for y in range(0, H, 120):
            grid.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{p["muted"]}" stroke-width="2" opacity=".25"/>')
        pulses = "\n".join(
            f'<circle cx="{120+i*150}" cy="{300+(i*211+idx*113)%1150}" r="{40+i%3*25}" fill="none" stroke="{p["a"]}" stroke-width="4" opacity=".35"/>'
            for i in range(7)
        )
        return "".join(grid) + pulses
    if project == "sneaker-wars-2026":
        cracks = []
        for i in range(13):
            x = (i * 117 + idx * 61) % W
            cracks.append(
                f'<path d="M {x} {-40} L {x-80+(i%5)*35} {440+i*70} L {x+70-(i%4)*20} {880+i*50} L {x-30} {H+40}" fill="none" stroke="{p["a" if i%2 else "b"]}" stroke-width="{2+i%3}" opacity=".28"/>'
            )
        alerts = "\n".join(
            f'<circle cx="{(i*173+idx*89)%W}" cy="{(i*211+idx*47)%H}" r="{22+i%4*18}" fill="none" stroke="{p["accent"]}" stroke-width="4" opacity=".22"/>'
            for i in range(16)
        )
        return "".join(cracks) + alerts
    bars = []
    for i in range(12):
        x = -80 + i * 115
        bars.append(f'<rect x="{x}" y="0" width="54" height="{H}" fill="{p["a" if i%2 else "b"]}" opacity="{0.08 + (i%3)*0.04}" transform="skewX(-12)"/>')
    stars = "\n".join(
        f'<path d="M {((i*83+idx*59)%W)} {((i*137+idx*101)%H)} l 12 28 l 28 12 l -28 12 l -12 28 l -12 -28 l -28 -12 l 28 -12 Z" fill="{p["accent"]}" opacity=".38"/>'
        for i in range(24)
    )
    return "".join(bars) + stars


def make_svg(project: str, idx: int, sid: str, world: str, variant: str, note: str) -> str:
    p = PALETTES[project]
    grad = f"g{idx}"
    lean = [-7, 5, -3, 8, -9, 4][idx % 6]
    x = 235 + math.sin(idx * 1.7) * 45
    y = 760 + math.cos(idx * 1.2) * 90
    scale = 0.9 if project != "la-gear-origin" else 0.96
    if project == "sneaker-wars-2026":
        scale = 0.92
        if idx >= 4:
            x += math.sin(idx) * 80
            y += 70
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="{grad}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{p['bg']}"/>
      <stop offset=".55" stop-color="{p['muted']}"/>
      <stop offset="1" stop-color="{p['b']}"/>
    </linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#{grad})"/>
  <circle cx="{220+idx*95%760}" cy="{300+idx*170%980}" r="360" fill="{p['a']}" opacity=".18" filter="url(#soft)"/>
  <circle cx="{840-idx*71%640}" cy="{1330-idx*97%900}" r="310" fill="{p['b']}" opacity=".24" filter="url(#soft)"/>
  {bg_elements(project, idx, p, world)}
  <path d="M 40 1390 C 270 1290, 760 1290, 1040 1425 L 1040 1920 L 40 1920 Z" fill="#000" opacity=".18"/>
  {sneaker(x, y, scale, p, variant, lean)}
  {sneaker(x-310, y+90, scale*.58, {**p, 'a': p['b'], 'b': p['accent']}, 'runner prototype' if project == 'sneaker-wars-2026' and idx >= 4 else 'shadow sneaker', -lean*.7) if project == 'sneaker-wars-2026' and idx >= 4 else ''}
  {sneaker(x+340, y+125, scale*.54, {**p, 'a': p['accent'], 'b': p['a']}, 'chunky light up fashion sneaker' if project == 'sneaker-wars-2026' and idx >= 4 else 'shadow sneaker', lean*.5) if project == 'sneaker-wars-2026' and idx >= 4 else ''}
  <g opacity=".18" font-family="Arial Black, Arial, sans-serif" font-weight="900" fill="{p['ink']}">
    <text x="70" y="1740" font-size="78">{esc(world.upper())}</text>
    <text x="72" y="1816" font-size="38">{esc(note.upper())}</text>
  </g>
</svg>
"""


def convert(svg: Path, png: Path) -> None:
    """Rasterize with ImageMagick.

    This is the one program here that needs `magick`, and nothing else in the
    repo does — it is not in doctor's TOOLS list and no extra can install it,
    because it is a system binary rather than a Python package. Say so plainly
    rather than surfacing a bare FileNotFoundError that names neither the tool
    nor the fix. The SVG is already written at this point and is usable on its
    own, so the failure is recoverable.
    """
    try:
        subprocess.run(["magick", str(svg), "-resize", f"{W}x{H}!", str(png)], check=True)
    except FileNotFoundError:
        raise SystemExit(
            f"ImageMagick is not installed, so {svg.name} could not be rasterized.\n"
            f"The SVG itself was written to {svg} and is usable as-is.\n"
            f"For PNGs: brew install imagemagick (macOS), or apt install imagemagick."
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    project = args.project
    if project not in SCENES:
        raise SystemExit(f"unknown project {project}")
    root = Path(project)
    clips = root / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    made = []
    for idx, (sid, world, variant, note) in enumerate(SCENES[project]):
        svg = clips / f"{sid}-still.svg"
        png = clips / f"{sid}-still.png"
        svg.write_text(make_svg(project, idx, sid, world, variant, note))
        convert(svg, png)
        made.append(str(png))
    print(json.dumps({"project": project, "assets": made}, indent=2))


if __name__ == "__main__":
    main()
