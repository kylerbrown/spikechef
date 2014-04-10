#!/usr/bin/python

from __future__ import division
import os.path
import argparse
import h5py
import numpy as np
from scipy.signal import butter, filtfilt
import arf
from numpy.lib import recfunctions
from arftoclu import arf_samplerate
import stimalign

__version__ = '0.2.0'

description = '''
clutoarf.py

packs the spike sorting results back into an arf file
'''


def add_shank_field(array, shanknum):
    return recfunctions.append_fields(array, 'shank',
                                      data=shanknum * np.ones(len(array)),
                                      dtypes=np.uint16, usemask=False)


# populate spike metadata
def spike_metadata(kwik_file, spikes_file):
    for shanknum, shank in enumerate(kwik_file['shanks'].values()):
        clusters = add_shank_field(shank['clusters'].value, shanknum+1)
        groups_of_clusters = add_shank_field(shank['groups_of_clusters'],
                                             shanknum+1)
        if 'clusters' not in spikes_file:
            spikes_file.create_dataset('clusters', data=clusters)
            spikes_file.create_dataset('groups_of_clusters',
                                       data=groups_of_clusters)
        else:
            spikes_file['clusters'] = np.append(spikes_file['clusters'], clusters)
            spikes_file['groups_of_clusters'] = np.append(spikes_file['groups_of_clusters'],
                                                          groups_of_clusters)
    return None


def jstim_log_sequence(stimlog):
    return [line.split()[-3] for line in open(stimlog, 'r')
            if ' [jstim] next stim: ' in line]


def find_and_write_pulse_time(arf_file, arf_entry_name, pulsechan,
                              spike_entry, verbose=True):
            pulsetime = stimalign.detect_pulse(arf_file[arf_entry_name][pulsechan])
            pulse_sampling_rate = arf_file[arf_entry_name][pulsechan].attrs['sampling_rate']
            arf.create_dataset(spike_entry, 'pulse', np.array([pulsetime]),
                               units='samples', datatype=1000,
                               sampling_rate=pulse_sampling_rate)
            if verbose:
                print("pulse: {}".format(pulsetime))


def dataset_length(entry):
    return next((len(x) for x in entry.values()
                 if type(x) == h5py.Dataset
                 and 'datatype' in x.attrs.keys()
                 and x.attrs['datatype'] < 1000), 0)


def add_spikes(spike_entry, kwik_file, start_sample, stop_sample):
    """adds all spikes between the start and stop samples from kwik file
    into spike_entry"""
    for shanknum, shank_group in enumerate(kwik_file['shanks'].values()):
        allspikes = shank_group['spikes']
        allwaves = shank_group['waveforms']['waveform_filtered']
        time_mask = np.logical_and(allspikes['time'] >= start_sample,
                                   allspikes['time'] < stop_sample)
        spikes = allspikes[time_mask]
        waves = allwaves[time_mask]
        # change 'time' field to 'start' for arf compatibility
        spikes.dtype.names = tuple([x if x != 'time' else 'start'
                                    for x in spikes.dtype.names])
        spikes['start'] = spikes['start'] - start_sample
        spike_dset_name = 'spikes_{}'.format(shanknum + 1)
        waves_dset_name = 'waves_{}'.format(shanknum + 1)

        if spike_dset_name not in spike_entry:
            arf.create_dataset(spike_entry, spike_dset_name,
                               spikes,
                               units=('ID', 'ID', 'none', 'none', 'samples'),
                               vdatatype=1001,
                               sampling_rate=arf_samplerate(args.arf))
            arf.create_dataset(spike_entry, waves_dset_name, waves,
                               units='samples', datatype=11001,
                               sampling_rate=arf_samplerate(args.arf))
        else:
            spike_entry[spike_dset_name].value = np.append(spike_entry[spike_dset_name], spikes)
            spike_entry[waves_dset_name].value = np.append(spike_entry[waves_dset_name], waves)


def add_lfp(spike_entry, raw_entry, Nlfp, cutoff=300, order=3,
            lfp_sampling_rate=1000):
    """adds first N lfp channels to the spike_entry"""
    data_channels = [x for x in raw_entry if type(x) == h5py.Dataset
                     and 'datatype' in x.attrs
                     and x.attrs['datatype'] < 1000]
    data_channels = sorted(data_channels, key=repr)[:Nlfp]
    for chan in data_channels:
        # low pass filter
        b, a = butter(order, cutoff * chan.attrs['sampling_rate'] / 2.)
        lfp = filtfilt(b, a, chan)
        # resample
        old_x = np.arange(len(chan)) / chan.attrs['sampling_rate']
        resample_ratio = chan.attrs['sampling_rate'] / lfp_sampling_rate
        new_x = np.arange(len(chan) / resample_ratio) / lfp_sampling_rate
        resamp_lfp = np.interp(new_x, old_x, lfp)
        arf.create_dataset(spike_entry, chan.name, resamp_lfp,
                           units='samples', datatype=2,
                           sampling_rate=lfp_sampling_rate)


def get_geometry(probe, verbose=True):
    variables = {}
    execfile(probe, variables)  # contains global variable geometry
    geometry = variables['geometry']
    geometry_array = np.array([v for v in geometry.values()])
    if verbose:
        print('geometry:')
        print(geometry_array)
    return geometry_array


def main(kwik_file, arf_file, spikes_file,
         stimlog=None, nlfp=0, pulsechan='', stimchannel='',
         probe=None, autodetect_pulse_channel=False, verbose=True):

    spike_metadata(kwik_file, spikes_file)

    if autodetect_pulse_channel:
        #determine pulse channel
        pulsechan = stimalign.autopulse_dataset_name(arf_file)

    # traverse arf entries, count samples, add kwik data to arf format
    entries = [x for x in arf_file.values() if type(x) == h5py.Group]
    entries = sorted(entries, key=repr)
    keys = [k for k, x in arf_file.items() if type(x) == h5py.Group]
    keys = sorted(keys, key=repr)

    if stimlog:
        stim_sequence = jstim_log_sequence(stimlog)
        if len(stim_sequence) != len(entries):
            print("Warning! jstim log has {} entries,  \
            arf files has {} entries"
                  .format(len(stim_sequence), len(entries)))
    else:
        stim_sequence = [None for e in entries]
    if probe:
        spikes_file['geometry'] = get_geometry(probe)
    # adding spike times and waveforms, and such, creating spike entries
    # in spikes_file
    stop_sample = 0
    for k, entry, stim_name in zip(keys, entries, stim_sequence):
        print(k)
        print(entry.name)
        print(entry.attrs['timestamp'])
        print(stim_name)

        #create entry in spike arf file
        spike_entry = arf.create_entry(spikes_file, k,
                                       entry.attrs['timestamp'])
        #write stimulus name as an attribute
        spike_entry.attrs['stimulus'] = stim_name

        if pulsechan:
            find_and_write_pulse_time(arf_file, k, pulsechan,
                                      spike_entry, verbose)
        if stimchannel:
            spike_entry.copy(arf_file[k][stimchannel], "stim")
        if nlfp:
            add_lfp(spike_entry, arf_file[k], nlfp)

        start_sample = stop_sample  # update starting time for next entry
        stop_sample = start_sample + dataset_length(entry)
        add_spikes(spike_entry, kwik_file, start_sample, stop_sample)

    print('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--kwik', help='hdf5 file containing the spike \
    sorting results, usually a .kwik',
                        required=True)
    parser.add_argument('--arf', help='original arf file containing raw data',
                        required=True)
    parser.add_argument('--stim', help='a jstim log to identify the stimulus')
    parser.add_argument('--lfp',
                        help='create lfp datasets, \
                        enter number of channels eg 32',
                        default=0, type=int)
    parser.add_argument('--pulse', help='name of pulse channel, \
    detect stimulus onset from a pulse channel',
                        type=str, default='')
    parser.add_argument('-o', '--out', help='name of output arf file')
    parser.add_argument('--stimchannel',
                        help='name of stimulus channel, will be copied')
    parser.add_argument('--probe',
                        help='name of .probe file, for storing geometry')
    args = parser.parse_args()

    used_files = [args.kwik, args.arf]
    if args.probe:
        used_files.append(args.probe)
    for f in used_files:
        if not os.path.isfile(args.probe):
            raise IOError('no such file: {}'.format(f))
    if not args.out:
        spikes_filename = os.path.splitext(os.path
                                           .split(args.arf)[-1])[0] \
            + '_spikes.arf'

    with h5py.File(args.kwik, 'r') as kwik_file,\
        h5py.File(args.arf, 'r') as arf_file,\
        arf.open_file(spikes_filename, 'w') as spikes_file:

        main(kwik_file, arf_file, spikes_file,
             args.stim, args.lfp, args.pulse, args.stimchannel, args.probe)
