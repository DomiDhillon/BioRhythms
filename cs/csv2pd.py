# -*- coding: utf-8 -*-
"""
Created on Tue May 18 21:12:17 2021

@author: domin
"""

import numpy as np
import pandas as pd
import datetime
import os


def choppingNames(df, n=-3):  # to finish arguments
    """change column names to the last 3 char of the name"""

    df = df.rename(columns=lambda x: x[n:])
    return df


def new_names(df):
    """replace white space with underscore in col names"""

    new_names = [name.replace(" ", "_") for name in df.columns]
    df.columns = list(new_names)
    return df


def avg_times(df, col_index):
    """fill Nas in Timestamp col_index of timestamp column"""
    missing = list(df[df.iloc[:, col_index].isnull()].index)
    for idx in missing:
        low_i = idx - 1
        up_i = idx + 1
        while low_i in missing:
            low_i -= 1
        while up_i in missing:
            up_i += 1
        time_delta = (df.iloc[up_i, col_index] - df.iloc[low_i, col_index]) / 2
        df.iloc[idx, col_index] = df.iloc[low_i, col_index] + time_delta
    return df


def intrpl_times(df):
    """reindex timestamp so there should not be missing or skipped values
    col_index of timestamp column"""
    start = pd.to_datetime(str(df.index.min()))
    end = pd.to_datetime(str(df.index.max()))
    dates = pd.date_range(start=start, end=end, freq='1H')
    df = df.reindex(dates)
    return df


def avg_Nas(df, col_index):
    """Fill Nas in Data"""
    missing = list(df[df.iloc[:, col_index].isnull()].index)
    for idx in missing:
        df.iloc[idx, col_index] = np.mean(df.iloc[idx - 5:idx + 5, col_index])
    return df


def intrpl(df, col_index):
    """ If the missing value is the first entry, it will stay NaN, because there's
    no previous entry to interpolate with."""

    interpolated = df.iloc[:, col_index].interpolate()
    missing = list(df[df.iloc[:, col_index].isnull()].index)
    for idx in missing:
        df.iloc[idx, col_index] = interpolated.iloc[idx]
    return df


def setTimeInx(df, col_index):
    # col_index for col that should be index
    name = df.columns[col_index]
    df = df.set_index(name)
    return df


def timeSeries(df, col_index):
    """input: df with timestamp index
    col_index of data"""

    df_temp = df.iloc[:, col_index]
    df_series = pd.Series(df_temp.iloc[:, 0], index=df_temp.index)
    return df_series


def shortening(df, weeks=None, days=None, tail=False):
    # tail: if u need data from a precise date - set this date to param

    if weeks:
        delta = datetime.timedelta(weeks=weeks)
    if days:
        delta = datetime.timedelta(days=days)
    df_short = df[df.index[0]:df.index[0] + delta]
    if tail:
        df_tail = df[df.index[0] + delta:df.index[-1]]
        return df_short, df_tail
    return df_short


def csv2pd(timestamp_col, data_col="all", path=None, fileName=None, header=0, chopName=False):
    """deletes non-interpolatable col ->
    i.e. for seizures u would have to fill with zeros and not interpolate, so use data_col='all"""

    if not path:
        path = input("Folder path")
    if not fileName:
        fileName = input("File name")
    newPD = pd.read_csv(path + "\\" + fileName, header=header, decimal='.',
                        parse_dates=[0])
    df = new_names(newPD)
    df = setTimeInx(df=df, col_index=timestamp_col)
    df = df.resample('H').mean()  # average by hour
    df = intrpl_times(df=df)
    if data_col == "all":
        for i in range(len(df.columns)):
            df.iloc[:, i] = df.iloc[:, i].interpolate()
    else:
        df.iloc[:, data_col - 1] = df.iloc[:, data_col - 1].interpolate()
    # IF THE FIRST ENTRY NaN -> INTERPOLATE DO NOT FIX IT SO DELETE THE ROW
    if np.sum(list(df.iloc[0, :].isnull())) > 0:
        df = df.drop(df.iloc[0, :].name)
    if chopName:
        nOfChar = int(input("index of first or last (negative) n characters"))
        df = choppingNames(df=df, n=nOfChar)

    return df


def csv2pd_rats(path, fileName, data_col, timestamp_col):
    newPD = pd.read_csv(path + "\\" + fileName, header=0, decimal='.',
                        parse_dates=[0])
    df = new_names(newPD)
    df = avg_times(df=df, col_index=timestamp_col)
    df = avg_Nas(df=df, col_index=data_col)
    df = setTimeInx(df=df, col_index=timestamp_col)
    return df


names = ["time", "m547", "m58e", "m5a3"]
path = "../folder"  # relative path to data
path2file = path + "/data.xlsx"


def excel2pd(names=None, path2file=None, useHeader=False):
    """to use when more sheets are used with the same col names - the sheets being diff vars
    names: names of columns, if None given, they'll bee col1,..,coln """

    if not path2file:
        path2file = input("File path")
    if not names:  # if you want to use custom colnames, specify the list of names in param
        if not useHeader:  # if you want to use colnames that already exist in excel file, set TRUE
            names = ["col{}".format(i + 1) for i
                     in range(len(pd.read_excel(path2file, sheet_name=None, header=0)))]
    if not useHeader:  # ==if there are names given AND u specified F for use header
        pdDict = pd.read_excel(path2file, sheet_name=None, header=0,
                               names=names)
    else:
        pdDict = pd.read_excel(path2file, sheet_name=None, header=0)  # colnames by default
    dfnames = []
    for key in pdDict.keys():
        globals()[key.lower()] = pd.DataFrame(pdDict[key])
        dfnames.append(key.lower())
    return dfnames
