#!/usr/bin/python
description = """ runs all chef scripts given:
+ an arf file
+ stimulus label (optional)
+ stimulus alignment (optional)
+ add spontaneous data (optional)
"""


import argparse


parser = argparse.ArgumentParser(description=description)
parser.add_argument('--arf', help='Arf file for sorting',
                    required=True)
parser.add_argument('--probe',
                    help='Probe file specifying the geometry of the probe',
                    required=True)
parser.add_argument('--detektparams',
                    help='extra spikedetect parameters file',
                    default=None)
parser.add_argument('--view',
                    help='Opens data in klustaviewa after sorting',
                    action='store_true')
parser.add_argument('--jstim', help="a jstim log for assigning stimuli to entries",
                    default=None)
parser.add_argument('--spon', help="another arf file to also be sorted",
                    default=None)
args = parser.parse_args()

if args.jstim:
    subprocess.call(['python',
                     '/home/kjbrown/spikechef/jstim_label',
                     args.arf, args.jstim])
    subprocess.call(['python',
                     '/home/kjbrown/spikechef/jstim_label',
                     
]
    )






