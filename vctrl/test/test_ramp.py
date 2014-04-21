#!/usr/bin/env python
"""
Unit tests for ramp.py
"""
from .. import ramp
import unittest
import time

class Test_01_Map_Float(unittest.TestCase):
    """
    Test cases for ramp.map_float
    """
    def test_01_map_float(self):
        # From
        istart = 0
        istop = 100
        # To
        ostart = 0
        ostop = 1000

        # Make sure ostop is bigger than ostart.
        expectations = [
            [0, 0],
            [100, 1000]
            ]
        for expectation in expectations:
            arg = expectation[0]
            ret = expectation[1]
            self.assertEqual(ramp.map_float(arg, istart, istop, ostart, ostop), ret)


class Test_02_Ramp(unittest.TestCase):
    """
    Test cases for ramp.Ramp
    """
    def test_01_jump_to(self):
        x = ramp.Ramp()
        x.jump_to_(100.0)
        self.assertEqual(x.poll(now=0.1), 100.0)
        x.jump_to_(200.0)
        self.assertEqual(x.poll(now=0.1), 200.0)

    def test_02_ramp_up(self):
        x = ramp.Ramp()
        x.start(100.0, duration=1.0, now=0.0)
        self.assertEqual(x.poll(now=0.1), 10.0)
        self.assertEqual(x.poll(now=0.2), 20.0)
        self.assertEqual(x.poll(now=1.0), 100.0)
        self.assertEqual(x.poll(now=1.2), 100.0)

    def test_03_ramp_down(self):
        x = ramp.Ramp()
        x.start(100.0, duration=1.0, now=0.0)
        self.assertEqual(x.poll(now=1.2), 100.0)
        x.start(0.0, duration=1.0, now=1.0)
        self.assertEqual(x.poll(now=1.2), 80.0)
        self.assertEqual(x.poll(now=2.0), 0.0)
        self.assertEqual(x.poll(now=2.2), 0.0)

