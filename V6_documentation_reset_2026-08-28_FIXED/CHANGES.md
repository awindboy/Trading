# V6 documentation reset — apply pack

This pack corrects V6 from a single-child `GOLD+XAUEUR+USDJPY vs GOLDx3` routing into the intended V3-generalization research program.

## Main corrections

1. Adds a permanent V3/V5 lineage and failure synthesis.
2. Makes V3 failure multi-causal/falsifiable rather than assuming hidden context.
3. Defines V6 indicators as causal measurements of named market-state hypotheses.
4. Prohibits broad indicator/window/threshold tournaments.
5. Adds a parent context-measurement registry with semantic families.
6. Reclassifies V6-001A as one queued cross-market child, not the V6 definition or fatal gate.
7. Preserves the exact V6-001A same-capacity falsifier.
8. Carries V5 recursive falsification into V6 governance.
9. Corrects root AGENTS/HANDOFF routing only when their exact Git blob identities match the verified repository state.

## Important interpretation

This update does NOT claim hidden context is already proven to be V3's failure cause.

V6 keeps competing explanations open:

- selection/multiplicity;
- covariate shift;
- hidden/omitted context;
- concept shift;
- event-formulation insufficiency;
- execution environment.

## Apply

From the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\apply_v6_doc_reset.ps1
```

The script fails closed unless:

- HEAD is exactly `03d0e893d74e23779a9188e9e91fd0659837dc03`;
- working tree is clean;
- all expected existing file Git blob hashes match;
- the two new V6 files do not already exist;
- the exact old root routing blocks are present.

It does not commit or push automatically.

After applying:

```powershell
git diff --check
git diff --stat
git diff
git add AGENTS.md docs/ea/HANDOFF.md docs/ea/v6
git commit -m "V6 correct context-measurement research authority"
git push
```

Then the next session must re-read the latest GitHub state.

## Windows PowerShell Korean-path fix

The apply script now finds the repository by walking upward from its own directory instead of parsing `git rev-parse --show-toplevel`. This avoids Windows PowerShell native-command encoding corruption such as `문서` becoming `臾몄꽌`.
