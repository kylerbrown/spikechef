#!/usr/bin/python

import argparse
from datetime import datetime
import os
import os.path
import shutil
import sys
from subprocess import call
from spikedetekt.probes import Probe
from spikedetekt import detektspikes
import h5py
import numpy as np

CHUNKSIZE = 500000  # chunks of arf arrays to place in .dat binaries
                    # size of file: CHUNKSIZE * number of channels


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
    entries_name = [k for k, x in arf_file.items() if type(x) == h5py.Group]
    entries_name = sorted(entries_name, key=repr)
    if Nentries > 0:
        entries = entries[:Nentries]
        entries_name = entries_name[:Nentries]
    filename_list = []
    data_max = determine_maximum_value(entries, probe.num_channels)
    for entry_name, entry in zip(entries_name, entries):
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
                                                 .split(entry_name)[-1],
                                                 i / CHUNKSIZE)
            filename = os.path.join(foldername, filename)
            print("{} bit depth utilized".format(np.max(np.abs(X))/(2.**15-1)))
            X.tofile(filename)
            filename_list.append(os.path.abspath(filename))
    print('created {} .dat files from {}'.format(len(filename_list),
                                                 arf_filename))
    arf_file.flush()
    arf_file.close()
    return filename_list


def arf_samplerate(arf_filename):
    if isinstance(arf_filename, h5py.File):
        arf_file = arf_filename
        open_flag = False
    else:
        arf_file = h5py.File(arf_filename, 'r')
        open_flag = True
    for group in arf_file.values():
        for dataset in group.values():
            if 'datatype' in dataset.attrs \
               and dataset.attrs['datatype'] < 1000 \
               and 'sampling_rate' in dataset.attrs:
                sampling_rate = dataset.attrs['sampling_rate']
                print(sampling_rate)
                if open_flag:
                    arf_file.flush()
                    arf_file.close()
                return sampling_rate


def main(arfname, probename, detektparams, Nentries=-1,
         cluster=True, view=False, batch=False):
    startTime = datetime.now()

        # read in probe file to determine the number of probes
    arf_filename = os.path.abspath(arfname)
    probe_filename = os.path.abspath(probename)
    eparams_filename = os.path.abspath(detektparams)\
        if detektparams is not None else None

    probe = Probe(probename)
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
            os.mkdir(foldername)
        else:
            pass
            #print('aborting')
            #sys.exit()
    else:
        os.mkdir(foldername)

    os.chdir(foldername)
    print('moving to {}'.format(os.path.abspath(os.curdir)))
#    os.path.d
    param_fname = '{}.params'.format(os.path.join(foldername,
                                                  os.path.
                                                  split(foldername)[-1]))

    if not os.path.exists(param_fname):
        # put dat files in directory
        dat_fnames = makedat(arf_filename, foldername, probe, Nentries)
        # ensure unique filenames
        assert len(dat_fnames) == len(set(dat_fnames))

        # create params file

        with open(param_fname, 'w') as f:
            f.write('RAW_DATA_FILES = {}\n'.format([x.encode('ascii')
                                                    for x in dat_fnames]))
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
    detektspikes.main(param_fname)
    #call(['python',
    #      'detektspikes.py',
    #      param_fname])

    # clean up .dat files
    #print("removing .dat files...")
    #[os.remove(x) for x in dat_fnames]

    os.chdir(os.path.join(foldername, '_1'))
    print('moving to {}'.format(os.path.abspath(os.curdir)))
    # finally copy the probe file
    shutil.copy(probe_filename, '.')

    if not (cluster or batch):
        sys.exit()

    #run klustakwik
    basename = os.path.split(foldername)[-1]
    print(basename)
    if batch:
        call(['rsync', ' -av ', '* '
              'beast.uchicago.edu:/home/kjbrown/' + basename])
        print('submitting remote job')
        call(['ssh', 'beast.uchicago.edu',
              '\'echo "klustakwik/MaskedKlustaKwik \
              {} 1 -PenaltyK 1 -PenaltyKLogN 0" | \
              qsub -l nodes=1:ppn=8 \''
              .format(os.path.join(basename, basename))])
        call(['rsync', ' -av ',
              'beast.uchicago.edu:/home/kjbrown/{}/*'
              .format(basename),
              '.'])
        #subprocess.call(['ssh', 'beast.uchicago.edu',
        #                 '\'rm -r {}\''.format(basename)])
    else:
        call(['MaskedKlustaKwik',
              os.path.abspath(basename), '1',
              '-PenaltyK', '2.0',
              '-PenaltyKLogN', '0.0',
              '-MaxPossibleClusters', str(int(probe.num_channels * 3)),
              '-MaxIter', '300',
              '-UseDistributional', '1',
              '-UseMaskedInitialConditions', '1',
              '-MaskStarts', str(int(probe.num_channels * 2))
              ])

    print('Automatic sorting complete! total time: {}'
          .format(datetime.now()-startTime))

    if view:
        call(['klustaviewa', '{}.clu.1'.format(basename)])


if __name__ == '__main__':
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
    parser.add_argument('--cluster', help="runs klustakwik",
                        action='store_true')
    parser.add_argument('--batch', help="runs klustakwik remotely on beast,\
    will not work for you without editing source code (for now)",
                        action='store_true')
    args = parser.parse_args()
    main(args.arf, args.probe, args.detektparams, args.Nentries, args.cluster,
         args.batch)
