#!/usr/bin/python

import os.path
import argparse
import h5py
import numpy as np
import arf
from numpy.lib import recfunctions
from arftoclu import arf_samplerate

description = '''
clutoarf.py

packs the spike sorting results back into an arf file
'''
parser = argparse.ArgumentParser(description=description)
parser.add_argument('--kwik', help='hdf5 file containing the spike \
sorting results, usually a .kwik',
                    required=True)
parser.add_argument('--arf', help='original arf file containing raw data',
                    required=True)
parser.add_argument('--merge', help='merge sorting results with raw data arf',
                    action='store_true')
args = parser.parse_args()


kwik_file = h5py.File(args.kwik, 'r')
arf_file = h5py.File(args.arf, 'r')
spikes_filename = os.path.splitext(os.path
                                   .split(args.arf)[-1])[0] + '_spikes.arf'
spikes_file = arf.open_file(spikes_filename,
                            'w')  # save location


def add_shank_field(array, shanknum):
    return recfunctions.append_fields(array, 'shank',
                                      data=shanknum * np.ones(len(array)),
                                      dtypes=np.uint16, usemask=False)

# populate spike metadata
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

# traverse arf entries, count samples, add kwik data to arf format

entries = [x for x in arf_file.values() if type(x) == h5py.Group]
entries = sorted(entries, key=repr)
keys = [k for k, x in arf_file.items() if type(x) == h5py.Group]
keys = sorted(keys, key=repr)

stop_sample = 0
for k, entry in zip(keys, entries):
    print entry.name
    print entry.attrs['timestamp']
    print k
    spike_entry = arf.create_entry(spikes_file, k,
                                   entry.attrs['timestamp'])
    if 'pulse' in entry.attrs:
        spike_entry.attrs['pulse'] = entry.attrs['pulse']
    if 'stimulus' in entry.attrs:
        spike_entry.attrs['stimulus'] = entry.attrs['stimulus']
#    spikes_file.create_group(os.path.split(entry.name)[-1])
    dataset_len = next((len(x) for x in entry.values()
                        if type(x) == h5py.Dataset
                        and 'datatype' in x.attrs.keys()
                        and x.attrs['datatype'] < 1000), 0)
    start_sample = stop_sample  # update starting time for next entry
    stop_sample = start_sample + dataset_len
    for shanknum, shank_group in enumerate(kwik_file['shanks'].values()):
        allspikes = shank_group['spikes']
        allwaves = shank_group['waveforms']['waveform_filtered']
        time_mask = np.logical_and(allspikes['time'] >= start_sample,
                                   allspikes['time'] < stop_sample)
        spikes = allspikes[time_mask]
        waves = allspikes[time_mask]
        # change 'time' field to 'start' for arf compatibility
        spikes.dtype.names = tuple([x if x != 'time' else 'start'
                                    for x in spikes.dtype.names])
        spikes['start'] = spikes['start'] - start_sample
        spikes = add_shank_field(spikes, shanknum + 1)
        waves = add_shank_field(waves, shanknum + 1)

        if 'spikes' not in entry:
            arf.create_dataset(spike_entry, 'spikes', spikes,
                               units='samples', datatype=1001,
                               sampling_rate=arf_samplerate(args.arf))
            spike_entry.create_dataset('waves', data=waves)
        else:
            entry['spikes'] = np.append(entry['spikes'], spikes)
            entry['waves'] = np.append(entry['waves'], waves)


print('Done!')
