
import argparse
import os.path
import h5py
import numpy as np

CHUNKSIZE = 500000  # chunks of arf arrays to place in .dat binaries
                    # size of file: CHUNKSIZE * number of channels


def determine_maximum_value(entries, start_channel, stop_channel, verbose=True):
    print('detecting maximum value to maximize bit depth...')
    grand_mag = 0
    for entry in entries:
        if verbose == True:
            print("entering {}".format(entry))
        datasets = [x for x in entry.values()
                    if type(x) == h5py.Dataset
                    and 'datatype' in x.attrs.keys()
                    and x.attrs['datatype'] < 1000]
        electrodes = sorted(datasets, key=repr)[start_channel:stop_channel]
        for i in range(0, len(electrodes[0]), CHUNKSIZE):
            X = np.column_stack(e[i:i + CHUNKSIZE] for e in electrodes)
            mag = np.max(np.abs(X))
            if verbose:
                print("max val: {}".format(mag))
            if mag > grand_mag:
                grand_mag = mag
                if verbose:
                    print("Largest value so far: {}".format(grand_mag))
    return grand_mag

def arf_entries(arf_file):
    entries = [x for x in arf_file.values() if type(x) == h5py.Group]
    return sorted(entries, key=repr)

def makedat(arf_file, foldername, start_channel, stop_channel,
            data_max, Nentries=-1, verbose=True):
    '''generates .dat files for use in the sorting software.'''
#    arf_file = h5py.File(arf_filename, 'r')
    filebase = os.path.split(os.path.splitext(arf_file.filename)[0])[-1]
    entries = arf_entries(arf_file)
    entries_name = [k for k, x in arf_file.items() if type(x) == h5py.Group]
    entries_name = sorted(entries_name, key=repr)
    if Nentries > 0:
        entries = entries[:Nentries]
        entries_name = entries_name[:Nentries]
    filename_list = []

    for entry_name, entry in zip(entries_name, entries):
        # assuming the first N datasets are the electrodes
        datasets = [x for x in entry.values()
                    if type(x) == h5py.Dataset
                    and 'datatype' in x.attrs.keys()
                    and x.attrs['datatype'] < 1000]
        electrodes = sorted(datasets, key=repr)[start_channel:stop_channel]
        assert(len(electrodes) == stop_channel - start_channel)
        assert(len(set([len(e) for e in electrodes])) == 1)

        for i in range(0, len(electrodes[0]), CHUNKSIZE):
            X = np.column_stack(e[i:i + CHUNKSIZE] for e in electrodes)
            X = np.ravel(np.int16(X / data_max * (2**15 - 1)))
            filename = '{}_a_{}_{:03}.dat'.format(filebase,
                                                 os.path
                                                 .split(entry_name)[-1],
                                                 i / CHUNKSIZE)
            filename = os.path.abspath(os.path.join(foldername, filename))
            print("{} bit depth utilized".format(np.max(np.abs(X))/(2.**15-1)))
            X.tofile(filename)
            filename_list.append(os.path.abspath(filename))
    print('created {} .dat files from {}'.format(len(filename_list),
                                                 arf_file.filename))
    arf_file.flush()
    arf_file.close()
    return filename_list


if __name__ == "__main__":
    description = '''arftodat.py

    converts arf files to a series of .dat files
    '''

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-d", "--directory",
                        help="directory to place .dat files",
                        default=os.path.curdir)
    parser.add_argument("--start-channel",
                        help="First electrode channel, inclusive (0)",
                        default=0, type=int)
    parser.add_argument("--stop-channel",
                        help="last channel, exclusive (32)",
                        default=32, type=int)
    parser.add_argument("arfs", help="arf files",
                        nargs='+')
    parser.add_argument("--num-entries",
                        help="number of entries, all by default",
                        default=-1, type=int)
    parser.add_argument("--quiet", help="turns off verbosity",
                        action="store_true")
    parser.add_argument("--max-val", help="maximum value of the dataset",
                        default=np.nan, type=float)
    args = parser.parse_args()
    
    verbose = not args.quiet

    # determine maximum values
    if np.isnan(args.max_val):
        maxes=[]
        for arf in args.arfs:
            with h5py.File(arf, 'r') as arf_file:
                entries = arf_entries(arf_file)
                maxes.append(determine_maximum_value(entries, args.start_channel,
                                                     args.stop_channel))
        data_max = max(maxes)
    else:
        data_max = args.max_val

    # check folder
    if not os.path.isdir(args.directory):
        mkdir(args.directory)

    # make dats
    for arf in args.arfs:
        with h5py.File(arf, 'r') as arf_file:
            makedat(arf_file, args.directory, args.start_channel,
                    args.stop_channel, data_max, args.num_entries,
                    verbose)
