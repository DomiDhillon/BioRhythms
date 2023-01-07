# -*- coding: utf-8 -*-
"""
Created on Wed May 19 10:29:01 2021

@author: domin
"""
import numpy as np

import pandas as pd

import matplotlib.pyplot as plt
import datetime

import math

from pycircstat.tests import rayleigh, omnibus


def plotting_hourly(df, col_index):  # try with enumerate maybe it's quicker
    """first col after index is 0"""

    # import math
    n_itterations = math.ceil(len(df) / 24)

    fig = plt.figure(figsize=(7, 7))
    ax = plt.subplot(111, projection='polar')
    # Make the labels go clockwise
    ax.set_theta_direction(-1)

    # Place Zero at Top
    ax.set_theta_offset(np.pi / 2)

    for i in range(n_itterations + 1):
        theDay = df[df.index[0]:df.index[0] + datetime.timedelta(days=i, hours=23)]
        xs = theDay.index.hour
        xs = xs / 24
        xs = xs * 2 * np.pi
        ys = theDay.iloc[:, col_index]
        ax.bar(xs, ys, width=0.1, alpha=0.03, color='red')  # try arrow instead of bar, and map colors to temp?
    ax.set_xticks(np.linspace(0, 2 * np.pi, 24, endpoint=False))


    ticks = np.arange(0, 24)
    ax.set_xticklabels(ticks)

    # SET TITLE
    ax.set_ylim(np.min(df.iloc[:, col_index]), np.max(df.iloc[:, col_index]))
    plt.show()


def color_hist(df, data_col, freq='D'):
    """creates a heatmap, nrows=ndays,cols=hours of the day;
    starts at upper left corner"""

    from pandas import Grouper

    start = np.where(df.index.hour == 0)[0][0]
    end = np.where(df.index.hour == 0)[0][-1]
    df = df.iloc[start:end, :]

    series = pd.Series(df.iloc[:, data_col], index=df.index)

    groups = series.groupby(Grouper(freq=freq))  # groups by hour
    days = [g[1].values for g in groups]

    fig = plt.figure()
    ax = plt.subplot(111)
    im = ax.matshow(days, interpolation=None, aspect='auto')
    cbar = fig.colorbar(im)
    cbar.ax.set_title(df.columns[data_col], y=1.05)
    plt.show()


def normalize_ys(array, df, col_index=0):
    data = df.iloc[:, 0]
    normalized = [(i - np.min(data)) / (np.max(data) - np.min(data)) for i in array]
    return normalized


def x2radians(array, period=1):
    array = array / (period * 24)
    array = array * 2 * np.pi
    return array


def get_df_name(df):
    name = [x for x in globals() if globals()[x] is df][0]
    return name


def plot_radial(df, data_col, high=0.05, low=0.001, period=1, test_omnibus=True):
    dfname = get_df_name(df)
    colname = df.columns[data_col]
    n_itterations = math.ceil(
        len(df) / (24 * period))  # need only whole cycles.. can calculate more precisely if not plotting
    print("There was {} periods of length {} day(s).".format(n_itterations, period))
    df = pd.DataFrame(df.iloc[:, data_col])
    fig, (ax, ax2) = plt.subplots(ncols=2, subplot_kw=dict(projection="polar"), figsize=(10, 5))
    for a in [ax, ax2]:
        a.set_theta_direction(-1)  # Make the labels go clockwise
        a.set_theta_offset(np.pi / 2)  # Place Zero at Top

    coord_low = [[], []]
    coord_high = [[], []]
    tests_lows = []
    tests_highs = []
    for i in range(n_itterations + 1):
        theDay = df[df.index[0] + datetime.timedelta(days=i * period):
                    df.index[0] + datetime.timedelta(days=(i + 1) * period)]

        # --------------select the highs and lows------------
        maxTempDay = np.max(theDay.iloc[:, 0])
        minTempDay = np.min(theDay.iloc[:, 0])
        high80 = maxTempDay - ((maxTempDay - minTempDay) * high)
        low20 = maxTempDay - ((maxTempDay - minTempDay) * (1 - low))

        # -----------------normalize temperatures; select high and low values----------------------
        yhigh = theDay[theDay.iloc[:, 0] >= high80].values
        # print(yhigh)
        yhigh = normalize_ys(array=yhigh, df=df)
        ylow = theDay[theDay.iloc[:, 0] <= low20].values
        ylow = normalize_ys(array=ylow, df=df)

        # ------tranaform x to polar coordinates (radians) ---------
        xhighHOURS = theDay[theDay.iloc[:, 0] >= high80].index.hour  # moduloDAYS + .HOUR!!!
        xhighDAYS = theDay[theDay.iloc[:, 0] >= high80].index.day
        xhighDAYSmodulo = xhighDAYS % period
        xhigh = xhighHOURS + xhighDAYSmodulo * 24
        xhigh = x2radians(xhigh, period=period)

        xlowHOURS = theDay[theDay.iloc[:, 0] <= low20].index.hour  # moduloDAYS + .HOUR!!!
        xlowDAYS = theDay[theDay.iloc[:, 0] <= low20].index.day
        xlowDAYSmodulo = xlowDAYS % period
        xlow = xlowHOURS + xlowDAYSmodulo * 24
        xlow = x2radians(xlow, period=period)

        # ----------------- jitter around r=1---------------
        jitterxlow = [np.random.normal(i, 0.1, 1) for i in xlow]
        jitterylow = np.random.normal(0.9, 0.1, len(ylow))
        jitterxhigh = [np.random.normal(i, 0.1, 1) for i in xhigh]
        jitteryhigh = np.random.normal(0.9, 0.1, len(yhigh))

        ax.scatter(jitterxlow, jitterylow, alpha=0.1,
                   color="blue")
        ax2.scatter(jitterxhigh, jitteryhigh, alpha=0.1,
                    color="red")

        # -----------------get vector composants------------
        for i in range(len(xlow)):
            tests_lows.append(xlow[i])
            coord_low[0].append(1 * np.cos(xlow[i]))
            coord_low[1].append(1 * np.sin(xlow[i]))

        for i in range(len(xhigh)):
            tests_highs.append(xhigh[i])
            coord_high[0].append(1 * np.cos(xhigh[i]))
            coord_high[1].append(1 * np.sin(xhigh[i]))

    # -----------------------ticks and labels-----------------
    rticks = np.arange(0, 1, 0.2)
    ax.set_rticks(rticks)
    ax2.set_rticks(rticks)
    if period == 1:
        ax.set_xticks(np.linspace(0, 2 * np.pi, 12, endpoint=False))
        ax2.set_xticks(np.linspace(0, 2 * np.pi, 12, endpoint=False))
    else:
        ax.set_xticks(np.linspace(0, 2 * np.pi, period, endpoint=False))
        ax2.set_xticks(np.linspace(0, 2 * np.pi, period, endpoint=False))
    if period == 1:
        ticks = np.linspace(0, 24 * period, num=12, endpoint=False)
    else:
        ticks = np.linspace(0, period, num=period, endpoint=False)
    ax.set_xticklabels(ticks)
    ax2.set_xticklabels(ticks)
    ax.set_ylim(0, 1)
    ax2.set_ylim(0, 1)

    # -----------------Mean Resultant Vectors-----------------------
    alpha_bar_low = math.atan2(np.sum(coord_low[1]) / len(coord_low[0]), np.sum(coord_low[0]) / len(coord_low[0]))
    rbar_mag_low = np.sqrt(np.sum(coord_low[0]) ** 2 + np.sum(coord_low[1]) ** 2) / len(coord_low[0])
    alpha_bar_high = math.atan2(np.sum(coord_high[1]) / len(coord_high[0]), np.sum(coord_high[0]) / len(coord_high[0]))
    rbar_mag_high = np.sqrt(np.sum(coord_high[0]) ** 2 + np.sum(coord_high[1]) ** 2) / len(coord_high[0])
    ax.bar(alpha_bar_low, rbar_mag_low, color='blue', alpha=0.5, width=0.05, label="Low")

    ax2.bar(alpha_bar_high, rbar_mag_high, color='red', alpha=0.5, width=0.05, label="High")
    ax.legend()
    ax2.legend()
    fig.suptitle(dfname + ": " + colname)
    plt.show()

    # ------------------omnibus-----------------------------
    # usage of omnibus test from pycircstat.test.omnibus
    if test_omnibus:
        omnibus_lows = omnibus(np.array(tests_lows), sz=np.radians(360 / 24 * period))[0]
        omnibus_highs = omnibus(np.array(tests_highs), sz=np.radians(360 / 24 * period))[0]
        print("p-value of Omnibus test for uniformity of low values :{}.".format(omnibus_lows),
              # sz=step size for evaluating distri, default in omnibus is 1deg; here is 360deg/24hours...
              "\np-value of Omnibus test for uniformity of high values :{}.".format(omnibus_highs))
        if omnibus_lows < 0.05:
            print('Low values significant.')
        if omnibus_highs < 0.05:
            print('High values significant.')

    unimod_lows = rayleigh(np.array(tests_lows))[0]
    unimod_highs = rayleigh(np.array(tests_highs))[0]
    print("p-value and z of rayleigh test for uniformity of low values :{}".format(unimod_lows),
          # sz=step size for evaluating distri, default in omnibus is 1deg; here is 360deg/24hours...
          "\np-value of rayleigh test for uniformity of high values :{}".format(unimod_highs))
    if unimod_lows < 0.05:
        print('Low values significant.')
    if unimod_highs < 0.05:
        print('High values significant.')
