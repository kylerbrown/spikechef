#!/usr/bin/python

import argparse
from datetime import datetime
import os, os.path, subprocess, shutil, sys
from spikedetekt.probes import Probe
import h5py
import numpy as np

CHUNKSIZE = 200000


def determine_maximum_value(entries, num_channels):
    print('detecting maximum value to maximize bit depth...')
    grand_mag = 0
    for entry in entries:
        datasets = [x for x in entry.values()
                    if type(x) == h5py.Dataset
                    and 'datatype' in x.attrs.keys()
                    and x.attrs['datatype'] < 1000]
        electrodes = sorted(datasets, key=repr)[:num_channels]
        for i in range(0, len(electrodes[0]), CHUNKSIZE):
            X = np.column_stack(e[i:i + CHUNKSIZE] for e in electrodes)
            mag = np.max(np.abs(X))
            if mag > grand_mag:
                grand_mag = mag
                print(grand_mag)
    return grand_mag


def makedat(arf_filename, foldername, probe, Nentries=-1, verbose=False):
    '''generates .dat files for use in the sorting software.'''
    arf_file = h5py.File(arf_filename, 'r')
    filebase = os.path.split(os.path.splitext(arf_filename)[0])[-1]
    entries = [x for x in arf_file.values() if type(x) == h5py.Group]
    entries = sorted(entries, key=repr)
    if Nentries > 0:
        entries = entries[:Nentries]
    filename_list = []
    data_max = determine_maximum_value(entries, probe.num_channels)
    for entry in entries:
        # assuming the first N datasets are the electrodes
        datasets = [x for x in entry.values()
                    if type(x) == h5py.Dataset
                    and 'datatype' in x.attrs.keys()
                    and x.attrs['datatype'] < 1000]
        electrodes = sorted(datasets, key=repr)[:probe.num_channels]
        if verbose:
            print(len(electrodes))
            print([len(e) for e in electrodes])

        for i in range(0, len(electrodes[0]), CHUNKSIZE):
            X = np.column_stack(e[i:i + CHUNKSIZE] for e in electrodes)
            X = np.ravel(np.int16(X / data_max * (2**15 - 1)))
            filename = '{}__{}_{:03}.dat'.format(filebase,
                                                 os.path
                                                 .split(entry.name)[-1],
                                                 i / CHUNKSIZE)
            filename = os.path.join(foldername, filename)
            print("{} bit depth utilized".format(np.max(np.abs(X))/(2.**15-1)))
            X.tofile(filename)
            filename_list.append(os.path.abspath(filename))
    print('created {} .dat files from {}'.format(len(filename_list),
                                                 arf_filename))
    return filename_list


def arf_samplerate(arf_filename):
    arf_file = h5py.File(arf_filename, 'r')
    for group in arf_file.values():
        for dataset in group.values():
            if 'datatype' in dataset.attrs \
               and dataset.attrs['datatype'] < 1000 \
               and 'sampling_rate' in dataset.attrs:
                return dataset.attrs['sampling_rate']


if __name__ == '__main__':
    startTime = datetime.now()

    description = '''
    arftodat.py

    converts arf files into .dat files for use in the spikedetekt
    sorting algorithm.
    Hopefully a temporary fix, spikedetekt should read arf files one day.

    THEN it runs spikedetekt and klustakwik
    '''

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--arf', help='Arf file for sorting',
                        required=True)
    parser.add_argument('-p', '--probe',
                        help='Probe file specifying the geometry of the probe',
                        required=True)
    parser.add_argument('--detektparams',
                        help='extra spikedetect parameters file',
                        default=None)
    parser.add_argument('--view',
                        help='Opens data in klustaviewa after sorting',
                        action='store_true')
    parser.add_argument('-N', '--Nentries',
                        help='process only the first Nentries',
                        type=int, default=-1)
    args = parser.parse_args()
    '''
    from collections import namedtuple
    tempargs = namedtuple('Args', 'arf probe eparams viewa')
    args = tempargs('bk196-2014_01_03-hvc-25s-0-0.arf',
    'A1x32-Poly3-25s.probe',
                    'extra_spikedetekt_params', True)
    '''
    # read in probe file to determine the number of probes
    arf_filename = os.path.abspath(args.arf)
    probe_filename = os.path.abspath(args.probe)
    eparams_filename = os.path.abspath(args.
                                       detektparams) if args.detektparams is not None else None
    probe = Probe(args.probe)
    print(probe_filename)

    #make a directory
    foldername, ext = os.path.splitext(arf_filename)
    print("folder name is {}".format(foldername))
    if ext != '.arf':
        raise Exception('file must have .arf extension!')
    if os.path.isdir(foldername):
        overwrite = raw_input('Directory {} exists, overwrite? y/n: '
                              .format(foldername))
        if overwrite == 'y':
            shutil.rmtree(foldername)
        else:
            print('aborting')
            sys.exit()
    os.mkdir(foldername)
    os.chdir(foldername)
    print('moving to {}'.format(os.path.abspath(os.curdir)))
#    os.path.d
    # put dat files in directory
    dat_fnames = makedat(arf_filename, foldername, probe, args.Nentries)

    # create params file
    param_fname = '{}.params'.format(os.path.join(foldername,
                                                  os.path.
                                                  split(foldername)[-1]))
    with open(param_fname, 'w') as f:
        f.write('RAW_DATA_FILES = {}\n'.format([x.encode('ascii') for x in dat_fnames]))
        f.write('SAMPLERATE = {}\n'.format(arf_samplerate(arf_filename)))
        f.write('NCHANNELS = {}\n'.format(probe.num_channels))
        f.write('PROBE_FILE = \'{}\'\n'.format(probe_filename))
        #f.write('OUTPUT_DIR = \'{}\'\n'.format(foldername))
                
        if eparams_filename is not None:
            with open(eparams_filename) as epar_f:
                f.write(epar_f.read())

    #remove old spike detect results
    #if os.path.isdir('_1'):
    #    shutil.rmtree('_1')

    # run spikedetect
    subprocess.call(['python',
                     '/home/kjbrown/spikechef/spikedetekt/scripts/detektspikes.py',
                     param_fname])
    #subprocess.call(['python', '/home/kjbrown/spikechef/spikedetekt/scripts/detektspikes.py', param_fname])
    #os.system('python ~/spikechef/scripts/detektspikes.py {}'.format param_fname)

    #run klustakwik
    os.chdir(os.path.join(foldername, '_1'))
    print('moving to {}'.format(os.path.abspath(os.curdir)))

    basename = os.path.split(foldername)[-1]
    subprocess.call(['MaskedKlustaKwik',
                     os.path.abspath(basename), '1',
                     '-PenaltyK', '1',
                     '-PenaltyKLogN', '0'])

    print('Automatic sorting complete! total time: {}'
          .format(datetime.now()-startTime))

    # finally copy the probe file and start klustaviewa
    shutil.copy(probe_filename, '.')

    if args.view:
        subprocess.call(['klustaviewa', '{}.clu.1'.format(basename)])

