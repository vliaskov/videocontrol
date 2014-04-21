#!/usr/bin/env python
"""
The Ramp class.
"""
import time

def map_float(value, istart, istop, ostart, ostop):
    """
    Convenience function to map a variable from one coordinate space
    to another.

    The result is clipped in the range [ostart, ostop]
    Make sure ostop is bigger than ostart.

    To map a MIDI control value into the [0,1] range:
    map_float(value, 0.0, 1.0, 0. 127.);
    """
    # FIXME: Should not require that ostop is bigger than ostart.
    ret = ostart + (ostop - ostart) * ((value - istart) / (istop - istart))
    # In Processing, they don't do the following: (clipping)
    return max(min(ret, ostop), ostart)


class Ramp(object):
    """
    Ramp generator.
    A number that goes from n to m in a given number of seconds.
    """
    def __init__(self):
        self._duration = 0.0
        self._start_time = 0.0
        self._current = 0.0
        self._start_point = 0.0
        self._end_time = 0.0
        self._target = 0.0

    def start(self, target, duration=0.0, now=None):
        if now is None:
            now = time.time()

        # Do this first:
        self._current = self.poll(now)
        # Then the rest:
        self._target = target
        self._start_point = self._current
        self._start_time = now
        self._duration = duration
        self._end_time = self._start_time + self._duration

    def is_done(self, now=None):
        if now is None:
            now = time.time()
        return now >= self._end_time or self._duration <= 0.0001

    def jump_to_(self, value, now=None):
        if now is None:
            now = time.time()
        self._current = value
        self._start_point = value
        self._target = value
        self._duration = 0.0

    def poll(self, now=None):
        if now is None:
            now = time.time()
        
        if self.is_done(now):
            return self._target
        else:
            elapsed = now - self._start_time
            ratio = elapsed / self._duration

            if self._target >= self._start_point:
                ret = map_float(ratio, 0.0, 1.0, self._start_point, self._target)
            else:
                ret = map_float(ratio, 1.0, 0.0, self._target, self._start_point)
            self._current = ret
            return ret


