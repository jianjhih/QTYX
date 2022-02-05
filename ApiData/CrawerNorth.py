#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import json
import requests
import re
import time
import numpy as np
import pandas as pd
from pathlib import Path
from requests.adapters import HTTPAdapter
from datetime import datetime
import os

# 爬虫东方财富网北上资金数据
class CrawerNorthData():

    # 单独调试 使用u"../DataFiles/NorthData/"
    store_path = os.path.dirname(os.path.dirname(__file__)) + '/DataFiles/NorthData/'

    def __init__(self):

        self.cur_time = datetime.now().strftime("%Y%m%d")
        self.df_total = pd.DataFrame()  # 新建一个空的DataFrame 存储处理后的北上资金数据
        self.df_new = pd.DataFrame()  # 新建一个空的DataFrame 存储处理前的北上资金数据

    def get_header(self):

        # 模拟请求headers
        s = requests.Session()
        s.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40'
        }
        s.mount('http://', HTTPAdapter(max_retries=3)) # 添加http适配器
        s.mount('https://', HTTPAdapter(max_retries=3)) # 添加https适配器
        return s

    def run(self):

        s = self.get_header()
        # 获取token 3a965a43f705cf1d9ad7e1a3e429d622
        tokenurl = s.get('http://data.eastmoney.com/')
        # 从返回的html code中获取token值
        s1 = re.search("token=.*?\"", tokenurl.text, flags=0)
        token = s1.group(0).replace("token=", "").replace("\"", "")

        # 发送请求获取数据
        lst = []
        page = 0
        data = ['1']
        while data:
            page += 1
            url = 'http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get?type=HSGT20_GGTJ_SUM&token='+ \
                  token + \
                  '&st=ShareSZ&sr=-1&ps=500&p='+\
                  str(page)

            req = s.get(url, timeout=5)
            data = req.json()
            lst = lst + data

        # 备份源数据，更新加入新数据
        self.df_new = pd.DataFrame(lst)

        # 重定义列名
        df_ren = self.df_new.rename({
            'DateType': 'N日数据',
            'HdDate': '数据日期',
            'SCode': '股票代码',
            'SName': '股票名称',
            'HYName': '所属行业板块',
            'HYCode': '行业板块代码',
            'DQName': '所属地区板块',
            'DQCode': '地区板块代码',
            'NewPrice': '当日收盘价(元)',
            'Zdf': '当日涨跌幅(%)',
            'Market': '沪市/深市(1or3)',
            'ShareHold': '当日持股数(股)',
            'ShareSZ': '当日持股市值(元)',
            'ZZB': '当日持股总占比',
            'LTSZ': '当日流通市值(元)',
            'ZSZ': '当日总市值(元)',
            'ShareHold_Chg_One': '当期增持股数(股)',
            'ShareSZ_Chg_One': '当期增持市值(元)',
            'ShareSZ_Chg_Rate_One': '当期市值增减幅',
            'LTZB_One': '当期流通股占比变动',
            'ZZB_One': '当期总占比变动',
        }, axis='columns')

        scode = "00000" + df_ren['股票代码'].astype(str)
        df_ren['股票代码'] = "'" + scode.str[-6:] + "'"

        # 取需要的列
        self.df_total = df_ren[['数据日期',
                 'N日数据',
                 '股票代码',
                 '股票名称',
                 '所属行业板块',
                 '所属地区板块',
                 '当日收盘价(元)',
                 '当日涨跌幅(%)',
                 '当日持股数(股)',
                 '当日持股市值(元)',
                 '当日持股总占比',
                 '当日流通市值(元)',
                 '当日总市值(元)',
                 '当期增持股数(股)',
                 '当期增持市值(元)',
                 '当期市值增减幅',
                 '当期流通股占比变动',
                 '当期总占比变动']]

        return self.df_total

    def save_csv(self):

        file_exist = Path(self.store_path + u"北向资金数据{0}.csv".format(self.cur_time))

        if file_exist.is_file() == False:
            self.df_total.to_csv(self.store_path + u"北向资金数据{0}.csv".format(self.cur_time), columns=self.df_total.columns, index=True, encoding='utf-8-sig')

        file_exist = Path(self.store_path + u"北向资金数据备份{0}.csv".format(self.cur_time))

        if file_exist.is_file() == False:
            self.df_new = self.df_new.reset_index(drop=True)
            self.df_new.to_csv(self.store_path + u"北向资金数据备份{0}.csv".format(self.cur_time), columns=self.df_new.columns, index=True, encoding='utf-8-sig')

class CrawerNorthBackend(CrawerNorthData):

    def __init__(self, syslog_obj):

        CrawerNorthData.__init__(self)

        self.tran_col = {}
        self.filter = []
        self.syslog = syslog_obj

    def datafame_join(self, date_val):

        file_exist = Path(self.store_path + u"北向资金数据{0}.csv".format(date_val))

        if file_exist.is_file() == False:

            self.syslog.re_print("开始获取爬虫北上资金数据...\n")

            try:
                df_dynorth = self.run()
            except:
                self.syslog.re_print("请检查爬虫接口-[CrawerNorthData]是否正常！\n")
                df_dynorth = pd.DataFrame()

            self.save_csv()

        else:
            self.syslog.re_print("历史数据已经存在该日北上资金数据...\n")
            try:
                df_dynorth = pd.read_csv(self.store_path + u"北向资金数据{0}.csv".format(date_val), parse_dates=True, index_col=0, encoding='utf-8-sig')
            except:
                self.syslog.re_print("请检查历史数据中该文件是否正常！\n")
                df_dynorth = pd.DataFrame()

        if df_dynorth.empty != True:

            self.syslog.re_print("爬虫北上资金数据获取成功！\n")
            df_dynorth['股票代码'] = df_dynorth['股票代码'].apply(lambda x: x.replace("'", ""))

            return df_dynorth
        else:
            return pd.DataFrame()


if __name__ == '__main__':

    for_test = CrawerNorthData()

    for_test.run()
    for_test.save_csv()
