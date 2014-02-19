#!/usr/bin/python

import h5py
import matplotlib.pyplot as plt
spike_file = h5py.File('bk196-2014_01_03-hvc-25s-0-0_spikes.arf')
plt.subplot(211)
entries = sorted([x for x in spike_file.values() if type(x) == h5py.Group], key=repr)
for i,entry in enumerate(entries[60::2]):
    if 'spikes' in entry:
        plt.scatter(entry['spikes']['start']/30000.,
                    entry['spikes']['cluster_manual']/130.+i,
                    c=plt.cm.prism(entry['spikes']['cluster_auto']/130.), alpha=.3, edgecolors='none',
                    s=20)


plt.ylabel('trial')
plt.title('bos')
plt.axis('tight')
plt.xlim(0, 4)


plt.subplot(212)
for i,entry in enumerate(entries[61::2]):
    if 'spikes' in entry:
        plt.scatter(entry['spikes']['start']/30000.,
                    entry['spikes']['cluster_manual']/130.+i,
                    c=plt.cm.prism(entry['spikes']['cluster_auto']/130.), alpha=.3, edgecolors='none',
                    s=20)

plt.xlabel('time (seconds), stimus roughly from 1-2')
plt.ylabel('trial')
plt.title('rbos')
plt.axis('tight')
plt.xlim(0, 4)
#plt.ylim(0, 150)
plt.show()



















