#!/usr/bin/env python3
"""Render a compact Phase-1B evidence card with Pillow only."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BG, PANEL, TEXT, MUTED = "#10131a", "#171c26", "#eef2f7", "#aab2c0"
BLUE, RED, GREEN = "#4dabf7", "#ff6b6b", "#51cf66"


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def score_value(score: list[dict], dimension: str, group: str, metric: str) -> float:
    return float(next(row["value"] for row in score if row["dimension"] == dimension and row["group"] == group and row["metric"] == metric))


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    draw.rounded_rectangle(box, radius=18, fill=PANEL)
    draw.text((box[0] + 24, box[1] + 18), title, fill=TEXT, font=font(23, True))


def render(root: Path, output: Path) -> None:
    score = rows(root / "V12_PHASE1B_SCORECARD.csv")
    flip_d = {row["flip_id"]: row for row in rows(root / "V12_PHASE1B_NHA_DECISION_CONTEXT.csv")}
    flip_o = rows(root / "V12_PHASE1B_NHA_OUTCOME_LINK.csv")
    image = Image.new("RGB", (1800, 1080), BG)
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "V12 Phase-1B  |  CRT Journey x frozen V10", fill=TEXT, font=font(35, True))
    draw.text((56, 82), "Causal H4 to M5 study | consumed evidence | no trade or sizing authority", fill=MUTED, font=font(17))

    boxes = [(50, 125, 875, 560), (925, 125, 1750, 560), (50, 600, 1120, 1030), (1170, 600, 1750, 1030)]
    panel(draw, boxes[0], "Frozen V10 Child relation")
    relations = ["ALIGNED_ACTIVE_JOURNEY", "NO_ACTIVE_JOURNEY", "OPPOSED_ACTIVE_JOURNEY"]
    labels = ["ALIGNED", "NEUTRAL", "OPPOSED"]
    stops = [score_value(score, "relation", group, "stopped_units_per_100_funded") for group in relations]
    returns = [score_value(score, "relation", group, "weighted_R_per_100_funded") for group in relations]
    maximum = max(stops + returns) * 1.15
    for i, label in enumerate(labels):
        x = 95 + i * 250
        draw.text((x + 25, 512), label, fill=MUTED, font=font(16, True))
        for offset, value, color, short in ((0, stops[i], RED, "STOP"), (78, returns[i], BLUE, "R")):
            height = int(285 * value / maximum)
            draw.rectangle((x + offset, 500 - height, x + offset + 58, 500), fill=color)
            draw.text((x + offset, 474 - height), f"{value:.1f}", fill=TEXT, font=font(15, True))
            draw.text((x + offset + 8, 502), short, fill=MUTED, font=font(12))
    draw.text((620, 165), "per 100 funded units", fill=MUTED, font=font(14))

    panel(draw, boxes[1], "FAST flip to next-run k1 stop rate")
    states = ["OPPOSITE_CRT_AUTHORIZED", "OLD_JOURNEY_AFTER_KEY_ARRIVAL", "OLD_JOURNEY_COUNTERFLOW", "OLD_JOURNEY_FAILED_NO_OPPOSITE", "NEUTRAL_ROTATION"]
    state_labels = ["Opposite CRT authorized", "Old journey after key", "Old journey counterflow", "Old failed, no opposite", "Neutral rotation"]
    colors = [GREEN, "#ffd43b", "#ff922b", "#f06595", "#9775fa"]
    for i, (state, label, color) in enumerate(zip(states, state_labels, colors)):
        rate = 100 * score_value(score, "explanation_state", state, "linked_k1_stop_rate")
        count = int(score_value(score, "explanation_state", state, "linked_v10_k1"))
        y = 205 + i * 65
        draw.text((960, y), label, fill=TEXT, font=font(15))
        draw.rectangle((1245, y + 2, 1245 + int(rate * 8.1), y + 27), fill=color)
        draw.text((1585, y), f"{rate:4.1f}%  n={count}", fill=MUTED, font=font(15, True))

    panel(draw, boxes[2], "Stop separation persists by year")
    yearly: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for outcome in flip_o:
        if not outcome["linked_v10_k1_R"]:
            continue
        decision = flip_d[outcome["flip_id"]]
        year = decision["known_at"][:4]
        group = "AUTH" if decision["explanation_state"] == "OPPOSITE_CRT_AUTHORIZED" else "NOAUTH"
        yearly[(year, group)][0] += 1
        yearly[(year, group)][1] += int(outcome["linked_v10_k1_stop_hit"])
    years = sorted({year for year, _ in yearly})
    chart = (105, 705, 1065, 955)
    draw.line((chart[0], chart[3], chart[2], chart[3]), fill="#5b6472", width=2)
    draw.line((chart[0], chart[1], chart[0], chart[3]), fill="#5b6472", width=2)
    for pct in (20, 30, 40):
        y = chart[3] - int((pct - 10) / 35 * (chart[3] - chart[1]))
        draw.line((chart[0], y, chart[2], y), fill="#293140", width=1)
        draw.text((62, y - 10), f"{pct}%", fill=MUTED, font=font(13))
    for group, color in (("AUTH", GREEN), ("NOAUTH", RED)):
        points = []
        for i, year in enumerate(years):
            rate = 100 * yearly[(year, group)][1] / yearly[(year, group)][0]
            x = chart[0] + int(i * (chart[2] - chart[0]) / (len(years) - 1))
            y = chart[3] - int((rate - 10) / 35 * (chart[3] - chart[1]))
            points.append((x, y))
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
            draw.text((x - 20, chart[3] + 12), year, fill=MUTED, font=font(13))
        draw.line(points, fill=color, width=4)
    draw.text((125, 975), "CRT authorized", fill=GREEN, font=font(15, True))
    draw.text((290, 975), "Not authorized", fill=RED, font=font(15, True))

    panel(draw, boxes[3], "Causal pack")
    facts = [
        ("2,649", "CRT journeys"), ("88.2%", "H4 coverage"), ("8h", "median duration"),
        ("70.9%", "forward midpoint hit"), ("44.7%", "forward opposite edge hit"),
        ("1,649", "R7G Children unchanged"), ("+741.01R", "frozen result preserved"),
    ]
    for i, (value, label) in enumerate(facts):
        y = 675 + i * 47
        draw.text((1210, y), value, fill=BLUE, font=font(21, True))
        draw.text((1390, y + 4), label, fill=TEXT, font=font(15))
    draw.text((1210, 997), "2 independent runs | byte-identical", fill=MUTED, font=font(14))

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.root, args.output)


if __name__ == "__main__":
    main()
