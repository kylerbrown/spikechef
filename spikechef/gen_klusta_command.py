from subprocess import call
import os.path
from math import ceil
import argparse


def subset(filebase, directory, shank_num, max_spikes):
    clu_filename = "{}.clu.{}".format(os.path.join(directory, filebase), 
                                      shank_num)
    Nspikes = float(sum(1 for line in open(clu_filename)))
    return int(ceil(Nspikes/max_spikes))


def klustakwik_strings(filebase, directory, shank_num, nchannels, max_spikes):
    subsample_factor = subset(filebase, directory, shank_num, max_spikes)
    minclus = 3 * nchannels
    maxclus = 8 * nchannels
    klus_args = ['MaskedKlustaKwik',
                 filebase,
                 str(shank_num),
                 #'-MaskStarts', str(minclus),
                 '-PenaltyK', '1',
                 '-PenaltyKLogN', '0',
                 '-UseDistributional', '1',
                 #'-SplitFirst', '40',
                 #'-SplitEvery', '100',
                 #'-MaxIter', '400',
                 #'-MaxPossibleClusters', str(maxclus),
                 '-UseMaskedInitialConditions', '1',
                 '-Subset', str(subsample_factor)
    ]
    return klus_args


def main(filebase, directory,
         shank_num, nchannels=32, max_spikes=800000, torque=False):
    filebase = os.path.split(filebase)[-1]
    klus_args = klustakwik_strings(filebase, directory,
                                   shank_num, nchannels, max_spikes)
    scriptname = "{}.{}.sh".format(os.path.join(directory, filebase),
                                   shank_num)
    print torque
    with open(scriptname, 'w') as f:
        if torque == 'beast':
            f.write('#PBS -N {}{}\n'.format(filebase[-15:], shank_num))
            f.write('#PBS -o {}_{}_err.txt\n'.format(filebase, shank_num))
            f.write('#PBS -l nodes=1:ppn=5\n')
            f.write('#PBS -l walltime=192:00:00\n')
            f.write('#PBS -V\n')
            f.write('cd $PBS_O_WORKDIR\n')
            f.write(" ".join(klus_args) + '\n')
        elif torque == 'beagle':
            f.write('#PBS -N {}{}\n'.format(filebase[-15:], shank_num))
            f.write('#PBS -o {}_{}_err.txt\n'.format(filebase, shank_num))
            f.write('#PBS -l mppwidth=1\n')
            f.write('#PBS -l walltime=192:00:00\n')
            f.write('cd $PBS_O_WORKDIR\n')
            f.write("aprun -n 1 -N 1 ")
            f.write(" ".join(klus_args) + '\n')
        else:
            f.write(" ".join(klus_args) + '\n')

    call(['chmod', 'u+x', scriptname])


if __name__ == "__main__":
    description = '''
    convenience program for running klustakwik,
    generates a script, which you should execute on your desired machine
    '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--filebase')
    parser.add_argument('-d', '--directory',
                        help="directory containing the files",
                        default='./')
    parser.add_argument('-s', '--shank-num', help="shank number",
                        default=1, type=int)
    parser.add_argument('-n', '--n-channels', help='number of channels on shank',
                        default=32, type=int)
    parser.add_argument('-t', '--torque', help="for running on beast or beagle, \
    say 'beast' or 'beagle'.")
    args = parser.parse_args()
    main(args.filebase, args.directory, 
         args.shank_num, args.n_channels, torque=args.torque)
