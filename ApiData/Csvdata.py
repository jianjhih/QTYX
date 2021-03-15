#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import pandas as pd

class Csv_Backend():

    tran_col = {"ts_code": u"股票代码", "close": u"当日收盘价",
                    # "turnover_rate": u"换手率%",
                    "turnover_rate_f": u"换手率%",  # 自由流通股
                    "volume_ratio": u"量比", "pe": u"市盈率(总市值/净利润)",
                    "pe_ttm": u"市盈率TTM",
                    "pb": u"市净率(总市值/净资产)",
                    "ps": u"市销率", "ps_ttm": u"市销率TTM",
                    "dv_ratio": u"股息率%",
                    "dv_ttm": u"股息率TTM%",
                    "total_share": u"总股本(万股)",
                    "float_share": u"流通股本(万股)",
                    "free_share": u"自由流通股本(万股)",
                    "total_mv": u"总市值(万元)",
                    "circ_mv": u"流通市值(万元)",
                    "name": u"股票名称",
                    "area": u"所在地域",
                    "list_date": u"上市日期",
                    "industry": u"所属行业"}

    filter = [u"换手率%", u"量比", u"市盈率(总市值/净利润)", u"市盈率TTM",
                  u"市净率(总市值/净资产)", u"市销率", u"市销率TTM", u"股息率%",
                  u"股息率TTM%", u"总股本(万股)", u"流通股本(万股)", u"自由流通股本(万股)",
                  u"总市值(万元)", u"流通市值(万元)"]

    @staticmethod
    def load_pick_data(path):

        return pd.read_csv(path, parse_dates=True, index_col=0, encoding='gbk', engine='python')

    @staticmethod
    def load_stock_data(path):

        return pd.read_csv(path, parse_dates=True, index_col=0, encoding='gbk', engine='python')
