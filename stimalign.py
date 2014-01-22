#!/usr/bin/python

import argparse


description = '''
stimalign.py

used the impulse channel to provide a reference point for aligning the stimulus trials.

This is required for experiments where jstim is running on a separate JACK server.
E.g. Using an Intan board for recording and a audio interface for stimulus presentation.
'''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('--arf', help='raw data arf file',
                    required=True)
parser.add_argument('--imp-channel', help='jrecord channel containing the timing impulse',
                    default=-1)





















