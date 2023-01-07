# -*- coding: utf-8 -*-
"""
Created on Wed May 19 10:05:19 2021

@author: domin
"""
import numpy as np
import matplotlib.pyplot as plt
import pywt
from matplotlib import ticker
import copy
import random
import pandas as pd


def morlet_transform(array, sampling_freq, scale_max):
    scales = np.arange(1, scale_max)  ##Return numbers spaced evenly on a log scale (a geometric progression).
    array = [(i - np.min(array)) / (np.max(array) - np.min(array)) for i in array]  # NORMALIZE - important

    # wavelet transform
    coef, freqs = pywt.cwt(array, scales, "cmor1.5-1.0", sampling_period=1 / sampling_freq)
    power = abs(coef)
    average_power = np.mean(power, axis=1)
    return coef, freqs, power, average_power, scales


def surrogate(df, col_index, sampling_freq, scale_max, n_surrogate=10):
    """Randomly shuffled datapoint-datasets analysis to contrast peaks in ori data (if any)"""

    arr2shuffle = copy.deepcopy(df)
    arr2shuffle = list(arr2shuffle.iloc[:, col_index])
    shuffled = []
    for i in range(n_surrogate + 1):
        shuffled.append(random.sample(arr2shuffle, k=len(arr2shuffle)))

    coefs = []
    freqs = []
    power = []
    average_power = []
    for arr in shuffled:
        coefs.append(morlet_transform(array=arr, sampling_freq=sampling_freq, scale_max=scale_max)[0])
        freqs.append(morlet_transform(array=arr, sampling_freq=sampling_freq, scale_max=scale_max)[1])
        power.append(morlet_transform(array=arr, sampling_freq=sampling_freq, scale_max=scale_max)[2])
        average_power.append(morlet_transform(array=arr, sampling_freq=sampling_freq, scale_max=scale_max)[3])
        ssd = np.std(average_power, axis=0)
    coefs, freqs, power, average_power = [np.mean(i, axis=0) for i in [coefs, freqs, power, average_power]]

    return coefs, freqs, power, average_power, ssd, shuffled


def plot_spect(df, col_index, title="", sampling_freq=24,
               sampling_unit="hours", sampling_period='days',
               scale_max=130, n_surrogate=10):
    """plot spectrogram (yaxis in log2 scale) & periodogram"""
    if not title:
        title = df.columns[col_index]
    array = df.iloc[:, col_index]
    coefs, freqs, power, average_power, scales = morlet_transform(array=array,
                                                                  sampling_freq=sampling_freq,
                                                                  scale_max=scale_max)
    scoefs, sfreqs, spower, saverage_power, ssd, shuffled = surrogate(df=df, col_index=col_index,
                                                                      sampling_freq=sampling_freq, scale_max=scale_max,
                                                                      n_surrogate=n_surrogate)
    # Spectogram
    fig = plt.figure(figsize=(18, 5))
    gs = fig.add_gridspec(1, 3)

    ax1 = fig.add_subplot(gs[0, :2])
    #ax3=fig.add_subplot(gs[1,:2])

    # surrogate
    cax1 = ax1.pcolormesh(np.arange(0, len(array)),
                          1 / freqs, power,
                          vmin=power.min(), vmax=power.max(),
                          cmap='plasma',
                          shading="gouraud")  # (1/freqs) will give you the period, if you want the frequency you use freqs

    # wt of surrogate
#    cax3 = ax3.pcolormesh(np.arange(0, len(array)), 1 / sfreqs, spower,
#                          vmin=power.min(), vmax=power.max(),
#                          cmap='plasma', shading="gouraud")

    # Cone of Influence (edge effect)
    COIlow = [np.sqrt(2) * s for s in scales]
    COIhigh = [len(array) - np.sqrt(2) * s for s in scales]
    ax1.plot(COIlow, 1 / freqs, color="blue")
    ax1.plot(COIhigh, 1 / freqs, color="blue")
    ax1.fill_between(COIlow, 1 / freqs, np.max(1 / freqs), color='grey', alpha=0.6)
    ax1.fill_between(COIhigh, 1 / freqs, np.max(1 / freqs), color='grey', alpha=0.6)

    for ax in [ax1]:
        ax.set_xlabel("Time (" + sampling_unit + ")")  # set unit as arg
        ax.set_ylabel("Period (" + sampling_period + ")")
        ax.set_yticks(np.round(1 / freqs, 0))
        ax.set_yscale('log', base=2)

        ax.get_yaxis().get_major_formatter().labelOnlyBase = False
        ax.get_yaxis().set_major_formatter(ticker.ScalarFormatter())
        ax.set_ylim(0.5, np.ceil(np.max(1 / freqs)))
    cbar1 = fig.colorbar(cax1, fraction=0.1)
    cbar1.ax.set_title('Power')
    ax1.set_title("Spectrogram")
    # ax3.set_title("Surrogate")

    # Periodogram
    ax2 = fig.add_subplot(gs[0, 2])
    # ax4=fig.add_subplot(gs[1,2])
    ax2.plot((1 / freqs), average_power, color='purple', label='data')
    ax2.plot((1 / sfreqs), saverage_power, color='gray', label='surrogate')

    # Define the confidence interval
    se = ssd / np.sqrt(len(shuffled))  # standard deviate/ sqrt(n)
    ci = 1.96 * se
    ax2.fill_between((1 / sfreqs), (saverage_power - ci), (saverage_power + ci), color='grey', alpha=0.1)

    ax2.legend(loc='lower right')
    ax2.set_title("Periodogram ")
    # for ax in [ax2,ax4]:
    ax2.set_xlabel('Period')
    ax2.set_ylabel('average Power')
    # ax.tick_params(axis='x',labelrotation=45)
    locs = np.arange(0, np.max(1 / freqs), step=2)
    ax2.xaxis.set_minor_locator(ticker.FixedLocator(locs))
    ax2.xaxis.set_major_locator(ticker.NullLocator())
    ax2.xaxis.set_minor_formatter(ticker.ScalarFormatter())
    ax2.yaxis.set_major_locator(ticker.NullLocator())
    ax2.yaxis.set_minor_formatter(ticker.ScalarFormatter())
    if scale_max > 600:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax.xaxis.get_minorticklabels(), rotation=45)

    figtitle = fig.suptitle(title, y=0.98)
    figtitle.set_fontsize(15)
    plt.show()
    shuffled = np.mean(shuffled, axis=0)
    shuffled = pd.DataFrame(shuffled, index=df.index)

    #can return processed shuffled dataset for further plotting
    #return shuffled
