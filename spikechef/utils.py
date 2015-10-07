import h5py
import numpy as np
from matplotlib import pyplot as plt


def detect_pulse(x):
    '''returns the index of the pulse, assumes single pulse'''
    dx = np.diff(x)
    # +1 is to compensate for diff's method of differentiation
    return np.argmax(dx) + 1


def arf_entries(arf_file):
    entries = [x for x in arf_file.values() if type(x) == h5py.Group]
    return sorted(entries, key=repr)


def entry_time_series_datasets(entry):
    datasets = [x for x in entry.values()
                if type(x) == h5py.Dataset
                and 'datatype' in x.attrs.keys()
                and x.attrs['datatype'] < 1000]
    return sorted(datasets, key=repr)


def jstim_log_sequence(stimlog):
    return [line.split()[-3] for line in open(stimlog, 'r')
            if ' [jstim] next stim: ' in line]


def geometry(probe_fname):
    """returns the geometry of a probe,
    as a dictionary"""
    geometry = None             # to be redefined by probe_fname
    exec(open(probe_fname, 'r').read())
    return geometry


def plot_song(song, xstart, xstop):
    x = np.arange(len(song)) / 30000.
    xmask = np.logical_and(x < xstop, x >= xstart)
    plt.specgram(song[xmask], Fs=30000)


def arf_samplerate(arf_filename):
    if isinstance(arf_filename, h5py.File):
        arf_file = arf_filename
        open_flag = False
    else:
        arf_file = h5py.File(arf_filename, 'r')
        open_flag = True
    for group in arf_file.values():
        if isinstance(group, h5py.Dataset):
            continue
        for dataset in group.values():
            if 'datatype' in dataset.attrs \
               and dataset.attrs['datatype'] < 1000 \
               and 'sampling_rate' in dataset.attrs:
                sampling_rate = dataset.attrs['sampling_rate']
                if open_flag:
                    arf_file.flush()
                    arf_file.close()
                return sampling_rate
