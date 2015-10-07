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
from spikechef.utils import arf_samplerate


def resample_wavs(wavenames, sr):
    wav_files = [ewave.open(wav) for wav in wavenames]
    resamp_wavs = [resample(f.read(),
                   sr * f.nframes / float(f.sampling_rate))
                   for f in wav_files]
    return resamp_wavs


def classify_stim(stimuli, stim_copies, sr):
    '''Classifies stimuli if no stimulus log exists'''
    max_corr = lambda x, y: np.max(fftconvolve(x, y[::-1]))
    stim_idx = [np.argmax([max_corr(stim, copy) for stim in stimuli])
                for copy in stim_copies]
    return stim_idx


def dset_generator(arf_file, dataset_name):
    for entry in arf_file.values():
        if not isinstance(entry, h5py.Group):
            continue
        elif dataset_name in entry:
            yield entry[dataset_name]
        else:
            print("{} does not exist in {}".format(dataset_name, entry.name))
            pass


def detect_pulse(pulse_dset, thr=.5):
    crossings = (pulse_dset[:-1] < thr) & (pulse_dset[1:] > thr)
    thresh_crossings = np.where(crossings)[0]
    if len(thresh_crossings) > 0:
        return thresh_crossings + 1
    else:
        return thresh_crossings


def create_label_dataset(pulse_dset, stim_labels, dset_name):
    """returns a record array with N rows where N is
the number of detected pulses. Each row has a column with the start time
in samples and an empty string row which will be populated when the stimulus
is identified"""
    starts = detect_pulse(pulse_dset)
    stim_list = [(s, '') for s in starts]
    stim_dtype = [('start', int),
                  ('name', 'a%d' %
                   (max(len(lb) for lb in stim_labels)))]
    stim_array = np.array(stim_list, dtype=stim_dtype)
    sr = pulse_dset.attrs['sampling_rate']
    label_dset = arf.create_dataset(
        pulse_dset.parent,
        dset_name,
        data=stim_array,
        datatype=2001,
        units=(np.string_('samples'), np.string_('')),
        sampling_rate=sr)
    return label_dset


def remove_old_label_dataset(dset_name, entry):
    if dset_name in entry:
        print(
            "{dset} already exists in {entry}, deleting".format(
                dset=dset_name,
                entry=entry))
        del entry[dset_name]


def add_stim_name_to_label_dataset(copy_dset, resampled_wavs, label_dset,
                                   stim_labels):
    assert label_dset.parent == copy_dset.parent
    max_stim_len = max(len(w) for w in resampled_wavs)
    stim_copies = [copy_dset[s:s + max_stim_len]
                   for s in label_dset["start"]]
    stim_idx = classify_stim(resampled_wavs, stim_copies,
                             copy_dset.attrs["sampling_rate"])
    name = np.array(stim_labels)[stim_idx]
    label_dset['name'] = name


def save_stimuli(stimulus_group, arf_file, stims_data, stim_labels, wavenames):
    """ saves resampled stimuli in to the arf file"""
    if stimulus_group in arf_file:
        del arf_file[stimulus_group]
    arf.create_entry(arf_file, stimulus_group, time.time())
    for sdata, sname, wname in zip(stims_data, stim_labels, wavenames):
        arf.create_dataset(
            arf_file[stimulus_group],
            sname,
            data=sdata,
            datatype=1,
            sampling_rate=arf_samplerate(arf_file),
            original_file=os.path.abspath(
                wname))


def label_stim(arfname, wavenames, stim_labels, pulse_key,
               copy_key, dset_name='stimulus_time', stimulus_group='stimuli'):
    resamp_wavs = resample_wavs(wavenames, arf_samplerate(arfname))
    with h5py.File(arfname, 'r+') as arf_file:
        pulse_dsets = dset_generator(arf_file, pulse_key)
        copy_dsets = dset_generator(arf_file, copy_key)
        for pulse_dset, copy_dset in zip(pulse_dsets, copy_dsets):
            assert pulse_dset.parent == copy_dset.parent
            remove_old_label_dataset(dset_name, pulse_dset.parent)
            # detect pulses
            label_dataset = create_label_dataset(pulse_dset, stim_labels,
                                                 dset_name)
            # classifying stimuli
            add_stim_name_to_label_dataset(copy_dset, resamp_wavs,
                                           label_dataset, stim_labels)
            print(list(label_dataset[:]))

        save_stimuli(stimulus_group, arf_file, resamp_wavs,
                     stim_labels, wavenames)


def main():
    p = argparse.ArgumentParser(
        prog='label stimulus',
        description="""Creates label datasets containing stimulus
        times and labels and saves stimulus wave files in arf""",
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
