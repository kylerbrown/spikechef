import shutil
import h5py
import os
from spikedetekt.probes import Probe
from spikedetekt import detektspikes
import argparse

def list_datfiles(directory):
    return (os.path.abspath(f) for f in os.listdir(directory) if f[-4:] == ".dat")

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


def create_params_file(foldername, param_fname, probe_filename,
                       eparams_filename, sampling_rate=30000):
    print(foldername)
    dat_fnames = list_datfiles(foldername)
    probe = Probe(probe_filename)
    with open(os.path.join(foldername, param_fname), 'w') as f:
            f.write('RAW_DATA_FILES = {}\n'.format([x.encode('ascii')
                                                    for x in dat_fnames]))
            f.write('SAMPLERATE = {}\n'.format(sampling_rate))
            f.write('NCHANNELS = {}\n'.format(probe.num_channels))
            f.write('PROBE_FILE = \'{}\'\n'.format(probe_filename))
            #f.write('OUTPUT_DIR = \'{}\'\n'.format(foldername))
            if eparams_filename is not None:
                with open(eparams_filename) as epar_f:
                    f.write(epar_f.read())


def copy_probe_to_subs(directory, probename):
    '''copies probes file to subfolders starting with "_*"
    These folders are created by spikedetect.
    '''
    subs = (os.path.abspath(f) for f in os.listdir(directory) if f[0] == "_"
            and os.path.isdir(f))
    [shutil.copy(probename, f) for f in subs]


def main(foldername, probename, eparams_filename, sampling_rate=30000):
    probe_filename = os.path.abspath(probename)
    param_fname = "{}.params".format(os.path.split(os.path.abspath(foldername))[-1])
    create_params_file(foldername, param_fname, probe_filename,
                       eparams_filename, sampling_rate)
    detektspikes.main(param_fname)
    copy_probe_to_subs(foldername, probename)


if __name__ == "__main__":
    description = '''
    detectspikes.py
    
    given a folder of .dat files, uses spikedetekt to find the spikes
    based on probe geometry.
    '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--directory', help='directory with .dat file,\
    defaults to \'.\'',
                        default='.')
    parser.add_argument('-p', '--probe',
                        help='Probe file specifying the geometry of the probe',
                        required=True)
    parser.add_argument('--params',
                        help='extra spikedetect parameters file',
                        default=None)
    parser.add_argument('--sampling-rate', help='sampling rate, default is 30000',
                        default=30000, type=int)
    args = parser.parse_args()
    main(args.directory, args.probe, args.params, args.sampling_rate)
