#!/usr/bin/python
description = """ runs all chef scripts given:
+ an arf file
+ stimulus label (optional)
+ stimulus alignment (optional)
+ add spontaneous data (optional)
"""
import sys
import os.path
import argparse
import stimalign
import mergespon
import jstim_label
import arftoclu

if __name__ == "__main__":
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
    parser.add_argument('--extraparams', help='extra spikedetekt parameters',
                        default=None)
    args = parser.parse_args()
    
    basename = os.path.splitext(args.arf)[0]
    cluster_results = os.path.join(basename, '_1', basename + '.clu')
    if os.path.exists(cluster_results):
        print('{} already has cluster results, skipping...')
        sys.exit()
    if args.jstim:
        print('running jstim_label...')
        jstim_label.main([args.arf], [args.jstim])

    if args.pulse:
        stimalign.main(args.arf)

    if args.spon:
        mergespon.main(args.spon, args.arf)

    arftoclu.main(args.arf, args.probe, args.extraparams)
