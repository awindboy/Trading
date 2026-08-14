"""Classify every rejected ambiguous June delivery-FVG family."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "output/mentor_june2026_causal_benchmark"

LABELS = {
    "CHILD": "동일 map/root/objective에 causal child OB가 복수",
    "ROOT+CHILD": "동일 scope/objective에 HTF root와 child lineage가 복수",
    "SCOPE+OBJECTIVE": "동일 root/child에 internal rotation과 external continuation이 동시 성립",
    "SCOPE+CHILD+OBJECTIVE": "root는 같지만 scope/objective와 child가 동시에 충돌",
    "SCOPE+ROOT+CHILD+OBJECTIVE": "map scope, HTF 원인, refinement, objective가 모두 충돌",
}


def main() -> int:
    source = json.loads(
        (RUN / "strict_delivery_replacement_ambiguous_families.json").read_text(encoding="utf-8")
    )
    rows = []
    for number, family in enumerate(source, 1):
        columns = list(zip(*family["lineages"]))
        names = ["SCOPE", "ROOT", "CHILD", "OBJECTIVE"]
        values = {name: sorted(set(column)) for name, column in zip(names, columns)}
        category = "+".join(name for name in names if len(values[name]) > 1)
        formed_epoch = int(family["formedBarId"].split(":", 1)[1]) + 60
        formed = datetime.fromtimestamp(formed_epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        rows.append({
            "familyId": f"J26-AMB-{number:03d}",
            "direction": family["direction"],
            "fvgFormedAtUtc": formed,
            "fvgBarId": family["formedBarId"],
            "firstRetestAtUtc": family["filledAtUtc"],
            "category": category,
            "exclusionReasonKo": LABELS[category],
            "lineageVariantCount": family["lineageVariantCount"],
            "scopeCount": len(values["SCOPE"]),
            "rootCount": len(values["ROOT"]),
            "childCount": len(values["CHILD"]),
            "objectiveCount": len(values["OBJECTIVE"]),
            "scopes": ";".join(values["SCOPE"]),
            "rootObBarIds": ";".join(values["ROOT"]),
            "childObBarIds": ";".join(values["CHILD"]),
            "objectiveBarIds": ";".join(values["OBJECTIVE"]),
            "lineagesJson": json.dumps(family["lineages"], ensure_ascii=False),
        })

    output = RUN / "ambiguous_delivery_family_classification.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
    report = [
        "# June 2026 Ambiguous Delivery-FVG Families",
        "",
        "These families passed the mechanical replacement chain but were rejected because the same physical FVG/retest had more than one causal interpretation.",
        "",
        "| Category | Families | Meaning |",
        "| --- | ---: | --- |",
    ]
    for category, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        report.append(f"| {category} | {len(items)} | {LABELS[category]} |")
    for category, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        report.extend([
            "", f"## {category}", "",
            "| Family | FVG formed | First retest | Variants | Roots | Children | Objectives |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ])
        for row in items:
            report.append(
                f"| {row['familyId']} | {row['fvgFormedAtUtc']} | {row['firstRetestAtUtc']} | "
                f"{row['lineageVariantCount']} | {row['rootCount']} | {row['childCount']} | "
                f"{row['objectiveCount']} |"
            )
    (RUN / "AMBIGUOUS_DELIVERY_FAMILY_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "families": len(rows),
        "categories": {key: len(value) for key, value in grouped.items()},
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
