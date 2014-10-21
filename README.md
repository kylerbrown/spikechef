spikechef
=========
Sorts multichannel arf data. Uses the klusta* suite.

For each program, try `--help` to see options


V 0.3
==================
1. collect data using Intan's RHD2000 interface software, which creates *.rhd files in a single directory.
2. use `rhd2arf.m` (Matlab script) to create arf files. [code](https://github.com/kylerbrown/rhd2arf) You can run the script from the command line from within the *.rhd directory by typing `matlab -nodisplay -r "path(path, '~/code/rhd2arf');rhd2arf;exit"`
3. use `label_stim` to annotate arf file with stimulus times and `dumber_sums.py` to get an estimate of stimulus response.
3. convert those arf files to .kwd (hdf5 format for klusta suite) with `arf2kwd.py`.
4. also create/use appropriate .prm and prb files (see klusta suite docs). and run `klusta EXPERIMENT.prm`
5. merge spikes back into the arf file with ...(TODO)



V 0.2
==================

Usage
---------
1. run `arftodat.py` on .arf(s)
2. run `detectspikes.py` on generated .dat files
3. generate a clustering script with `gen_klusta_command.py`, then run the resulting script, which is _very_ memory intensive and may take 1-2 days.
4. After clustering, use klustaviewer to review
5. use `clutoarf.py` to create spike-sorted arf file for analysis!

