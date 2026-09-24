# V12 Phase 1J — Within-run causal timeline contract

Status: **frozen before evaluation; consumed-development mechanism diagnostic only**  
Frozen: `2026-09-24`

## Question

Phase 1I showed that repeat-stop runs are a valuable target but that entry-time
classification could not protect the right tail reliably. Phase 1J asks a
different question: **after the first actual entry, but before the first stop or
the first economically large journey is already known, when do the two paths
first become observably different?**

This is not another admission classifier. It tests whether V10 can preserve the
first Child while withholding later exposure, or recognize repair/progression,
from information that appears inside the run.

## Frozen population and labels

- Reuse the Phase 1I funded FAST-run population without changing its run IDs.
- Include only `STOP_ONLY_RUN` and `TAIL_JOURNEY_RUN` in the primary contrast.
- Keep `after_stop_candidate` as a secondary descriptive cohort. Its tail count
  is known to be too small for a policy fit.
- Do not relabel neutral runs or redefine a journey from the Phase 1J path.

## Causal reveal

The timeline begins at the earliest actual Child entry in the run. Completed
M15 bars are reconstructed from the verified raw-M1 prefix.

- A stop-only timeline ends at the earliest stopped Child exit.
- A tail timeline ends at the earliest raw-M1 touch at which one of its final
  tail Children has reached `5` weighted R units.
- The tail touch price is `entry + direction * |entry-stop| * 5 / weight`.
- Only M15 bars whose completion time is strictly earlier than the terminal may
  enter a snapshot.
- Same-M1 ordering is never invented.

All path distances use the first Child's frozen entry-to-Hard-SL distance. This
is normalization, not a signal.

## Frozen observations

At each completed M15 bar, record aligned settlement, cumulative MFE/MAE,
close-path length and efficiency, favorable/opposed dwell, zero crossings,
repairs, streaks, favorable giveback, and how many Children/units had actually
entered by then.

Take one snapshot at each first occurrence of:

1. favorable close;
2. opposed close;
3. favorable repair after an opposed close;
4. two consecutive favorable closes;
5. two consecutive opposed closes;
6. repaired departure beyond the best favorable close that existed before the
   first opposed close.

The first `1`, `2`, `4`, and `8` completed M15 bars are retained only as timing
diagnostics. They cannot become a fixed funding schedule from this phase.

## Interpretation screen

Phase 1J may nominate a mechanism for a later frozen policy test only when:

- each test fold has at least five runs of each class;
- the event occurs in at least 25% of both classes pooled;
- the feature's tail-minus-stop sign agrees in F1, F2, and F3; and
- pooled absolute standardized difference is at least `0.50`, or univariate
  AUC is at least `0.70` after orienting the sign.

Passing this screen means only that a causal mechanism deserves another test.
It grants no veto, exit, retry, allocation, or sizing authority.

## Seals

All GOLD# chronology through `2026-09-18 23:57` is consumed development
evidence. Post-cutoff prices and GOLD# 2021 remain sealed.
