#!/usr/bin/env python3
"""Render the compact V12 Phase-1A comparison figure from output CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1800
HEIGHT = 1200
BG = "#0b1020"
PANEL = "#141c31"
TEXT = "#eef3ff"
MUTED = "#aebbd4"
GRID = "#34405c"
POS = "#36c98f"
NEG = "#ff6b78"
V10 = "#6aa9ff"
V12 = "#bd8cff"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    draw.rounded_rectangle(box, radius=24, fill=PANEL, outline=GRID, width=2)
    draw.text((box[0] + 28, box[1] + 22), title, font=font(27, True), fill=TEXT)


def hbar(
    draw: ImageDraw.ImageDraw,
    *,
    x0: int,
    x1: int,
    y: int,
    value: float,
    limit: float,
    color: str,
    label: str,
    value_suffix: str = "",
) -> None:
    center = (x0 + x1) // 2
    half = (x1 - x0) // 2 - 12
    draw.line((center, y - 5, center, y + 30), fill=GRID, width=2)
    width = min(half, int(abs(value) / limit * half)) if limit else 0
    left, right = (center, center + width) if value >= 0 else (center - width, center)
    draw.rounded_rectangle((left, y, right, y + 24), radius=8, fill=color)
    draw.text((x0, y - 2), label, font=font(18), fill=MUTED)
    value_text = f"{value:+.2f}{value_suffix}"
    text_box = draw.textbbox((0, 0), value_text, font=font(18, True))
    tx = right + 8 if value >= 0 else left - (text_box[2] - text_box[0]) - 8
    draw.text((tx, y - 2), value_text, font=font(18, True), fill=TEXT)


def render(output_dir: Path) -> Path:
    comparison = read_csv(output_dir / "V12_PHASE1A_V10_COMPARISON.csv")
    scorecard = read_csv(output_dir / "V12_PHASE1A_SCORECARD.csv")
    counter = read_csv(output_dir / "V12_PHASE1A_COUNTERFACTUAL_SUMMARY.csv")

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((55, 38), "V12 Phase-1A vs V10", font=font(42, True), fill=TEXT)
    draw.text(
        (55, 92),
        "Spreadless structural R | consumed evidence | matched 2024-10-01 to 2026-08-28",
        font=font(22),
        fill=MUTED,
    )

    # Panel 1: exposure-normalized comparison.
    p1 = (45, 145, 910, 720)
    panel(draw, p1, "Matched: return and stopped exposure per 100 funded units")
    labels = {
        "V10_SELECTED_CHILDREN_1U": "V10 selected, 1U",
        "V10_R7G_HISTORICAL_FUNDED_UNITS": "V10 R7G actual units",
        "V12_C3_OPEN_CONTROL_C2_EXTREME_T1": "V12 C3-open control",
        "V12_MODEL1_RELATIVE_THICK_V1_C2_EXTREME_T1": "V12 Model1 + C2 SL",
        "V12_MODEL1_RELATIVE_THICK_V1_TRIGGER_STRUCTURE_T1": "V12 Model1 + trigger SL",
    }
    y = 205
    for row in comparison:
        label = labels[row["strategy"]]
        is_v10 = row["strategy"].startswith("V10")
        net = float(row["net_r_per_100_funded_units"])
        stops = float(row["stopped_units_per_100"])
        fills = int(float(row["funded_units"]))
        draw.text((73, y), f"{label}  (units={fills})", font=font(20, True), fill=V10 if is_v10 else V12)
        hbar(draw, x0=350, x1=870, y=y + 4, value=net, limit=50.0, color=POS if net >= 0 else NEG, label="")
        draw.text((75, y + 31), f"stopped units / 100: {stops:.1f}", font=font(17), fill=MUTED)
        y += 96

    # Panel 2: annual instability of the attractive recent variant.
    p2 = (940, 145, 1755, 720)
    panel(draw, p2, "Model1 + trigger SL: annual T1 result")
    annual = [
        row
        for row in scorecard
        if row["scope"] == "FULL_CONSUMED"
        and row["family"] == "MODEL1_RELATIVE_THICK_V1"
        and row["risk_variant"] == "TRIGGER_STRUCTURE"
        and row["target"] == "T1"
        and row["slice_type"] == "YEAR"
    ]
    y = 222
    for row in annual:
        value = float(row["net_r"])
        fills = int(row["filled_children"])
        draw.text((980, y - 2), f"{row['slice_value']}  n={fills}", font=font(18), fill=MUTED)
        hbar(
            draw,
            x0=1160,
            x1=1695,
            y=y,
            value=value,
            limit=8.0,
            color=POS if value >= 0 else NEG,
            label="",
            value_suffix="R",
        )
        y += 88
    draw.text((980, 657), "Positive result is confined to 2025-2026.", font=font(19, True), fill="#ffd166")

    # Panel 3: mechanism audit.
    p3 = (45, 750, 1755, 1135)
    panel(draw, p3, "Counterfactual mechanism audit")
    headers = ["Scope / mechanism", "Fills blocked", "Blocked baseline net", "Common-fill delta", "Meaning"]
    xs = [75, 515, 755, 1030, 1295]
    for x, value in zip(xs, headers):
        draw.text((x, 810), value, font=font(18, True), fill=MUTED)
    y = 855
    for row in counter:
        scope = "Full" if row["scope"] == "FULL_CONSUMED" else "Matched"
        effect = "confirmation" if row["effect"] == "CONFIRMATION_EFFECT" else "trigger-stop guard"
        blocked = int(row["incrementally_blocked_a_fills"])
        blocked_net = float(row["blocked_a_net_r"])
        common_delta = float(row["common_net_r_delta_b_minus_a"])
        meaning = (
            "avoids stops, but entry delay costs more"
            if row["effect"] == "CONFIRMATION_EFFECT"
            else "recently selective; not stable over full history"
        )
        draw.text((xs[0], y), f"{scope}: {effect}", font=font(19, True), fill=TEXT)
        draw.text((xs[1], y), str(blocked), font=font(19), fill=TEXT)
        draw.text((xs[2], y), f"{blocked_net:+.2f}R", font=font(19), fill=POS if blocked_net < 0 else NEG)
        draw.text((xs[3], y), f"{common_delta:+.2f}R", font=font(19), fill=POS if common_delta > 0 else NEG)
        draw.text((xs[4], y), meaning, font=font(18), fill=MUTED)
        y += 62

    draw.text(
        (55, 1160),
        "Research conclusion: Phase-1A is reproducible, but it does not establish a robust replacement for V10.",
        font=font(20, True),
        fill="#ffd166",
    )
    path = output_dir / "V12_PHASE1A_SUMMARY.png"
    image.save(path, format="PNG", optimize=True)
    return path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "output" / "v12_phase1a_no_ml_baseline_20260923"
    path = render(default)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
