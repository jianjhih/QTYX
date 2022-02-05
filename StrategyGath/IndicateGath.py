#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import os
import sys
import  numpy as np
import pandas as pd

sys.path.append(os.path.abspath('..'))

# 创建本地存储路径
data_path = os.path.dirname(os.path.dirname(__file__)) + '/DataFiles/stock_history/'

# 指标类的功能
from ApiData.Tushare import basic_code_list

class Base_Indicate_Group():

    @staticmethod
    def rps_pct_rolling(filt_date=20210101):

        df_stbasic = basic_code_list(['ts_code', 'symbol', 'name', 'area', 'industry', 'list_date'])

        # 剔除出新股和次新股 即只考虑2017年1月1日以前上市的股票
        df_stbasic = df_stbasic[df_stbasic['list_date'].apply(int).values < filt_date] # 转换为int后筛选

        # 获取当前所有非新股/次新股代码和名称
        codes = df_stbasic.ts_code.values
        names = df_stbasic.name.values
        # 构建一个字典方便调用
        code_name = dict(zip(names[0:100], codes[0:100]))

        # 构建一个空的dataframe用来装数据
        data = pd.DataFrame()

        for name, code in code_name.items():

            num, sym = code.lower().split(".")
            bs_code = sym + num
            df = pd.read_csv(data_path + bs_code + '.csv', index_col=1, parse_dates=[u"日期"], encoding='GBK',
                             engine='python')  # 文件名中含有中文时使用engine为python

            df.index = df.index.strftime('%Y-%m-%d')
            # w:周5; 月20; 半年120; 一年250
            df["涨跌幅"] = df["涨跌幅"].rolling(window=120).mean().round(2)
            data[name] = df["涨跌幅"][-120:-1].fillna(0)

        data.fillna(0, inplace=True)
        return data

    @staticmethod
    def rps_top10_order(data, rank, name):

        if name == '': name="平安银行"

        RPS = {}
        for index, row in data.iterrows():
            df = pd.DataFrame(row.sort_values(ascending=False))
            df.rename(columns={row.name: "pct"}, inplace=True)  # 更改列名
            df['n'] = range(1, len(df) + 1)
            df['name'] = df.index
            df['rps'] = (1 - df['n'] / len(df)) * 100
            df.set_index("n", drop=True, inplace=True)
            RPS[index] = df

        # 构建一个以时间——收益率/RPS/股票名称的DataFrame空表
        df_new = pd.DataFrame(np.NaN, columns=['pct', 'name', 'rps'], index=data.index)
        # 按时间汇集每日排名第一的数据
        for date in df_new.index:
            rps_df = RPS[date]
            df_new.loc[date, 'pct'] = rps_df.loc[1, 'pct']
            df_new.loc[date, 'name'] = rps_df.loc[1, 'name']
            df_new.loc[date, 'rps'] = rps_df.loc[1, 'rps']

        # 构建一个以时间——RPS排名前N的股票名称DataFrame空表
        df_stock = pd.DataFrame(np.NaN, columns=range(1, rank + 1), index=data.index)

        # 构建一个以时间——个股RPS排名和收盘价的DataFrame空表
        df_track = pd.DataFrame(np.NaN, columns=['close', 'rps'], index=data.index)

        # 按时间汇集每日排名前十的数据
        for date in df_stock.index:
            rps_df = RPS[date]
            df_stock.loc[date, :] = rps_df.name[0:rank]
            df_track.loc[date, 'rps'] = rps_df[rps_df.name.values == name]['rps'].values

        columns = {}
        for num in range(rank):
            columns[num+1] = f"第{num+1}名"

        df_stock.rename(columns=columns, inplace=True)

        return df_stock, df_track

