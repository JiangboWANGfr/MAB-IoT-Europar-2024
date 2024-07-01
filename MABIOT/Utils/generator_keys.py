import argparse
from ast import Return
import sys
import time
import math
import pandas as pd
import numpy as np
import itertools
import pickle


def generator_keys_basic(num_allocated_device, precision):
    keys = []
    keeped_keys = []
    elements = []
    for it in range(0, num_allocated_device):
        for val in np.linspace(0, 1, precision):
            elements.append(val)
    keys = list(set(itertools.combinations(elements, num_allocated_device)))
    key_array = np.array(keys)
    for key in key_array:
        if (round(key.sum(), 2) == 1.0):
            keeped_keys.append(key.tolist())
    return keeped_keys


def generator_keys(num_allocated_device, num_devices, precision):
    keys = []
    keeped_keys = []
    elements = []
    for it in range(0, num_allocated_device):
        for val in np.linspace(0, 1, precision):
            elements.append(val)
    keys = list(set(itertools.combinations(elements, num_allocated_device)))
    key_array = np.array(keys)
    for key in key_array:
        if (round(key.sum(), 2) == 1.0):
            keeped_keys.append(key.tolist())

    devices_id = [i for i in range(0, num_devices)]
    devices_comb = list(
        set(itertools.combinations(devices_id, num_allocated_device)))
    final_keys = []
    for comb in devices_comb:
        for keeped_key in keeped_keys:
            act = [0.0 for x in range(num_devices)]

            # Fill in the device list in the sampled positions
            for index_comb, index_list in zip(comb, range(0, num_allocated_device)):
                act[index_comb] = round(keeped_key[index_list], 1)

            final_keys.append(act)

    return final_keys


def generate_save_keys(num_allocated_device, num_devices, precision, path):
    keys = generator_keys(num_allocated_device, num_devices, precision)

    with open(path, 'wb') as fp:
        pickle.dump(keys, fp)


def load_keys(path):
    with open(path, 'rb') as fp:
        keys = pickle.load(fp)
    return keys
# final_keys = generator_keys(4,8,11)
# print(len(final_keys))
