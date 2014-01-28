spikechef
=========

Sorts multichannel arf data. Uses the klusta* suite.

Usage
---------
1. run stimalign.py on any arf file with a pulse channel indicating a stimulus onset
    python stimalign.py -f test.arf -v --visual
2. run jstim_label on the arf file from (1) along with it's associated jstim label file. If more than one jstim_label file exists, simply create a new file as such `cat jstimlog1 jstimlog2 jstimlog3 > jstimlogall`
    python jstim_label.py test.arf jstim-test-concat.log
3. if there is another arf file you would like to spikesort together, combine them with `mergespon.py`
4. run arftoclu.py, this is the most time intensive process, calls spikedetekt and klustakwik
5. review spikes in klustaviewa
6. create an spike arf file with clutoarf.py