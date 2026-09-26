V13 GitHub update packet
Date: 2026-09-26
Base main HEAD: b57be8e619254191f3a54da86bec3745edae6ac8

Purpose
-------
Start V13 as a clean HA-only rebuild and add the frozen Baseline-0 MT5 EA.

Apply
-----
1. Refresh/checkout awindboy/Trading main.
2. Confirm HEAD is the expected base above or review intervening changes.
3. Extract this ZIP at repository root, preserving paths.
4. Review git diff.
5. Compile mt5/experts/V13HAOnlyMax10EA.mq5 in MetaEditor.
6. Run the canonical full-window tester protocol.
7. Add the compact tester receipt under docs/ea/v13/results/ before any strategy change.

This packet intentionally does not include generated XLSX ledgers or old V10-V12
feature code.
