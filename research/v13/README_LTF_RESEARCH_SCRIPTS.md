# Research scripts in this package

These scripts are preserved from the 2026-09-29 research session for audit/reproduction. Most historical session scripts use `/mnt/data/...` absolute paths because that was the execution environment; adjust paths or provide the same mounted filenames before rerunning.

Key lineage:

1. `v13_ltf_ml_research.py` — builds LTF POI/feature universe and outer-year ML studies.
2. `v13_ltf_ml_hurdle.py` — hurdle/tail score research with purged chronological training.
3. `v13_ltf_structural_r.py` — structural target/stop experiment; raw R is unstable when stop distance becomes tiny, so it is diagnostic only.
4. `rebuild_first_breach_ml.py` — reconstructs the first-correction-envelope-breach exit and ML OOF scores.
5. `analyze_overlay.py` — dollar conversion / SA-1 overlay comparison. Packaging fixed the invalid namedtuple access for the `1u_all` column in the concurrency function; no economic formula changed.
6. `staged_proof_eval.py`, `staged_integrated_full.py` — rebreak-proof staged funding, block quality, preperiod stress and concurrency.
7. `proof_ml_eval.py` — conditional proof-stage ML; result is effectively random.
8. `feedback180_eval.py` — direct V10-style 180-H4 feedback transplant; rejected.
9. `replace_addon_eval.py` — direct Child1 + LTF replacement comparison against SA-1 add-ons.

10. The interrupted follow-on session added true all-M30 envelope, strategic
    destination delivery, route-topology and q75/q50 state-machine research.
    Its final script/fold artifacts and event ledger were not saved. Do not infer
    them from the earlier hurdle files or claim exact regeneration.

The package does not claim these scripts are polished production research tooling. They are audit artifacts from the consumed-data investigation.

The execution harness for a regenerated frozen ledger is
`mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5`. It is not an embedded model.
