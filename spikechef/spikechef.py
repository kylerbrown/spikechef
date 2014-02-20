#!/usr/bin/python
description = """ runs all chef scripts given:
+ an arf file
+ stimulus label (optional)
+ stimulus alignment (optional)
+ add spontaneous data (optional)
"""


import argparse
import subprocess
import spikechef.stimalign
import spikechef.mergespon

parser = argparse.ArgumentParser(description=description)
parser.add_argument('--arf', help='Arf file for sorting',
                    required=True)
parser.add_argument('--probe',
                    help='Probe file specifying the geometry of the probe',
                    required=True)
parser.add_argument('--jstim', help="""a jstim log for
assigning stimuli to entries""",
                    default=None)
parser.add_argument('--spon', help="another arf file to also be sorted",
                    default=None)
parser.add_argument('--pulse', help="determines pulse location \
for replay experiments",
                    action='store_true')
args = parser.parse_args()

if args.jstim:
    subprocess.call(['python',
                     '/home/kjbrown/spikechef/jstim_label.py',
                     args.arf, args.jstim])

if args.pulse:
    stimalign.main(args.arf)

if args.spon:
    mergespon.main(args.spon, args.arf)


subprocess.call(['python',
                 '/home/kjbrown/spikechef/arftoclu.py',
                 '--arf', args.arf,
                 '--probe', args.probe,
                 '--detektparams',
                 '/home/kjbrown/spikechef/extra_spikedetekt_params',
                 '--cluster'])
