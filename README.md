spikechef
=========

Sorts multichannel arf data. Uses the klusta* suite.

Usage
---------
1. run `arftodat.py` on .arf(s)
2. run `detectspikes.py` on generated .dat files
3. generate a clustering script with `gen_klusta_command.py`, then run the resulting script, which is _very_ memory intensive and may take 1-2 days.
4. After clustering, use klustaviewer to review
5. use `clutoarf.py` to create spike-sorted arf file for analysis!

For each program, try `--help` to see options
