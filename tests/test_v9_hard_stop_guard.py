#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'v9_hard_stop_guard.py'
HEADER='<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n'
ROWS='''2025.05.01	01:00:00	100	101	99	100.5	1	0	10
2025.05.01	01:01:00	100.5	102	100	101.5	1	0	10
2025.05.01	01:02:00	101.5	103	98	99	1	0	10
2025.05.01	01:03:00	99	105	97	104	1	0	10
'''

class GuardTest(unittest.TestCase):
    def run_cli(self,*args,expect=0):
        cp=subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)
        self.assertEqual(cp.returncode,expect,cp.stdout+'\n'+cp.stderr); return cp
    def test_long_first_touch(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.tsv'; p.write_text(HEADER+ROWS,encoding='utf-8')
            cp=self.run_cli('--input',str(p),'--side','LONG','--stop','99','--active-after','2025-05-01 01:00:00')
            d=json.loads(cp.stdout); self.assertTrue(d['stop_touched']); self.assertEqual(d['touch_timestamp'],'2025-05-01 01:02:00')
    def test_short_first_touch(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.tsv'; p.write_text(HEADER+ROWS,encoding='utf-8')
            cp=self.run_cli('--input',str(p),'--side','SHORT','--stop','102.5','--active-after','2025-05-01 01:00:00')
            d=json.loads(cp.stdout); self.assertEqual(d['touch_timestamp'],'2025-05-01 01:02:00')
    def test_refuses_through_beyond_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.tsv'; p.write_text(HEADER+ROWS,encoding='utf-8')
            cp=self.run_cli('--input',str(p),'--side','LONG','--stop','90','--active-after','2025-05-01 01:00:00','--through','2025-05-01 02:00:00',expect=2)
            self.assertIn('before requested through',cp.stderr)
if __name__=='__main__': unittest.main()
