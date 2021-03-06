from stingray.lightcurve import Lightcurve
from stingray.events import EventList
import numpy as np
from hendrics.io import save_events, HEN_FILE_EXTENSION, load_folding
from hendrics.efsearch import main_zsearch
from hendrics.phaseogram import main_phaseogram, run_interactive_phaseogram
from hendrics.phaseogram import BasePhaseogram
from hendrics.plot import plot_folding
import os
import pytest


class TestPhaseogram():
    def setup_class(cls):
        cls.pulse_frequency = 1/0.101
        cls.tstart = 0
        cls.tend = 25.25
        cls.tseg = cls.tend - cls.tstart
        cls.dt = 0.00606
        cls.times = np.arange(cls.tstart, cls.tend, cls.dt) + cls.dt / 2
        cls.counts = \
            100 + 20 * np.cos(2 * np.pi * cls.times * cls.pulse_frequency)
        lc = Lightcurve(cls.times, cls.counts, gti=[[cls.tstart, cls.tend]])
        events = EventList()
        events.simulate_times(lc)
        cls.event_times = events.time
        cls.dum = 'events' + HEN_FILE_EXTENSION
        save_events(events, cls.dum)

    def test_zsearch(self):
        evfile = self.dum
        main_zsearch([evfile, '-f', '9.85', '-F', '9.95', '-n', '64',
                      '--fit-candidates', '--fit-frequency',
                      str(self.pulse_frequency)])
        outfile = 'events_Z2n' + HEN_FILE_EXTENSION
        assert os.path.exists(outfile)
        plot_folding([outfile], ylog=True)
        efperiod = load_folding(outfile)
        assert np.isclose(efperiod.peaks[0], self.pulse_frequency,
                          atol=1/25.25)
        # Defaults to 2 harmonics
        assert efperiod.N == 2

    def test_phaseogram_input_periodogram(self):
        evfile = self.dum
        main_phaseogram([evfile, '--periodogram',
                         'events_Z2n' + HEN_FILE_EXTENSION, '--test'])

    def test_phaseogram_input_f(self):
        evfile = self.dum
        main_phaseogram([evfile, '-f', '9.9', '--test'])

    def test_phaseogram_input_f_change(self):
        evfile = self.dum
        ip = run_interactive_phaseogram(evfile, 9.9, test=True)
        ip.update(1)
        ip.recalculate(1)
        ip.reset(1)
        ip.fdot = 2
        f, fdot, fddot = ip.get_values()
        assert fdot == 2
        assert f == 9.9

    def test_phaseogram_raises(self):
        evfile = self.dum
        with pytest.raises(ValueError):
            main_phaseogram([evfile, '--test'])

    def test_phaseogram_input_periodogram_binary(self):
        evfile = self.dum
        main_phaseogram([evfile, '--binary', '--periodogram',
                         'events_Z2n' + HEN_FILE_EXTENSION, '--test'])

    def test_phaseogram_input_f_binary(self):
        evfile = self.dum
        main_phaseogram([evfile, '--binary', '-f', '9.9', '--test'])

    def test_phaseogram_input_f_change_binary(self):
        evfile = self.dum
        ip = run_interactive_phaseogram(evfile, 9.9, test=True, binary=True)
        ip.update(1)
        ip.recalculate(1)
        ip.reset(1)
        ip.zoom_in(1)
        ip.zoom_out(1)
        ip.orbital_period = 2
        orbital_period, fdot, fddot = ip.get_values()
        assert orbital_period == 2

    def test_phaseogram_raises_binary(self):
        evfile = self.dum
        with pytest.raises(ValueError):
            main_phaseogram([evfile, '--test'])

    @classmethod
    def teardown_class(cls):
        os.unlink(cls.dum)
