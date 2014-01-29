description = '''
mergespon.py

adds spon entries to an arf file, entry names are modified as such:
jrecord_0001 -> spon_0001 and added to arf file
'''

import argparse
import h5py


def main(arf_spon, arf_out, spon_entry_name='jrecord',
         out_entry_name='spon', verbose=True):
    '''copies entrys with spon_entry_name from arf_spon to arf_out,
    renaming with out_entry_name'''
    spon = h5py.File(arf_spon, 'r')
    out = h5py.File(arf_out, 'a')
    spon_entries = [e for e in spon.values()
                    if isinstance(e, h5py.Group) and spon_entry_name in e.name]
    for entry in spon_entries:
        new_name = entry.name.split('/')[-1].replace(spon_entry_name,
                                                     out_entry_name)
        
        print("new entry name: " + new_name)
        out[new_name] = h5py.ExternalLink(arf_spon, entry.name)
        #out.copy(entry, new_name)
        if verbose:
            print('{} from {} externaly linked to {} as {}'
                  .format(entry.name, entry.file, out.file, new_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--arf-spon',
                        help='arf file with spontaneous recordings',
                        required=True)
    parser.add_argument('-o', '--arf-out',
                        help="""entrys from ARF_SPON will be copied
                        here and renamed""",
                        required=True)
    parser.add_argument('-v', '--verbose', help='prints things',
                        action='store_true')
    args = parser.parse_args()
    print(args.arf_spon)
    main(args.arf_spon, args.arf_out, verbose=args.verbose)




















 
