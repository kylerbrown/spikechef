#!/usr/bin/python

import os.path
import h5py
import sys
import argparse


def parse_jstim_log(log_name):
    with open(log_name, 'r') as log_file:
        stim_list = [item.split()[0] for item in log_file.read().split('next stim: ')]
        stim_list.pop(0)
        return stim_list

    
def main():

    arf_paths = []
    log_paths = []

    parser = argparse.ArgumentParser(prog="jstim_label",
                                     description="""Label stimulus presentations in arf files,
                                     using the output of jstim saved as a text file.""")

    parser.add_argument("--overwrite", action="store_true", help=
                        "Overwrites already existing stimulus attributes.")
    parser.add_argument("files", nargs ="*", help="""List of arf files and corresponding jstim log files.
                         The first arf file will be labeled using the first log file, the second arf
                         file with the second log, and so on.""")
                        
    options = parser.parse_args()
    
    for file_name in options.files:
        root, ext = os.path.splitext(file_name)
    
        if not os.path.isfile(file_name): 
            sys.exit("\"%s\" is not a file" % file_name)

        elif ext == '.arf':        
            arf_paths.append(file_name)        
        else:
            log_paths.append(file_name)

    if len(arf_paths) == 0:
        sys.exit("No arf file given")
    elif len(log_paths) == 0:
        sys.exit("No log files given")
    elif len(log_paths) != len(arf_paths):
        sys.exit("Number of arf files given is not the same as the number of log files given")


    for arf_name, log_name in zip(arf_paths, log_paths):
                
        with h5py.File(arf_name, 'a') as arf_file:
            stim_list = parse_jstim_log(log_name)
            arf_file = h5py.File(arf_name)
        
            #obtain list of groups (which excludes datasets) in arf file root
            group_list = [entry for entry in arf_file.itervalues() if isinstance(h5py.Group) ]
            if len(group_list) != len(stim_list):
                print "The number of stimulus presentations listed in the log \"%s\" is not the same as the \n"\
                    "number of groups in the corresponding file \"%s\"" \
                    ".This file will not be labeled." %(log_name, arf_name)
                continue       

            for group, stimulus in zip(group_list, stim_list):

                #dictionary of attributes with lower case keys for case insensitive comparison
                attrs_lower = dict(zip([key.lower() for key in group.attrs.iterkeys()], 
                                       group.attrs.itervalues()))
                if 'stimulus' in attrs_lower and len(attrs_lower['stimulus']) > 0:
                    if options.overwrite:
                        del attrs_lower['stimulus']                        
                    else: 
                        print "Group %s in file %s already has \"stimulus\" attribute.  "\
                            "This group will not be labeled." %(group.name, arf_name)
                        continue

                group.attrs['stimulus'] = stimulus


if __name__ == '__main__':
    main()










