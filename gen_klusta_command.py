from subprocess import call
from math import ceil
import argparse

def subset(filebase, shank_num, max_spikes):
    clu_filename = "{}.clu.{}".format(filebase, shank_num)
    Nspikes = float(sum(1 for line in open(clu_filename)))
    return ceil(Nspikes/max_spikes)

def klustakwik_strings(filebase, shank_num, nchannels, max_spikes):
    subsample_factor = subset(filebase, shank_num, max_spikes)
    minclus = 3 * nchannels
    maxclus = 5 * nchannels
    klus_args = ['MaskedKlustaKwik',
                 filebase,
                 str(shank_num),
                 '-MaskStarts', str(minclus),
                 '-PenaltyK', '2',
                 '-PenaltyKLogN', '0',
                 '-UseDistributional', '1',
                 '-SplitFirst', '40',
                 '-SplitEvery', '100',
                 '-MaxIter', '400',
                 '-MaxPossibleClusters', str(maxclus),
                 '-UseMaskedInitialConditions', '1',
                 '-Subset', str(subsample_factor)
    ]
    return klus_args

def main(filebase, shank_num, nchannels=32, max_spikes=1500000, torque=False):
    klus_args = klustakwik_strings(filebase, shank_num, nchannels, max_spikes)
    scriptname = "{}.{}.sh".format(filebase, shank_num)
    print torque
    with open(scriptname, 'w') as f:
        if torque == 'beast':
            f.write('#PBS -N {}\n'.format(filebase))
            f.write('#PBS -o {}_err.txt\n'.format(filebase))
            f.write('#PBS -l nodes=1:ppn=8\n')
            f.write('#PBS -l walltime=48:00:00\n')
            f.write('#PBS -V\n')
            f.write('cd {}\n'.format(filebase))
        elif torque == 'beagle':
            print("no")

        f.write(" ".join(klus_args) + '\n')

    call(['chmod', 'u+x', scriptname])


if __name__ == "__main__":
    description='''
    convenience program for running klustakwik,
    generates a script, which you should execute on your desired machine
    '''
    parser =  argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--filebase')
    parser.add_argument('-s', '--shank-num', help="shank number",
                        default= 1, type=int)
    parser.add_argument('-n', '--n-channels', help='number of channels on shank',
                       default=32, type=int)
    parser.add_argument('-t', '--torque', help="for running on beast or beagle, \
    say 'beast' or 'beagle'.")
    args = parser.parse_args()
    main(args.filebase, args.shank_num, args.n_channels, torque=args.torque)
