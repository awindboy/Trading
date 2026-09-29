from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED = [
    "event_id", "action_time", "action_order", "action", "direction",
    "volume", "policy_lane", "reason", "expected_price",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("ledger", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()

    d = pd.read_csv(args.ledger, dtype={"event_id": str})
    assert list(d.columns) == REQUIRED, f"header mismatch: {list(d.columns)}"
    d["action_time"] = pd.to_datetime(d.action_time, format="%Y-%m-%d %H:%M:%S")
    assert d.notna().all().all(), "null field"
    assert d.action.isin(["ENTRY", "EXIT"]).all(), "unknown action"
    assert d.direction.isin(["LONG", "SHORT"]).all(), "unknown direction"
    assert (d.volume.sub(0.01).abs() < 1e-12).all(), "non-fixed volume"
    assert ((d.action.eq("EXIT") & d.action_order.eq(0)) | (d.action.eq("ENTRY") & d.action_order.eq(1))).all(), "action order mismatch"

    ordered = d.sort_values(["action_time", "action_order", "event_id"]).reset_index(drop=True)
    assert d.reset_index(drop=True).equals(ordered), "ledger is not chronologically sorted"
    grouped = d.groupby("event_id", sort=False)
    assert grouped.size().eq(2).all(), "event does not have exactly two actions"
    assert grouped.action.apply(lambda x: set(x) == {"ENTRY", "EXIT"}).all(), "entry/exit pair mismatch"

    entries = d[d.action.eq("ENTRY")].set_index("event_id")
    exits = d[d.action.eq("EXIT")].set_index("event_id")
    paired = entries[["action_time", "direction", "volume", "policy_lane"]].join(
        exits[["action_time", "direction", "volume", "policy_lane"]],
        lsuffix="_entry", rsuffix="_exit", how="inner",
    )
    assert (paired.action_time_entry < paired.action_time_exit).all(), "entry is not before exit"
    assert (paired.direction_entry == paired.direction_exit).all(), "direction changes within event"
    assert (paired.volume_entry == paired.volume_exit).all(), "volume changes within event"
    assert (paired.policy_lane_entry == paired.policy_lane_exit).all(), "lane changes within event"

    receipt = {
        "status": "PASS",
        "ledger": args.ledger.name,
        "sha256": digest(args.ledger),
        "bytes": args.ledger.stat().st_size,
        "rows": len(d),
        "events": len(entries),
        "first_action_time": str(d.action_time.min()),
        "last_action_time": str(d.action_time.max()),
        "lanes": entries.policy_lane.value_counts().sort_index().to_dict(),
        "directions": entries.direction.value_counts().sort_index().to_dict(),
        "same_timestamp_exit_before_entry_groups": int(
            d.groupby("action_time").apply(
                lambda g: int(g.action.eq("EXIT").any() and g.action.eq("ENTRY").any()),
                include_groups=False,
            ).sum()
        ),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
