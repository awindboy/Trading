#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import scripts.v9_ict_object_engine as eng


class ObjectEngineTests(unittest.TestCase):
    def test_bullish_fvg_exact_geometry_and_fill(self):
        bars=[
            eng.Bar(datetime(2025,1,1,0),60,100,101,99,100),
            eng.Bar(datetime(2025,1,1,1),60,100,105,100,104),
            eng.Bar(datetime(2025,1,1,2),60,104,108,102,107), # 101 < 102 => FVG 101-102
            eng.Bar(datetime(2025,1,1,3),60,107,107.5,101.5,102), # touch only
            eng.Bar(datetime(2025,1,1,4),60,102,103,100.5,101), # full fill
        ]
        m1_rows=[
            (datetime(2025,1,1,3,15),102,103,101.5,102),
            (datetime(2025,1,1,4,20),101.5,102,100.5,101),
        ]
        x=eng.fvg_candidates(bars,"H1",datetime(2025,1,1,4,59),m1_rows,[r[0] for r in m1_rows])
        f=[o for o in x if o.direction=="BULL"][0]
        self.assertEqual(f.price_low,101)
        self.assertEqual(f.price_high,102)
        self.assertEqual(f.first_touch_at,"2025-01-01 03:15:00")
        self.assertEqual(f.full_fill_at,"2025-01-01 04:20:00")
        self.assertEqual(f.geometric_state,"FULLY_FILLED")

    def test_liquidity_raid_lifecycle(self):
        bars=[
            eng.Bar(datetime(2025,1,1,h),60,100,100+h,90,95) for h in range(6)
        ]
        swing=eng.Obj("X","H1","SWING","HIGH","2025-01-01 01:00:00",None,
                      "2025-01-01 01:00:00","2025-01-01 03:59:00",101,101)
        m1_rows=[(datetime(2025,1,1,4,10),100,102,99,101)]
        liq=eng.liquidity_candidates(bars,[swing],"H1",datetime(2025,1,1,5,59),m1_rows,[r[0] for r in m1_rows])[0]
        self.assertEqual(liq.geometric_state,"RAIDED")
        self.assertIsNotNone(liq.raid_at)


if __name__=="__main__": unittest.main()
