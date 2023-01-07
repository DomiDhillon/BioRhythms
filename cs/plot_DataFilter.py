# -*- coding: utf-8 -*-
"""
Created on Wed May 19 09:55:27 2021

@author: domin
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter


def butter_lowpass(cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=2):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


def plot_DataFilter(df, col_index, order=3, fs=24, cutoff=5 / 14,
                    get_filtered=False):
    """Filter requirements.
    fs= n samples per 1 time unit
    cutoff= how many times per n*unit"""

    order = order
    fs = fs  # sample rate,
    cutoff = cutoff  # desired cutoff frequency of the filter

    # timestamp
    t = df.index

    # Raw data
    data = df.iloc[:, col_index]
    ymin = np.min(data)
    ymax = np.max(data)
    data_range = [ymin - 0.05 * np.mean(ymax - ymin), ymax + 0.05 * np.mean(ymax - ymin)]

    # Filter the data, and plot both the original and filtered signals.
    y = butter_lowpass_filter(data, cutoff, fs, order)

    if get_filtered:
        filteredDF = pd.DataFrame(y, index=t)
        return filteredDF

    plt.figure(figsize=(16, 5))
    plt.plot(t, data, 'violet', label='data', alpha=0.5)
    plt.plot(t, y, 'red', linewidth=2, label='filtered data', alpha=0.8)  # filter
    plt.xlabel('Time')
    plt.ylim(data_range)
    plt.grid()
    plt.legend()

    title = df.columns[col_index]
    plt.title(title)
    plt.show()
