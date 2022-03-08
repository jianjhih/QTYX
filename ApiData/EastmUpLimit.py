#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

from urllib import request
from datetime import datetime
from pathlib import Path

import pandas as pd
import random
import json
import re
import os

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# 爬虫东方财富网每日涨停数据
class ReptileUpLimit():

    store_path = os.path.dirname(os.path.dirname(__file__)) + '/DataFiles/UplimData/'

    def __init__(self):

        self.cur_time = datetime.now().strftime("%Y%m%d") # 初始化值
        self.df_up = pd.DataFrame()  # 新建一个空的DataFrame 存储处理后的每日涨停数据

    def get_header(self):

        # 构造请求头信息,随机抽取信息
        agent1 = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        agent2 = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1'
        agent3 = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'
        agent4 = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR ' \
                 '3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0) '
        agent5 = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR ' \
                 '3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) '

        agent = random.choice([agent1, agent2, agent3, agent4, agent5])  # 请求头信息

        header = {
            'User-Agent': agent,
            'Referer': 'https://www.eastmoney.com/'
        }
        return header

    def run(self, trade_date):

        self.cur_time = trade_date
        try:
            url = 'http://push2ex.eastmoney.com/getTopicZTPool?cb=callbackdata4570496&ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=1000&sort=fbt:asc&date=' + str(
                self.cur_time) + "&_=1644837745766"

            req_obj = request.Request(url, headers=self.get_header())
            resp = request.urlopen(req_obj).read().decode(encoding='utf-8')
            pattern = re.compile(r'"pool":\[(.*?)\]', re.S).findall(resp)

            st_data = pattern[0].replace("},{", "}walt{").split('walt')

            stocks = []

            for i in range(len(st_data)):
                # stock = st_data[i].replace('"',"").split(",")
                stock = json.loads(st_data[i])
                fenzi = str(stock['zttj']['ct'])
                fenmu = str(stock['zttj']['days'])
                # print(len(str(stock['fbt'])))

                stock_all = str(stock['c']) + "," + str(stock['n']) + "," + str(stock['p'] / 1000) + "," + \
                            str(round((stock['zdp']), 2)) + "," + str(round(stock['amount'] / 100000000, 2)) + "," + \
                            str(round(stock['ltsz'] / 100000000, 2)) + "," + \
                            str(str(round(stock['hs'], 2))) + "," + str(stock['lbc']) + "," + \
                            str(datetime.strptime(str(stock['fbt']), "%H%M%S"))[10:] + "," + \
                            str(datetime.strptime(str(stock['lbt']), "%H%M%S"))[10:] + "," + \
                            str(round(stock['fund'] / 100000000, 2)) + "," + str(str(stock['zbc'])) + "," + \
                            str(stock['hybk']) + "," + str(fenmu + str('天') + fenzi + str('板')) + "," + \
                            str(round(stock['fund'] / stock['amount'], 2))

                stocks.append(stock_all.split(","))

            self.df_up = pd.DataFrame(stocks, dtype=object)

            columns = {0: "股票代码", 1: "股票名称", 2: "最新价格", 3: "涨跌幅", 4: "成交额（亿）", 5: "流通市值（亿）", 6: "换手率（%）", 7: "连板天数",
                       8: "首次封板时间", 9: "最终封板时间", 10: "封板资金（亿）", 11: "炸板次数", 12: "所属行业", 13: "涨停统计", 14: '封成比'}
            self.df_up.rename(columns=columns, inplace=True)
            self.df_up = self.df_up.astype({"最新价格": 'float64', "涨跌幅": 'float64', "成交额（亿）": 'float64',
                                               "流通市值（亿）": 'float64',  "换手率（%）": 'float64',  "连板天数": 'int64',
                                               "封板资金（亿）": 'float64',  "炸板次数": 'int64', "封成比": 'float64'})

            self.df_up["股票代码"] = self.df_up["股票代码"].apply(lambda x: x + '.SH' if x[0] == '6' else x + '.SZ')

        except:
            print("获取涨停板数据出错！调整有效交易日期！")

        return self.df_up

    def save_csv(self):

        file_exist = Path(self.store_path + u"A股每日涨停明细-{0}.csv".format(self.cur_time))
        self.df_up.to_csv(file_exist, columns=self.df_up.columns, index=True, encoding='GBK')


class UpLimitBackend(ReptileUpLimit):

    def __init__(self, syslog_obj):

        ReptileUpLimit.__init__(self)

        self.tran_col = {}
        self.filter = []
        self.syslog = syslog_obj

    def datafame_join(self, date_val):

        self.syslog.re_print("开始获取A股每日涨停明细...\n")

        try:
            df_dyuplim = self.run(date_val)
            self.save_csv()
            self.syslog.re_print("爬虫A股每日涨停明细获取成功！\n")
        except:
            self.syslog.re_print("请检查爬虫接口-[ReptileUpLimit]是否正常！\n")
            df_dyuplim = pd.DataFrame()

        return df_dyuplim
