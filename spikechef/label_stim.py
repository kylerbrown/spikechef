#!/usr/bin/python
#  -*- mode: Python -*-
import numpy as np
import h5py
import arf
import ewave
from scipy.signal import resample
import time
import os
import argparse
from scipy.signal import fftconvolve


def classify_stim(stimuli, stim_copies, sr=30000):
    '''Classifies stimuli if no stimulus log exists'''
    print("length =\t{}".format([len(x) for x in stim_copies]))
    max_corr = lambda x, y: np.max(fftconvolve(x, y[::-1]))
    stim_idx = [np.argmax([max_corr(stim, copy) for stim in stimuli])
                for copy in stim_copies]

    return stim_idx


def dset_generator(arf_file, dataset_name):
    for entry in arf_file.values():
        # print(entry)
        # print(dataset_name)
        if not isinstance(entry, h5py.Group):
            continue
        elif dataset_name in entry:
            yield entry[dataset_name]
        else:
            print("{} does not exist in {}".format(dataset_name, entry.name))
            pass
            #raise IOError('No dataset named {}'.format(dataset_name))


def detect_pulse(pulse_dset, thr=.5):
    crossings = (pulse_dset[:-1] < thr) & (pulse_dset[1:] > thr)
    thresh_crossings = np.where(crossings)[0]
    if len(thresh_crossings) > 0:
        return thresh_crossings + 1
    else:
        return thresh_crossings


def label_stim(arfname, wavenames, stim_labels, pulse_key,
               copy_key, dset_name='stimulus_time', stimulus_group='stimuli'):
    wav_files = [ewave.open(wav) for wav in wavenames]

    with h5py.File(arfname, 'r+') as arf_file:
        # obtain stimulus times
        # finds when pulse channel crosses threshold, then finds max around
        # that time
        pulse_dsets = dset_generator(arf_file, pulse_key)
        copy_dsets = dset_generator(arf_file, copy_key)
        for pulse_dset, copy_dset in zip(pulse_dsets, copy_dsets):
            print((pulse_dset.name, copy_dset.name))
            starts = detect_pulse(pulse_dset)

            # creating label dataset
            stim_list = [(s, '') for s in starts]
            stim_dtype = [('start', int),
                          ('name', 'a%d' %
                           (max(len(lb) for lb in stim_labels)))]
            stim_array = np.array(stim_list, dtype=stim_dtype)
            sr = pulse_dset.attrs['sampling_rate']
            if dset_name in pulse_dset.parent:
                print(
                    "{dset} already exists in {entry}, deleting".format(
                        dset=dset_name,
                        entry=pulse_dset.parent))
                del pulse_dset.parent[dset_name]
            label_dset = arf.create_dataset(
                pulse_dset.parent,
                dset_name,
                data=stim_array,
                datatype=2001,
                units=(
                    np.string_('samples'),
                    np.string_('')),
                sampling_rate=sr)

            # classifying stimuli
            copy_sr = copy_dset.attrs['sampling_rate']
            resampled_wavs = [
                resample(
                    f.read(),
                    copy_sr *
                    f.nframes /
                    float(
                        f.sampling_rate)) for f in wav_files]
            max_stim_len = max(len(w) for w in resampled_wavs)
            stim_copies = [
                copy_dset[
                    s:min(
                        s + max_stim_len,
                        copy_dset.size)] for s in starts]
            stim_idx = classify_stim(resampled_wavs, stim_copies)
            name = np.array(stim_labels)[stim_idx]
            label_dset['name'] = name
            print(name)

        # saving stimuli
        if stimulus_group not in arf_file:
            arf.create_entry(arf_file, stimulus_group, time.time())
        for i, f in enumerate(wav_files):
            if stim_labels[i] not in arf_file[stimulus_group]:
                arf.create_dataset(
                    arf_file[stimulus_group],
                    stim_labels[i],
                    data=f.read(),
                    datatype=1,
                    sampling_rate=f.sampling_rate,
                    original_file=os.path.abspath(
                        wavenames[i]))


def main():
    p = argparse.ArgumentParser(
        prog='label stimulus',
        description="""Creates label datasets containing stimulus times and labels and saves stimulus wave files in arf""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("arf", help='Name of arf file to label')
    p.add_argument(
        "-w",
        "--wavenames",
        help="""Stimulus wave files""",
        nargs="+")
    p.add_argument(
        "-l",
        "--labels",
        help="""Labels for each stimulus""",
        nargs="+",
        required=True)
    p.add_argument(
        "-p",
        "--pulse_channel",
        help="""Name of pulse channel""",
        required=True)
    p.add_argument(
        "-c",
        "--copy_channel",
        help="""Name of stimulus copy channel""",
        required=True)
    p.add_argument(
        "-d",
        "--dataset_name",
        help="""Name of label datasets to be created""",
        default="stimulus_time")
    p.add_argument(
        "-s",
        "--stimulus_group",
        help="""Name of the group in the arf file containing the stimuli""",
        default="stimuli")

    options = p.parse_args()
    print(options.stimulus_group)
    label_stim(options.arf, options.wavenames,
               options.labels, options.pulse_channel,
               options.copy_channel, options.dataset_name,
               options.stimulus_group)
if __name__ == '__main__':
    main()
