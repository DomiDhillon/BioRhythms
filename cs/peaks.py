# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 16:23:34 2021

@author: domin
"""
import os
import pandas as pd
import numpy as np
import datetime
from cs.csv2pd import *
import matplotlib.pyplot as plt
from scipy import stats, signal


def creatingFarmFolder(path, csv_name):
    """creates folder for separate cows if it doesn't exist"""

    os.chdir(path)
    try:
        os.mkdir('./' + csv_name[:-4])
    except FileExistsError:
        pass
    os.chdir('./' + csv_name[:-4])


def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)


def separatingCows(dfFarm, colname4grouping='cow'):
    for cow in (dfFarm.groupby(dfFarm[colname4grouping])):
        cow[1].to_csv(str(cow[0]) + '.csv', index=False)

    csvList = os.listdir()
    csvList = [filename for filename in csvList if filename.endswith("csv")]
    return csvList


def get_prominences(df, col_index, prominences, peaks_low, peaks,
                    prominences_low, prominences_high):
    prominences = prominences
    peaks = peaks
    prominences_high = prominences_high
    prominences_low = prominences_low

    inversed_col = [-x for x in df.iloc[:, col_index]]
    peaks_l = signal.find_peaks(inversed_col)[0]
    prominences_l = signal.peak_prominences(inversed_col, peaks_l)[0]
    prominences_l = [-x for x in prominences_l]
    prominences.append(prominences_l)

    col2analyse = df.iloc[:, col_index]
    peaks_h = signal.find_peaks(col2analyse)[0]
    prominences_h = signal.peak_prominences(col2analyse, peaks_h)[0]
    prominences.append(list(prominences_h))

    # merge prominence values and append found peaks
    peaks_low.append(peaks_l)
    peaks.append(peaks_h)
    prominences_low.append(prominences_l)
    prominences_high.append(prominences_h)
    return prominences, peaks_low, peaks, prominences_low, prominences_high


def normal_fitting2(df, oriDF, col_index, distance=1, CIlim=0.95):
    """checks whether df is a tuple - from split df due to NAs. If yes, find peaks in boths, then fit
    normal distri to merged prominence values then plot it on common graph
    HAVE TO SAVE DF AS TUPLE EVEN IF ONLY ONE"""

    prominences = []
    peaks_low = []
    peaks = []
    prominences_low = []
    prominences_high = []
    oriDF = oriDF.resample(str(distance) + "h").mean()
    dfLIST = [df[i].resample(str(distance) + "h").mean() for i in range(len(df))]
    df = tuple(dfLIST)

    # if type(df) is tuple:                    #if tuple, merge prom values from all sections
    for i in range(len(df)):
        prominences, peaks_low, peaks, prominences_low, prominences_high = get_prominences(df=df[i],
                                                                                           col_index=col_index,
                                                                                           prominences=prominences,
                                                                                           peaks_low=peaks_low,
                                                                                           peaks=peaks,
                                                                                           prominences_low=prominences_low,
                                                                                           prominences_high=prominences_high)
    prominences = np.concatenate(prominences)

    # fitting gamma to prominences
    m, sd = stats.norm.fit(prominences)  # beta=scale
    xhist = plt.hist(prominences, density=True,
                     color="grey", alpha=0.5)
    quantile = np.linspace(stats.norm.ppf(0.001, loc=m, scale=sd),
                           stats.norm.ppf(0.999, loc=m, scale=sd), 1000)
    CI = stats.norm.interval(CIlim, loc=m, scale=sd)
    print(CI)
    R = stats.norm.pdf(quantile, loc=m, scale=sd)
    plt.vlines(x=[CI[1], CI[0]], ymin=min(R), ymax=max(R), color=["red", "green"], linestyle="dashed")
    plt.plot(quantile, R, color="darkblue")
    plt.show()

    plt.figure(figsize=(16, 5))
    plt.plot(oriDF.index, oriDF.iloc[:, col_index], 'pink', label='data', alpha=0.3)
    # plt.plot(testSlice1.index, testSlice1.iloc[:,1], 'violet', label='data',alpha=0.7)
    # plt.plot(testSlice2.index, testSlice2.iloc[:,1], 'violet', label='data',alpha=0.7)
    for i in range(len(peaks)):
        peaksGammaHigh = peaks[i][prominences_high[i] > CI[1]]
        peaksGammaLow = peaks_low[i][prominences_low[i] < CI[0]]
        plt.scatter(df[i].index[peaksGammaHigh], df[i].iloc[:, col_index][peaksGammaHigh], color="red")
        plt.scatter(df[i].index[peaksGammaLow], df[i].iloc[:, col_index][peaksGammaLow], color="green")
        # plt.plot(col2analyse.index, col2analyse, 'pink', label='data',alpha=0.5)
        plt.plot(df[i].index, df[i].iloc[:, col_index], 'violet', label='data', alpha=0.5)
        # plt.plot(df.index, inversed_col, 'darkblue', label='data',alpha=0.5)
    plt.show()


def cuttingOutNas(csvList, distance):
    for i in range(len(csvList)):
        cow = pd.read_csv(csvList[i], header=0, decimal='.',
                          parse_dates=[0])
        cow = new_names(cow)
        cow = setTimeInx(df=cow, col_index=0)
        cow = intrpl_times(df=cow)
        # time range of nulls
        nullValues = [list(cow[cow.iloc[:, i].isnull()].index) for i in range(1, 5)]  # len(cow.columns))]
        if all_equal(nullValues):
            nullValues = nullValues[0]
        else:
            np.concatenate(nullValues)
            nullValues = np.unique(nullValues)
        null_range = pd.date_range(start=nullValues[0], end=nullValues[-1])

        Slice1 = cow[cow.index < null_range[0]]
        Slice2 = cow[cow.index > null_range[-1]]
        Slice = (Slice1, Slice2)

        for j in range(1, 5):
            print("Cow n." + str(csvList[i][:-4]) + " , col: " + str(cow.columns[j]))
            normal_fitting2(df=Slice, oriDF=cow, col_index=j, distance=distance)


def farm2CSV2cows(farmNumber=1, path= "../data/cows",
                  distance=1):
    os.chdir(path)
    csvList = os.listdir()
    csvList = [filename for filename in csvList if filename.endswith("csv")]

    farm_i = farmNumber - 1  # Farm number YOU WANT TO PROCESS NOW -----------------------------

    csv_name = csvList[farm_i]
    df = pd.read_csv(csvList[farm_i], header=0, parse_dates=True)
    df.iloc[:, 2] = [0 if i == 24 else i for i in df.iloc[:, 2]]  # set midnight to 0, not 24
    df.iloc[:, 2] = [str(i) + ':00:00' for i in df.iloc[:, 2]]  # add minutes and seconds in time col
    df['date'] = pd.to_datetime(df['date'])  # change to date format
    timestamp = pd.to_datetime(df['date'].dt.date.astype(str)
                               + ' '
                               + df['hour'].astype(str)),  # put date and time together

    df.drop(['date', 'hour'], inplace=True, axis=1)  # delete the cols since it will be index
    df['timestamp'] = np.array(timestamp[0])
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    df.iloc[:, 0] = [day + datetime.timedelta(days=1) if day.hour == 0 else day for day in
                     df.iloc[:, 0]]  # new day if midnight

    creatingFarmFolder(path=path, csv_name=csv_name)

    separatingCows(dfFarm=df, colname4grouping="cow")

    csvList = os.listdir()
    csvList = [filename for filename in csvList if filename.endswith("csv")]

    cuttingOutNas(csvList=csvList, distance=distance)
