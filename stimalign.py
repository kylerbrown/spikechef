#!/usr/bin/python

import argparse, sys
import numpy as np
import h5py
import matplotlib.pyplot as plt



def detect_pulse(x):
    '''returns the index of the pulse, assumes single pulse'''
    dx = np.diff(x)
    return np.argmax(dx) + 1     # +1 is to compensate for diff's method of differentiation


def set_pulse_attribute(arf_file, pulse_dataset_name, verbose=False, visual=False):
    '''sets the pulse location in samples as an atribute of the entry'''
    if visual:
        plt.figure()
    entries = sorted([e for e in arf_file.values() if isinstance(e, h5py.Group)], key=repr)
    for entry in entries:
        if pulse_dataset_name in entry:
            pulse_time = detect_pulse(entry[pulse_dataset_name])
            entry.attrs['pulse'] = pulse_time
            entry[pulse_dataset_name].attrs['pulse'] = pulse_time # second location to be safe.
            if verbose:
                print('''Pulse time {} added to entry {},
                using pulse channel {}.'''.format(pulse_time,
                                                  entry.name,
                                                  pulse_dataset_name))
            if visual:
                plt.plot(np.arange(pulse_time-50, pulse_time+50),
                         entry[pulse_dataset_name][pulse_time-50:pulse_time+50])
                plt.vlines(pulse_time, 0, 2, colors='r')
    if visual:
        plt.show()


def last_dataset_name(arf_file):
    '''returns the name of the last dataset in standard arf entries'''
    try:
        candidate_entry = next( (entry for entry in arf_file.itervalues()
                                 if isinstance(entry, h5py.Group) and
                                 next((dset for dset in entry.values() if 'datatype' in dset.attrs
                                       and dset.attrs['datatype']<1000), False))
                                )
    except StopIteration:
        sys.exit('arf file does not have sampled data')
    dsets = sorted([dset for dset in candidate_entry.values() if 'datatype' in dset.attrs
                    and dset.attrs['datatype']<1000], key=repr)
    return dsets[-1].name.split('/')[-1]


def main(arf_name, pulse_name=-1, verbose=False, visual=False):
    arf_file = h5py.File(arf_name, 'a')
    if pulse_name == -1:
        pulse_dataset_name = last_dataset_name(arf_file)
        if verbose:
            print('choosing last dataset {} as pulse data'.format(pulse_dataset_name))
    else:
        pulse_dataset_name = pulse_name
    set_pulse_attribute(arf_file, pulse_dataset_name, verbose, visual)
    if verbose:
        print('aligment complete for {}'.format(arf_name))


if __name__ == '__main__':
    description = '''
    stimalign.py

    used the impulse channel to provide a reference point for aligning the stimulus trials.

    This is required for experiments where jstim is running on a separate JACK server.
    E.g. Using an Intan board for recording and a audio interface for stimulus presentation.
    '''

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--arf', help='raw data arf file',
                        required=True)
    parser.add_argument('-p', '--pulse-name',
                        help='jrecord channel containing the timing impulse, \
                        defaults to last chan, sorted alphabetically',
                        default=-1)
    parser.add_argument('-v', '--verbose', help='prints things',
                        action='store_true')
    parser.add_argument('--visual', help='plots all found impulse locations\
    for visual verification', action='store_true')
    args = parser.parse_args()
    main(args.arf, args.pulse_name, args.verbose, args.visual)

















