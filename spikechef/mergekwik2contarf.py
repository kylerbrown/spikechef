import h5py
import numpy as np
import matplotlib.pyplot as plt


def get_spike_times(kwik_channel):
    return kwik_channel['spikes']['time_samples']


def get_spike_cluster(kwik_channel):
    return kwik_channel['spikes']['clusters']['main']


def get_cluster_group(kwik_channel):
    clusters = kwik_channel['clusters']['main'].values()
    clusters_id = [int(i.name.split('/')[-1])
                   for i in clusters]
    group = [i.attrs['cluster_group'] for i in clusters]
    return {i:g for i,g in zip(clusters_id, group)}


def get_cluster_group_names(kwik_channel):
    groups = kwik_channel['cluster_groups']['main'].values()
    group_id = [int(i.name.split('/')[-1])
                   for i in groups]
    label = [i.attrs['name'] for i in groups]
    return {l: i for l, i in zip(label, group_id)}


def get_spike_waveforms(kwx_channel):
    pass


def get_geometry(kwik):
    """ returns an Nelectrode by 3 array, where each row has
    electrode number, x position, y position"""
    geometry = []
    for kwik_channel in kwik['channel_groups'].values():
        channels = kwik_channel['channels'].values()
        channel_nums = [int(i.name.split('/')[-1]) for i in channels]
        channel_geometry = [i.attrs['position'] for i in channels]
        shank_geometry = [np.insert(geo, 0, c_num)
                          for c_num, geo in zip(channel_nums, channel_geometry)]
        geometry.extend(shank_geometry)
    geometry = np.array(geometry)
    
    return geometry[argsort(geometry[:,0]),:] #sorted by electrode number


def geometry_array

def main(kwik, kwx, arf):
    pass




if __name__ == "__main__":

    kwik_fname = "/home/kjbrown/forebrain_syrinx/data/k405/2014-05-16/site_1/k405_140516_cont.kwik"
    kwx_fname = "/home/kjbrown/forebrain_syrinx/data/k405/2014-05-16/site_1/k405_140516_cont.kwx"
    arf_fname = "/home/kjbrown/forebrain_syrinx/data/k405/2014-05-16/site_1/k405_140516.arf"
    with h5py.File(kwik_fname, 'r') as kwik,\
    h5py.File(kwx_fname, 'r') as kwx,\
    h5py.File(arf_fname, 'r') as arf:
        main(kwik, kwx, arf)
