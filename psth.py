#!/usr/bin/python

from __future__ import division
import argparse
import h5py
import pandas
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import gaussian
description = '''
goals: display a peristimulus time histogram for data in a spike-sorted
arf file.
'''


def plot_stim(stim_entry, pulse, XMAX, sampling_rate,
              Nstim, istim, neuron_N, group_name, stim, style='spec'):
    stimdata = stim_entry[pulse:pulse + XMAX
                          * sampling_rate]
    plt.subplot(Nstim * 2, 1, istim * 2 + 1)
    if style == 'spec':
        plt.specgram(stimdata, NFFT=512, noverlap=30, Fs=sampling_rate)
    elif plot_stim == 'osc':
        stimx = np.arange(len(stimdata)) / sampling_rate
        plt.plot(stimx, stimdata)

    plt.title("neuron: {}, group: {}, stim:{}"
              .format(neuron_N, group_name, stim))
    plt.subplot(Nstim * 2, 1, istim * 2 + 2)


def plot_psth(spike_times, sampling_rate=30000,
              trial_duration=None, plot=True, tzero=0):
    '''spike_times: a list of arrays with spike times in seconds
    sampling_rate: sampling rate of convolution process
    trial_duration: length of trial in seconds,
                    else will be last spike time in spike_times'''
    # create spike counts array at high resolution
    if trial_duration:
        counts = np.zeros(trial_duration * sampling_rate)
    else:
        counts = np.zeros(np.max([max(trial + tzero) for trial in spike_times
                                  if len(trial) > 0]) * sampling_rate + 1)
    for trial in spike_times:
        counts[((trial + tzero) * sampling_rate).astype(int)] += 1
    kernelstd = 5               # kernel standard deviation in milliseconds
    kernelstd_samples = kernelstd / 1000. * sampling_rate
    kernel = gaussian(8 * kernelstd_samples, kernelstd_samples)
    psth = np.convolve(kernel, counts, 'same')
    x = np.arange(len(counts)) / sampling_rate - tzero
    if plot:
        plt.plot(x, psth, alpha=.3, linewidth=1, color='r')
    return x, psth


def get_neuron_group_names(spk_f):
    pgoff = pandas.DataFrame(spk_f['groups_of_clusters'].value)
    neuron_group_names = {k: v for k, v in
                          [x for bee in pgoff[pgoff.columns[:-1]]
                           for x in pgoff[bee]]}  # ugly, wrote once,
                           #   afraid to look at
    return neuron_group_names


def main(spk_f, save=False):
    XMAX = 4
    # find unique stimuli
    stim_entries = [(ename, entry) for ename, entry in spk_f.items()
                    if isinstance(entry, h5py.Group)
                    and 'stimulus' in entry.attrs]
    stimuli = set([entry.attrs['stimulus'] for ename, entry in stim_entries])
    # determine spike groups (good, mua, noise)
    neuron_group_names = get_neuron_group_names(spk_f)

    # for each unique stimuli, plot raw data
    for neuron_N, group, shank in spk_f['clusters']:
        group_name = neuron_group_names[group]
        if group_name == 'Noise':
            continue
        plt.figure(neuron_N, figsize=(8, 8), dpi=180)
        Nstim = len(stimuli)
        for istim, stim in enumerate(stimuli):
            associated_trials = [(ename, entry)
                                 for ename, entry in stim_entries
                                 if 'stimulus' in entry.attrs
                                 and stim == entry.attrs['stimulus']]
            associated_trials = sorted(associated_trials, key=repr)
            spike_times = []
            for itrial, (tname, trial) in enumerate(associated_trials):
                plt.subplot(Nstim * 2, 1, istim * 2 + 2)
                plt.title("neuron: {}, group: {}, stim:{}"
                          .format(neuron_N, group_name, stim))

                id_mask = trial['spikes_1']['cluster_manual'] == neuron_N
                pulse = trial['pulse'].value
                sampling_rate = trial['pulse'].attrs['sampling_rate']
                times = (trial['spikes_1']['start'][id_mask]
                         .astype(float) - pulse) / sampling_rate
                spike_times.append(times)
                #print(times)
                plt.vlines(times, itrial, itrial+1)
                plt.xlim(0, XMAX)
                if 'stim' in spk_f[tname] and itrial == 0:
                    plot_stim(spk_f[tname]['stim'], pulse, XMAX, sampling_rate,
                              Nstim, istim, neuron_N, group_name, stim)
            plot_psth(spike_times, sampling_rate)
        plt.tight_layout()
        if not save:
            plt.show()
        else:
            plt.savefig("group_{}_neuron_{:03}.png".format(group_name,
                                                           neuron_N))
            plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--spike',
                        help='arf file containing the spikes',
                        required=True)
    parser.add_argument('--save', help="save to disk instead of showing",
                        action='store_true')
    args = parser.parse_args()
    with h5py.File(args.spike, 'r') as spk_f:
        main(spk_f, args.save)



















