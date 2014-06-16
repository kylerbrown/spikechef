import h5py
import argparse
import os
from os.path import splitext
import stat
import numpy as np

if __name__=='__main__':
    p = argparse.ArgumentParser(prog="arf2kwd.py")
    p.add_argument("arf", help="Arf file to convert to kwd")
    p.add_argument("-n", "--name", help="in addition to data of types 3, or 23, include channels\
     containing NAME in their channel name",
                   default=False)
    
    options = p.parse_args()
    print options.name
    arffilename = '.'.join([splitext(options.arf)[0], 'raw.kwd'])
    with h5py.File(arffilename,'w-') as kwd_file:
        kwd_file.create_group('recordings')
        with h5py.File(options.arf,'r+') as arf_file:
            groups = (entry for entry in arf_file.itervalues() if isinstance(entry,h5py.Group))
            nchannels = None
            for idx,group in enumerate(groups):
                channels = [dset for dset in group.itervalues()
                            if dset.attrs.get('datatype') in (3,23)
                            or (options.name and options.name in dset.name.split('/')[-1])]
                if nchannels in (len(channels),None):
                    nchannels = len(channels)
                else:
                    raise ValueError("The number of extracellular channels must be the same in all arf entries")
                if nchannels == 0:
                    raise ValueError("No channels of correct datatyple")

                dset_sizes = [ch.size for ch in channels]
                if all(s == dset_sizes[0] for s in dset_sizes):
                    dset_size = dset_sizes[0]
                else:
                    raise ValueError("The number size of each extracellular dataset within each arf entry must be equal")

                for dset in channels:
                    print(dset.name)
                kwd_group = kwd_file['recordings'].create_group(str(idx))
                dataset=kwd_group.create_dataset('data',shape=(dset_size, nchannels),
                                                 dtype='int16')
                max_array_size = 10**7 #maximum size of array data to read from disk 
                for ch_idx,channel in enumerate(channels):
                    #convert from microvolts to original integer data (but as *signed* integers).
                    for start in xrange(0,dset_size,max_array_size):
                        stop = min(dset_size,start+max_array_size)
                        dataset[start:stop, ch_idx] = np.round(channel[start:stop]/0.195)

                #creating extraneous group and attribute
                kwd_group.create_group('filter')
                kwd_group.attrs['downsample_factor'] = np.string_('N.')

    os.chmod(arffilename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
