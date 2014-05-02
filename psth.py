#!/usr/bin/python

from __future__ import division
import argparse
import h5py
import pandas
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import gaussian, argrelextrema

description = '''
goals: display a peristimulus time histogram for data in a spike-sorted
arf file.
'''


def minima(a):
    return argrelextrema(a, np.less)[0]

def simple_plot_stim(stim_entry, pulse, XMAX, sampling_rate,
                     style='osc'):
    stimdata = stim_entry[pulse:pulse + XMAX
                          * sampling_rate]
    if style == 'spec':
        plt.specgram(stimdata, NFFT=512, noverlap=500, Fs=sampling_rate)
    elif style == 'osc':
        stimx = np.arange(len(stimdata)) / sampling_rate
        plt.plot(stimx, stimdata)


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

def count_spikes(spike_times):
    '''spike_times is a list trials, each sublist is a list of spike times
    this functions returns true if there are any spikes for the neuron'''
    return sum((len(x) for x in spike_times))

def any_spikes(spike_times):
    return count_spikes(spike_times) > 0

def plot_psth(spike_times, sampling_rate=30000,
              trial_duration=None, plot=True, tzero=0, kernelstd=5):
    '''spike_times: a list of arrays with spike times in seconds
    sampling_rate: sampling rate of convolution process
    trial_duration: length of trial in seconds,
                    else will be last spike time in spike_times'''
    #check if there are any spikes
    if not any_spikes(spike_times):
        print("no spikes")
        return
    # create spike counts array at high resolution
    if trial_duration:
        counts = np.zeros(trial_duration * sampling_rate)
    else:
        counts = np.zeros(np.max([max(trial + tzero) for trial in spike_times
                                  if len(trial) > 0]) * sampling_rate + 1)
    for trial in spike_times:
        counts[((trial + tzero) * sampling_rate).astype(int)] += 1
    #kernelstd = 4               # kernel standard deviation in milliseconds
    kernelstd_samples = kernelstd / 1000. * sampling_rate
    kernel = gaussian(8 * kernelstd_samples, kernelstd_samples)
    psth = np.convolve(kernel, counts, 'same')
    x = np.arange(len(counts)) / sampling_rate - tzero
    if plot:
        plt.plot(x, psth, linewidth=1, color='r')
        plt.ylabel("summed rates")
        plt.xlabel("s")
    print("{} total spikes in psth".format(count_spikes(spike_times)))
    return x, psth


def get_neuron_group_names(spk_f):
    pgoff = pandas.DataFrame(spk_f['groups_of_clusters'].value)
    neuron_group_names = {k: v for k, v in
                          [x for bee in pgoff[pgoff.columns[:-1]]
                           for x in pgoff[bee]]}  # ugly, wrote once,
                           #   afraid to look at
    return neuron_group_names


def get_unique_stimuli(spk_f):
    stim_entries = [(ename, entry) for ename, entry in spk_f.items()
                    if isinstance(entry, h5py.Group)
                    and 'stimulus' in entry.attrs]
    return set([entry.attrs['stimulus'] for ename, entry in stim_entries])
 

def master_raster(spk_f, kernelstd=5, save=False):
    print("master raster")
    XMAX = 2
    stimploted = False
    stimuli = list(get_unique_stimuli(spk_f))
    stim_entries = [(ename, entry) for ename, entry in spk_f.items()
                    if isinstance(entry, h5py.Group)
                    and 'stimulus' in entry.attrs]
    neuron_group_names = get_neuron_group_names(spk_f)
    # for each unique stimuli, plot raw data
    for istim, stim in enumerate(stimuli):
        plt.figure(figsize=(12, 8), dpi=300)
        stimploted = False
        print(stim)
        associated_trials = [(ename, entry)
                             for ename, entry in stim_entries
                             if 'stimulus' in entry.attrs
                             and stim == entry.attrs['stimulus']]
        associated_trials = sorted(associated_trials, key=repr)
        Ntrials=len(associated_trials)
        spike_times = []
        for Nth_row, (neuron_N, group, shank) in enumerate(spk_f['clusters']):
            print(neuron_N)
            group_name = neuron_group_names[group]
            if group_name == 'Noise':
                continue        
            for itrial, (tname, trial) in enumerate(associated_trials):
                ax3 = plt.subplot(313)
                id_mask = trial['spikes_1']['cluster_manual'] == neuron_N
                pulse = trial['pulse'].value
                sampling_rate = trial['pulse'].attrs['sampling_rate']
                times = (trial['spikes_1']['start'][id_mask]
                         .astype(float) - pulse) / sampling_rate
                spike_times.append(times)
                #print(times)
                #plt.vlines(times, Nth_row + itrial/Ntrials,
                #           Nth_row + (3 + itrial)/Ntrials)
                plt.xlim(0, XMAX)
                if 'stim' in spk_f[tname] and itrial == 0 and not stimploted:
                    ax2 = plt.subplot(312, sharex=ax3)
                    simple_plot_stim(spk_f[tname]['stim'], pulse, XMAX, sampling_rate)
                    ax1 = plt.subplot(311, sharex=ax3)
                    simple_plot_stim(spk_f[tname]['stim'], pulse, XMAX, sampling_rate,
                                     style='spec')
                    stimploted = True
        
        x, psth = plot_psth(spike_times, sampling_rate, kernelstd=kernelstd)
        plt.suptitle('rate window: {} ms'.format(kernelstd))
        #  compute minima
        mins_ind = minima(psth)
        for ax in [ax1, ax2, ax3]:
             [ax.axvline(b) for b in x[mins_ind]]
        plt.tight_layout()
        if not save:
            plt.show()
        else:
            save_name = "{}_dumbsum_{}ms.png".format(stim,
                                                     kernelstd)
            print(save_name)
            plt.savefig(save_name)
            plt.close()


def plot_by_neuron(spk_f, save=False):
    XMAX = 2
    stimuli = get_unique_stimuli(spk_f)
    stim_entries = [(ename, entry) for ename, entry in spk_f.items()
                    if isinstance(entry, h5py.Group)
                    and 'stimulus' in entry.attrs]
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
            x, psth = plot_psth(spike_times, sampling_rate)
        plt.tight_layout()
        if not save:
            plt.show()
        else:
            save_name = "group_{}_neuron_{:03}.png".format(group_name,
                                                           neuron_N)
            print(save_name)
            plt.savefig(save_name)
            plt.close()


def main(spk_f, plot_type='master_raster', save=False):
    if plot_type == 'by_neuron':
        plot_by_neuron(spk_f, save)
    elif plot_type == 'master_raster':
        for kernelstd in [3, 4, 6, 7, 8, 9]:
            master_raster(spk_f, kernelstd=kernelstd, save=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('spike',
                        help='arf file containing the spikes')
    parser.add_argument('--save', help="save to disk instead of showing",
                        action='store_true')
    args = parser.parse_args()
    with h5py.File(args.spike, 'r') as spk_f:
        main(spk_f, save=args.save)



















