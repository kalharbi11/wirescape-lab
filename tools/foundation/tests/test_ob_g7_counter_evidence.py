# SPDX-License-Identifier: GPL-3.0-only
"""Run the OB-g7 counter evidence regressions on draft and ready Lab heads."""
import importlib.util
from pathlib import Path
import sys
import unittest

io_dir = Path(__file__).resolve().parents[3] / 'bench' / 'io'
sys.path.insert(0, str(io_dir))
try:
    spec = importlib.util.spec_from_file_location('ob_g7_counter_evidence', io_dir / 'test_counter_evidence.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
finally:
    sys.path.remove(str(io_dir))

CounterEvidenceTests = module.CounterEvidenceTests

if __name__ == '__main__':
    unittest.main()
