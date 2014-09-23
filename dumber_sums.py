#!/usr/bin/python

from __future__ import division, unicode_literals
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
import h5py
import arf_vis_tools.arf_utils as arf_utils
from scipy.signal import filtfilt, butter


def dumber_sums(arf):


    data_entry_name = arf_utils.data_entry_name(arf)
    data = arf[data_entry_name]
    try:
        stimuli = data["stimulus_time"]
    except KeyError:
        raise KeyError("no dataset called stimulus_time in {}, run label_stim first"
                       .format(data.name))

    stim_names = list(set(stimuli["name"]))

    datasets = [x for x in arf_utils.entry_time_series_datasets(data)
                if ("A-0" in x.name) or ("B-0" in x.name)]
    sampling_rate = datasets[0].attrs["sampling_rate"]

    for stim_name  in stim_names:
        stim_data = arf['stimuli'][stim_name]  # get actual pcm data of stimulus
        stim_t = np.arange(len(stim_data)) / stim_data.attrs["sampling_rate"]
        fig, axs = plt.subplots(2, 1, sharex=True)
        plt.subplots_adjust(hspace=0)
        plt.title(stim_name)
        axs[0].plot(stim_t, stim_data)  
        # create psth from .5 seconds before stimulus to .5 after
        psth_buffer_length = int(0.5 * sampling_rate)
        psth_stim_length = int(len(stim_data) / stim_data.attrs["sampling_rate"]
                               * sampling_rate)
        psth_index =  np.arange(2 * psth_buffer_length + psth_stim_length) - psth_buffer_length
        psth_t = psth_index / sampling_rate
        data_sums = [np.zeros_like(psth_index) for x in datasets]
        presentation_times = stimuli["start"][stimuli["name"]==stim_name]
        hb, ha = butter(2, 400 / (sampling_rate / 2), "highpass")
        lb, la = butter(2, 200 / (sampling_rate / 2), "lowpass")
        for i, dataset in enumerate(datasets):
            for presentation_time in presentation_times:

                temp_data = dataset[psth_index[0] + presentation_time:
                                        psth_index[-1] + presentation_time + 1]
                data_sums[i] += filtfilt(lb, la, np.abs(filtfilt(hb, ha, temp_data)))

        data_means = [x / len(presentation_times) for x in data_sums]

        cum_maxes = np.cumsum([max(x) for x in data_means])
        plot_offset = np.hstack(([0], cum_maxes))[:-1] / 2
        [axs[1].plot(psth_t, x + offset) for x, offset in zip(data_means, plot_offset)]
        plt.xlim(psth_t[0], psth_t[-1])
        plt.show()
    


def main():
    p = argparse.ArgumentParser(prog="dumber_sums.py",
                                description="""Simple and relatively fast plotting to check
                                for stimulus response prior to spike sorting""")
    p.add_argument("arf", help="name of the arf file")
    args = p.parse_args()
    with h5py.File(args.arf, 'r') as arf:
        dumber_sums(arf)

if __name__ == "__main__":
    sys.exit(main())
