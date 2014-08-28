from __future__ import division, print_function, unicode_literals
import argparse
import os.path
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb

# spike timing
def get_kwik_shanks(kwik):
    return kwik['channel_groups'].values()

def get_spike_times(kwik_channel):
    return kwik_channel['spikes']['time_samples']


def get_spike_cluster(kwik_channel):
    return kwik_channel['spikes']['clusters']['main']


def get_cluster_spikes(cluster_id, kwik_channel):
    spikes = get_spike_times(kwik_channel)
    spike_ids = get_spike_cluster(kwik_channel)
    id_mask = spike_ids.value == cluster_id
    return spikes[id_mask]


def get_cluster_group(kwik_channel):
    clusters = kwik_channel['clusters']['main'].values()
    clusters_id = [int(i.name.split('/')[-1])
                   for i in clusters]
    group = [i.attrs['cluster_group'] for i in clusters]
    return [(i, g) for i,g in zip(clusters_id, group)]


def get_cluster_group_names(kwik_channel):
    groups = kwik_channel['cluster_groups']['main'].values()
    group_id = [int(i.name.split('/')[-1])
                   for i in groups]
    label = [i.attrs['name'] for i in groups]
    return {i: l for l, i in zip(label, group_id)}

# spike shape/location

def get_spike_waveforms(kwx_shank):
    return kwx_shank['waveforms_filtered']


def get_shank_channel_order(kwik_channel):
    return kwik_channel.attrs['channel_order']


def get_shank_geometry(kwik_channel):
    channels = kwik_channel['channels'].values()
    channel_nums = [int(i.name.split('/')[-1]) for i in channels]
    channel_geometry = [i.attrs['position'] for i in channels]
    shank_geometry = [np.insert(geo, 0, c_num)
                      for c_num, geo in zip(channel_nums, channel_geometry)]
    return np.array(shank_geometry)


def get_shank_geometry_dict(kwik_channel):
    channels = kwik_channel['channels'].values()
    channel_nums = [int(i.name.split('/')[-1]) for i in channels]
    channel_geometry = [i.attrs['position'] for i in channels]
    return {n: geo for n, geo in zip(channel_nums, channel_geometry)}


def get_all_geometry(kwik):
    """ returns an Nelectrode by 3 array, where each row has
    electrode number, x position, y position"""
    geometry = []
    for kwik_channel in kwik['channel_groups'].values():
        shank_geometry = get_shank_geometry(kwik_channel)
        geometry.extend(shank_geometry)
    geometry = np.array(geometry)
    return geometry[np.argsort(geometry[:,0]),:]  # sorted by electrode number


def plot_cluster_waves(kwx_shank, kwik_shank, cluster_id, nwaves=300, mean=True):
    spikes = get_spike_times(kwik_shank)
    spike_ids = get_spike_cluster(kwik_shank)
    id_mask = spike_ids.value == cluster_id
    spike_nums = np.arange(len(spikes))[id_mask]
    # randomly select nwaves waves:
    randomed_spike_nums = spike_nums[np.random.permutation(len(spike_nums))]
    wave_ids = randomed_spike_nums[:nwaves]
    wave_mask = np.zeros(get_spike_waveforms(kwx_shank).shape[0], 'bool')
    wave_mask[wave_ids] = True
    waves = get_spike_waveforms(kwx_shank)[wave_mask, :, :]
    geometry = get_shank_geometry_dict(kwik_shank)
    channel_order = get_shank_channel_order(kwik_shank)
    for i, ch_n in enumerate(channel_order):
        geox, geoy = geometry[ch_n]
        wavey = waves[:, :, i].T
        wavey += 300*geoy
        wavex = np.arange(wavey.shape[0]) / 30000. * 1000
        wavex += wavey.shape[0]*geox / 30000. * 1000
        if mean:
            wave_u = np.mean(wavey, 1)
            wave_std = np.std(wavey, 1)
            plt.plot(wavex, wave_u, 'k')
            plt.fill_between(wavex, wave_u, wave_u+wave_std, color='grey', alpha=0.5)
            plt.fill_between(wavex, wave_u, wave_u-wave_std, color='grey', alpha=0.5)
        else:
            plt.plot(wavex, wavey, 'k', alpha=0.1)

def N_colors(N, Srange=(.5, 1), Vrange=(.5, 1)):
    """returns N unique rgb colors for plotting,
    chosen via maximal hue distance in HSV space"""
    H = np.linspace(0, 1-1./N, N)
    S = np.random.rand(N)*(Srange[1]-Srange[0]) + Srange[0]
    V = np.random.rand(N)*(Vrange[1]-Vrange[0]) + Vrange[0]
    HSV = np.dstack((H,S,V))
    return hsv_to_rgb(HSV)


def get_starts(arf, name='bos'):
    """returns the times (in samples)
    of stimuli with name=NAME"""
    time_dset = arf['entry']['stimulus_time']
    print(name)
    mask = time_dset['name'.encode('utf-8')] == name
    return time_dset['start'.encode('utf-8')][mask]


def peristimulus_times(arf, spike_times, pre=-2, post=4, label="bos",
                       sampling_rate=30000):
    """returns a list of spike time lists,
    input spike times are in samples and pre, post are in seconds
    spike_times and labels must had the same sampling_rate
    """
    starts = get_starts(arf, name=label)
    peri_times = []
    for start in starts:
        mask = np.logical_and(spike_times > pre*sampling_rate + start,
                              spike_times < post*sampling_rate + start)
        epoch_times =  spike_times[mask].astype(int) - start
        peri_times.append(epoch_times)
    return peri_times


def plot_raster(peri_times, spike_sr=30000):
    for i, epoch_times in enumerate(peri_times):
        plt.vlines(epoch_times/spike_sr, i, i+1)


def plot_song_spec(stimulus_dset):
    plt.specgram(stimulus_dset, Fs=stimulus_dset.attrs['sampling_rate'])
    plt.ylim(0,9000)

def plot_song_osc(stimulus_dset):
    t = np.arange(len(stimulus_dset)) / stimulus_dset.attrs['sampling_rate']
    plt.plot(t, stimulus_dset)

def get_all_spike_times(kwik, group=None):
    '''returns a list of all spike times from group GROUP'''
    shanks = get_kwik_shanks(kwik)
    all_spike_times = []
    for shank in shanks:
        shank_spikes = []
        clusters = get_cluster_group(shank)
        cluster_groups = get_cluster_group_names(shank)
        for ith_cluster, (cluster_id, cl_group) in enumerate(clusters):
            if cluster_groups[int(cl_group)] == group:
                spike_times = get_cluster_spikes(cluster_id, shank)
                shank_spikes.append(spike_times)
        all_spike_times.append(shank_spikes)
    return all_spike_times

