# -*- coding: utf-8 -*-
"""
Created on Wed May 26 10:45:06 2021

@author: domin
"""
import numpy as np
import pandas as pd
import datetime
import math
from plot_hists import normalize_ys, x2radians
from pycircstat import omnibus, rayleigh


def uniformity_test(df, data_col, period=1, high=0.1, low=0.1, alpha=0.05):
    """calculate omnibus test for uniformity of circular data;
    period: IN DAYS;
    mean resultant vector length in range [0,1] because ys are normalized"""

    # from pycircstat.tests import rayleigh
    # from pycircstat.tests import omnibus
    n_itterations = math.ceil(len(df) / (24 * period))  # need only whole cycles..
                                                        # can calculate more precisely if not plotting
    df = pd.DataFrame(df.iloc[:, data_col])

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

        # -----------------get vector composants------------
        for i in range(len(xlow)):
            tests_lows.append(xlow[i])
            coord_low[0].append(1 * np.cos(xlow[i]))
            coord_low[1].append(1 * np.sin(xlow[i]))

        for i in range(len(xhigh)):
            tests_highs.append(xhigh[i])
            coord_high[0].append(1 * np.cos(xhigh[i]))
            coord_high[1].append(1 * np.sin(xhigh[i]))

    # -----------------Mean Resultant Vectors-----------------------
    rbar_mag_low = np.sqrt(np.sum(coord_low[0]) ** 2 + np.sum(coord_low[1]) ** 2) / len(coord_low[0])
    rbar_mag_high = np.sqrt(np.sum(coord_high[0]) ** 2 + np.sum(coord_high[1]) ** 2) / len(coord_high[0])
    print("PERIOD: {} day(s): \nThe magnitude of the resultant vector is: {}".format(period, rbar_mag_low),
          "for low values and {} for high.".format(rbar_mag_high))

    # ------------------omnibus and rauleigh-----------------------------
    omnibus_lows = omnibus(np.array(tests_lows), sz=np.radians(360 / 24 * period))[0]
    omnibus_highs = omnibus(np.array(tests_highs), sz=np.radians(360 / 24 * period))[0]
    print("p-value of Omnibus test for uniformity of low values :{}.".format(omnibus_lows),
          # sz=step size for evaluating distri, default in omnibus is 1deg; here is 360deg/24hours...
          "\np-value of Omnibus test for uniformity of high values :{}.".format(omnibus_highs))
    if omnibus_lows < alpha:
        print('Low values significant.')
    if omnibus_highs < alpha:
        print('High values significant.')
    unimod_lows = rayleigh(np.array(tests_lows))[0]
    unimod_highs = rayleigh(np.array(tests_highs))[0]
    print("p-value and z of rayleigh test for uniformity of low values :{}".format(unimod_lows),
          # sz=step size for evaluating distri, default in omnibus is 1deg; here is 360deg/24hours...
          "\np-value of rayleigh test for uniformity of high values :{}".format(unimod_highs))
    if unimod_lows < alpha:
        print('Low values significant.')
    if unimod_highs < alpha:
        print('High values significant.')
