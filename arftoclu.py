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
from arftodat import makedat



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


def prep_analysis_folder(foldername):
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


def create_params_file(param_fname, dat_fnames, probe, probe_filename,
                       eparams_filename, sampling_rate=30000):
    with open(param_fname, 'w') as f:
            f.write('RAW_DATA_FILES = {}\n'.format([x.encode('ascii')
                                                    for x in dat_fnames]))
            f.write('SAMPLERATE = {}\n'.format(sampling_rate))
            f.write('NCHANNELS = {}\n'.format(probe.num_channels))
            f.write('PROBE_FILE = \'{}\'\n'.format(probe_filename))
            #f.write('OUTPUT_DIR = \'{}\'\n'.format(foldername))
            if eparams_filename is not None:
                with open(eparams_filename) as epar_f:
                    f.write(epar_f.read())


def run_klustakwik(basename, probe, shank=1, maxiter=400):
        call(['MaskedKlustaKwik',
              os.path.abspath(basename), str(shank),
              '-PenaltyK', '2.0',
              '-PenaltyKLogN', '0.0',
              '-MaxPossibleClusters', str(int(probe.num_channels * 4)),
              '-MaxIter', str(maxiter),
              '-UseDistributional', '1',
              '-UseMaskedInitialConditions', '1',
              '-MaskStarts', str(int(probe.num_channels * 3))])


def main(arfnames, foldername, probename, detektparams, Nentries=-1,
         cluster=True, view=False, batch=False):
    startTime = datetime.now()

    # read in probe file to determine the number of probes
    arf_filenames = [os.path.abspath(x) for x in arfnames]
    sampling_rate = arf_samplerate(arf_filenames[0])
    probe_filename = os.path.abspath(probename)
    eparams_filename = os.path.abspath(detektparams)\
        if detektparams is not None else None

    probe = Probe(probename)
    print(probe_filename)
    
    prep_analysis_folder(foldername)  # changes directory to analysis directory

    param_fname = '{}.params'.format(os.path.join(foldername,
                                                  os.path.
                                                  split(foldername)[-1]))

    # put dat files in directory
    dat_fnames = []
    for arf_filename in arf_filenames:
        dat_fnames.extend(makedat(arf_filename, foldername, probe, Nentries))
    # ensure unique filenames
    assert len(dat_fnames) == len(set(dat_fnames))

    # create params file
    create_params_file(param_fname, dat_fnames, probe, probe_filename,
                       eparams_filename, sampling_rate)

    # run spikedetect
    detektspikes.main(param_fname)

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
