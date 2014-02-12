#!/usr/bin/python

from __future__ import division
import argparse
import h5py
import pandas
import matplotlib.pyplot as plt
import numpy as np
description = '''
goals: display a peristimulus time histogram for data in a spike-sorted
arf file.
'''


def main(spk_f, arf_f=None, save=False):
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
                           for x in pgoff[bee]]}
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
            for itrial, (tname, trial) in enumerate(associated_trials):
                plt.subplot(Nstim * 2, 1, istim * 2 + 2)
                plt.title("neuron: {}, group: {}, stim:{}"
                          .format(neuron_N, group_name, stim))

                id_mask = trial['spikes']['cluster_manual'] == neuron_N
                pulse = trial.attrs['pulse']
                times = (trial['spikes']['start'][id_mask].astype(float) - pulse) / 30000 # TODO add sampling rate to spike arf files
                #print(times)
                plt.vlines(times, itrial, itrial+1)
                plt.xlim(0, 2)
                if arf_f and itrial % 5 == 0:
                    plt.subplot(Nstim * 2, 1, istim * 2 + 1)
                    stimdata = arf_f[tname]['pcm_033'][pulse:pulse + 2 * 30000]
                    stimx = np.arange(len(stimdata)) / 30000
                    plt.plot(stimx, stimdata)
                    plt.title("neuron: {}, group: {}, stim:{}"
                              .format(neuron_N, group_name, stim))
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



















