#!/usr/bin/python

description = '''
goals: display a peristimulus time histogram for data in a spike-sorted
arf file.
'''

import argparse
import h5py


def main(spk_f, arf_f):
    # find unique stimuli
    # for each unique stimuli, plot raw data
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--spike',
                        help='arf file containing the spikes',
                        required=True)
    parser.add_argument('--arf',
                        help='original arf file')
    args = parser.parse_args()
    spk_f = h5py.File(args.spike, 'r')
    arf_f = h5py.File(args.arf, 'r')
    main(spk_f, arf_f)




















