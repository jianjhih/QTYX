#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import baostock as bs
import numpy as np
import pandas as pd
import sqlite3

def bs_k_data_stock(code_val='sz.000651', start_val='2009-01-01', end_val='2019-06-01',
                    freq_val='d', adjust_val='3'):

    # 登陆系统
    lg = bs.login()

    # 获取历史行情数据
    fields= "date,open,high,low,close,volume"

    df_bs = bs.query_history_k_data_plus(code_val, fields, start_date=start_val, end_date=end_val,
                                 frequency=freq_val, adjustflag=adjust_val) # <class 'baostock.data.resultset.ResultData'>
    # frequency="d"取日k线，adjustflag="3"默认不复权，1：后复权；2：前复权

    data_list = []

    while (df_bs.error_code == '0') & df_bs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(df_bs.get_row_data())

    result = pd.DataFrame(data_list, columns=df_bs.fields)

    result.close = result.close.astype('float64')
    result.open = result.open.astype('float64')
    result.low = result.low.astype('float64')
    result.high = result.high.astype('float64')
    result.volume = result.volume.astype('float64')
    result.volume = result.volume/100 # 单位转换：股-手
    result.date = pd.DatetimeIndex(result.date)
    result.set_index("date", drop=True, inplace=True)
    result.index = result.index.set_names('Date')

    recon_data = {'High': result.high, 'Low': result.low, 'Open': result.open, 'Close': result.close,\
                  'Volume': result.volume}
    df_recon = pd.DataFrame(recon_data)

    # 登出系统
    bs.logout()
    return df_recon

def bs_profit_data_stock(code_val='sh.600000', year_val='2017', quarter_val=2):

    # 登陆系统
    lg = bs.login()
    # 显示登陆返回信息
    print('login respond error_code:'+lg.error_code)
    print('login respond  error_msg:'+lg.error_msg)

    # 查询季频估值指标盈利能力
    profit_list = []
    rs_profit = bs.query_profit_data(code=code_val, year=year_val, quarter=quarter_val)
    while (rs_profit.error_code == '0') & rs_profit.next():
        profit_list.append(rs_profit.get_row_data())
    result_profit = pd.DataFrame(profit_list, columns=rs_profit.fields)

    # 登出系统
    bs.logout()
    return result_profit


