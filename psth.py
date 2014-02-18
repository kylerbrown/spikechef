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
        plt.plot(x, psth, alpha=.5, linewidth=2)
    return x, psth


def main(spk_f, arf_f=None, save=False):
    sampling_rate = 30000
    XMAX = 4
    # find unique stimuli
    stim_entries = [(ename, entry) for ename, entry in spk_f.items()
                    if isinstance(entry, h5py.Group)
                    and 'stimulus' in entry.attrs]
    stimuli = set([entry.attrs['stimulus'] for ename, entry in stim_entries])
    # determine spike groups (good, mua, noise)
    #neuron_group_names = spk_f['groups_of_clusters']
    pgoff = pandas.DataFrame(spk_f['groups_of_clusters'].value)
    #shanks = pgoff['shank']
    #raw_names = pgoff[[x for x in pgoff.columns is x != 'shank']]
    #neuron_group_names = {spiken: name for spiken, name in
    #                      [x for x raw_names]}
    #neuron_group_names = {0: 'Noise', 1: 'MUA', 2: 'Good', 3:'Unsorted'}
    neuron_group_names = {k: v for k, v in
                          [x for bee in pgoff[pgoff.columns[:-1]]
                           for x in pgoff[bee]]}  # ugly
    # for each unique stimuli, plot raw data
    for neuron_N, group, shank in spk_f['clusters']:
        group_name = neuron_group_names[group]
        if group_name == 'Noise':
            continue
        fig = plt.figure(neuron_N)
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

                id_mask = trial['spikes']['cluster_manual'] == neuron_N
                pulse = trial.attrs['pulse']
                times = (trial['spikes']['start'][id_mask]
                         .astype(float) - pulse) / sampling_rate
                spike_times.append(times)
                #print(times)
                plt.vlines(times, itrial, itrial+1)
                plt.xlim(0, XMAX)
                if arf_f and itrial % 5 == 0:
                    plt.subplot(Nstim * 2, 1, istim * 2 + 1)
                    stimdata = arf_f[tname]['pcm_033'][pulse:pulse + XMAX
                                                       * sampling_rate]
                    stimx = np.arange(len(stimdata)) / sampling_rate
                    plt.plot(stimx, stimdata)
                    plt.title("neuron: {}, group: {}, stim:{}"
                              .format(neuron_N, group_name, stim))
                    plt.subplot(Nstim * 2, 1, istim * 2 + 2)
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
    parser.add_argument('--arf',
                        help='original arf file', default='', type=str)
    parser.add_argument('--save', help="save to disk instead of showing",
                        action='store_true')
    args = parser.parse_args()
    spk_f = h5py.File(args.spike, 'r')
    arf_f = h5py.File(args.arf, 'r') if args.arf is not '' else None
    print(arf_f)
    main(spk_f, arf_f, args.save)



















