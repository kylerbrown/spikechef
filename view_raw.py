
import numpy as np
import matplotlib.pyplot as plt
import h5py
from scipy import signal
from clutoarf import jstim_log_sequence

def geometry(probe_fname):
    """returns the geometry of a probe,
    as a dictionary"""
    geometry = None             # to be redefined by probe_fname
    exec(open(probe_fname, 'r').read())
    return geometry


def get_entries(arf_file):
    entries = [x for x in arf_file.values() if type(x) == h5py.Group]
    return sorted(entries, key=repr)


def get_dsets(entry):
    """returns all raw time series data"""
    datasets = [x for x in entry.values()
                if type(x) == h5py.Dataset
                and 'datatype' in x.attrs.keys()
                and x.attrs['datatype'] < 1000]
    return sorted(datasets, key=repr)


def spike_filter(dset, cutoff=500., sampling_rate=30000.):
    b, a = signal.butter(3, cutoff/(sampling_rate/2.), btype="highpass")
    return signal.filtfilt(b, a, dset)


def dumb_peaks(dset, thresh_f=4.5):
    x = spike_filter(dset)
    #plt.plot(x)

    #_, peaks = peakdetect(x)
    #peakx, peaky = zip(*peaks)
    thresh = -thresh_f * np.std(x)
    #plt.hlines(thresh, 0, len(x))
    crossings = np.arange(len(x-1))[np.diff(np.array(x < thresh,
                                                   dtype=int))==-1]
    return crossings


def plot_dumb_peaks(dsets, xstart, xstop):
    for ith, data in enumerate(dsets):
        x = np.arange(len(data)) / 30000.
        xmask = np.logical_and(x < xstop, x > xstart)
        static_data = data.value[xmask]
        peaks = dumb_peaks(static_data)
        plt.vlines(peaks, ith, ith+1)
        plt.title('dumb threshold')
        plt.ylabel('electrode #')


def plot_raw_data(dsets, xstart=.5, xstop=1.5):
    for ith, data in enumerate(dsets):
        x = np.arange(len(data)) / 30000.
        xmask = np.logical_and(x < xstop, x > xstart)
        plt.plot(x[xmask], 50*spike_filter(data.value[xmask])+ith)
        plt.title('highpass data')
        plt.ylabel('electrode #')
        plt.xlim(xstart, xstop)
        plt.ylim(-1, len(dsets))


def plot_song(song, xstart, xstop):
    x = np.arange(len(song)) / 30000.
    xmask = np.logical_and(x < xstop, x > xstart)
    plt.specgram(song[xmask], Fs=30000)


def dumb_plot(entry):
    """plots every dataset in an entry"""
    pass

if __name__ == '__main__':
    xstart, xstop = .5, 2.5 
    arffile = "/home/kjbrown/projects/spikechef/data/b12/b12-2014_04_11-hvc-7dd0-1-0.arf"
    stims = jstim_log_sequence("/home/kjbrown/projects/spikechef/data/b12/b12-2014_04_11-hvc-7dd0-1-0.stim")
    with h5py.File(arffile, 'r') as arf:
        entries = get_entries(arf)
        for e, stim in zip(entries, stims):
            if stim == 'b12' or True:
                fig = plt.figure(figsize=(15, 15))
                fig.subplots_adjust(wspace=0, hspace=0)
                dsets = get_dsets(e)
                song = dsets[33]

                plt.subplot(311)
                plot_song(song, xstart, xstop)
                plt.title(stim)
                print(stim)

                plt.subplot(3, 1, 2)
                plot_raw_data(dsets[:32], xstop=xstop, xstart=xstart)


                plt.subplot(313)
                plot_dumb_peaks(dsets[:32], xstart, xstop)
                plt.show()
