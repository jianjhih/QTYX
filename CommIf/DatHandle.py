#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import pandas as pd

def day_down_resample(day_data, type_='W-FRI'):
    # 日线降采样

    # 周线Close等于一周中最后一个交易日Close
    # 周线Open等于一周中第一个交易日Open
    # 周线High等于一周中High的最大值
    # 周线Low等于一周中Low的最小值
    # 周线Volume等于一周中Volume的总和

    # 更优雅的实现方式
    CONVERSION = {
         'Open': 'first',
         'Close': 'last',
         'High': 'max',
         'Low': 'min',
         'vol': 'sum'
    } if 'vol' in day_data.columns else {
         'Open': 'first',
         'Close': 'last',
         'High': 'max',
         'Low': 'min',
         'Volume': 'sum'
    }

    return day_data.resample(
        type_,
        closed='right',
        label='right'
    ).apply(CONVERSION).fillna(method='bfill', axis=0)  # NAN值填充)

# 前复权
def day_to_qfq(day_data):
    # 今日收盘价 = 昨日收盘价 * (1+涨跌幅）——> 昨日收盘价 = 今日收盘价*(1/(1+涨跌幅))

    CONV = {
        'CLOSE': 'Close',
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'PCT': 'Pctchg'

    } if 'Close' in day_data.columns else {
        'CLOSE': '收盘价',
        'OPEN': '开盘价',
        'HIGH': '最高价',
        'LOW': '最低价',
        'PCT': '涨跌幅'
    }

    # 复权处理完成后再排序
    day_data.sort_index(ascending=False, inplace=True)

    # 计算前复权因子
    day_data['fd_factor'] = (1 / (day_data[CONV['PCT']] / 100 + 1)).cumprod()

    day_data['close_fd'] = day_data.iloc[0][CONV['CLOSE']] * day_data['fd_factor']  # 相乘得到后复权价
    day_data['close_fd'] = day_data['close_fd'].shift(1)
    day_data.iloc[0, day_data.columns.get_loc('close_fd')] = day_data.iloc[0, day_data.columns.get_loc(CONV['CLOSE'])]

    day_data['open_fd'] = day_data[CONV['OPEN']] / day_data[CONV['CLOSE']] * day_data['close_fd']
    day_data['high_fd'] = day_data[CONV['HIGH']] / day_data[CONV['CLOSE']] * day_data['close_fd']
    day_data['low_fd'] = day_data[CONV['LOW']] / day_data[CONV['CLOSE']] * day_data['close_fd']

    day_data.iloc[0, day_data.columns.get_loc('open_fd')] = day_data.iloc[0, day_data.columns.get_loc('Open')]
    day_data.iloc[0, day_data.columns.get_loc('high_fd')] = day_data.iloc[0, day_data.columns.get_loc('High')]
    day_data.iloc[0, day_data.columns.get_loc('low_fd')] = day_data.iloc[0, day_data.columns.get_loc('Low')]

    day_data[CONV['OPEN']], day_data[CONV['HIGH']], day_data[CONV['LOW']], day_data[CONV['CLOSE']] = \
        day_data['open_fd'], day_data['high_fd'], day_data['low_fd'], day_data['close_fd']
    # 复权处理完成后再排序
    day_data.sort_index(ascending=True, inplace=True)

    return day_data

# 后复权
def day_to_hfq(day_data):

    CONV = {
        'CLOSE': 'Close',
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'PCT': 'Pctchg'

    } if 'Close' in day_data.columns else {
        'CLOSE': '收盘价',
        'OPEN': '开盘价',
        'HIGH': '最高价',
        'LOW': '最低价',
        'PCT': '涨跌幅'
    }

    # 今日收盘价 = 昨日收盘价 * (1+涨跌幅)
    day_data['bd_factor'] = (day_data[CONV['PCT']] / 100 + 1).cumprod()

    if (day_data.iloc[0][CONV["CLOSE"]] != 0) and (day_data.iloc[0]['Open'] != 0):
        initial_price = day_data.iloc[0][CONV["CLOSE"]] / (1 + day_data.iloc[0][CONV['PCT']] / 100)  # 计算上市价格
    else:
        # 前一日收盘价
        initial_price = day_data.iloc[1][CONV["CLOSE"]] / (1 + day_data.iloc[1][CONV['PCT']] / 100)  # 计算上市价格

    day_data['close_bd'] = initial_price * day_data['bd_factor']  # 相乘得到复权价
    day_data['open_bd'] = day_data[CONV["OPEN"]] / day_data[CONV["CLOSE"]] * day_data['close_bd']
    day_data['high_bd'] = day_data[CONV["HIGH"]] / day_data[CONV["CLOSE"]] * day_data['close_bd']
    day_data['low_bd'] = day_data[CONV["LOW"]] / day_data[CONV["CLOSE"]] * day_data['close_bd']
    day_data[CONV["OPEN"]], day_data[CONV["HIGH"]], day_data[CONV['LOW']], day_data[CONV['CLOSE']] = \
        day_data['open_bd'], day_data['high_bd'], day_data['low_bd'], day_data['close_bd']
    return day_data