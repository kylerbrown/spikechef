from spikechef import label_stim

import numpy as np

no_pulse = np.zeros(100)

one_pulse = no_pulse.copy()
one_pulse[10:13] = 1

two_pulse = one_pulse.copy()
two_pulse[14:17] = 2


class Test_detect_pulse:
    def test_no_pulse(self):
        assert len(label_stim.detect_pulse(no_pulse)) == 0

    def test_one_pulse(self):
        assert len(label_stim.detect_pulse(one_pulse)) == 1

    def test_one_timing(self):
        assert label_stim.detect_pulse(one_pulse)[0] == 10

    def test_two_pulse(self):
        assert len(label_stim.detect_pulse(two_pulse)) == 2

    def test_two_pulse_timing(self):
        assert label_stim.detect_pulse(two_pulse)[0] == 10
        assert label_stim.detect_pulse(two_pulse)[1] == 14
