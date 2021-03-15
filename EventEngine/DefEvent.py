#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究
import datetime
import pandas as pd

from CommIf.SysFile import Base_File_Oper
from ApiData.Baostock import bs_k_data_stock
from StrategyGath.StrategyGath import Base_Strategy_Group
from ApiData.Csvdata import (
    Csv_Backend
)

class EventHandle:

    event_task = {}

    def __init__(self, *args, **kwargs):

        # ----- gui event -----

        self.event_task['get_stock_dat'] = self.get_stock_dat
        self.event_task['cfg_firm_para'] = self.cfg_firm_para
        self.event_task['cfg_back_para'] = self.cfg_back_para
        self.event_task['get_csvst_dat'] = self.get_csvst_dat

    #### 配置股票数据相关 ####
    def get_stock_dat(self, **kwargs):
        # baostock接口获取行情数据
        baost_para = {"30分钟": "30", "60分钟": "60", "日线": "d", "周线": "w",
                      "后复权": "2", "前复权": "1", "不复权": "3"}

        # 传递参数
        st_code = kwargs["st_code"]
        sdate_obj = kwargs["sdate_obj"]
        edate_obj = kwargs["edate_obj"]
        period_val = baost_para[kwargs["st_period"]]
        auth_val = baost_para[kwargs["st_auth"]]

        sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)
        edate_val = datetime.datetime(edate_obj.year, edate_obj.month + 1, edate_obj.day)

        try:
            df = bs_k_data_stock(st_code,
                                 start_val=sdate_val.strftime('%Y-%m-%d'),
                                 end_val=edate_val.strftime('%Y-%m-%d'),
                                 freq_val=period_val,
                                 adjust_val=auth_val)

            # df.to_csv("offline-2021-12-29.csv", columns=df.columns, index=True, encoding='GB18030')
        except:
            df = pd.DataFrame()
        finally:
            return df

    def get_csvst_dat(self, **kwargs):
        # csv文件获取行情数据

        # 传递参数
        get_path = kwargs["get_path"]

        try:
            df = Csv_Backend.load_stock_data(get_path)
        except:
            df = pd.DataFrame()
        finally:
            # 返回数据
            return df

    #### 配置文件获取相关 ####
    def cfg_firm_para(self, **kwargs):
        # 行情显示界面 配置文件

        # 传递参数
        st_code = kwargs["st_code"]
        st_auth = kwargs["st_auth"]
        st_period = kwargs["st_period"]

        # 加载参数
        firm_para = Base_File_Oper.load_sys_para("./ConfigFiles/firm_para.json")

        # 更新参数
        firm_para['subplots_dict']['graph_fst']['title'] = st_code + st_period + st_auth

        if "st_label" in kwargs.keys():
            # 适应于衍生技术指标的显示
            st_label = kwargs["st_label"]
            firm_para['subplots_dict']['graph_fst']['graph_type'][st_label] = 'null'

        # 返回参数
        return firm_para['subplots_dict']

    def cfg_back_para(self, **kwargs):
        # 回测显示界面 配置文件

        # 传递参数
        st_code = kwargs["st_code"]
        cash_value = kwargs["cash_value"]
        slippage_value = kwargs["slippage_value"]
        commission_value = kwargs["commission_value"]
        tax_value = kwargs["tax_value"]
        stake_value = kwargs["stake_value"]

        # 加载参数
        back_para = Base_File_Oper.load_sys_para("./ConfigFiles/back_para.json")
        # 更新回测参数
        back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['cash_hold'] = cash_value
        back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['slippage'] = slippage_value
        back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['c_rate'] = commission_value
        back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['t_rate'] = tax_value
        back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['stake_size'] = stake_value
        back_para['subplots_dict']['graph_fst']['title'] = st_code + "-回测分析"
        # 保存参数
        Base_File_Oper.save_sys_para("./ConfigFiles/back_para.json", back_para)
        # 返回参数
        return back_para['subplots_dict']

    def cfg_sub_para(self, **kwargs):

        # 传递参数
        st_code = kwargs["st_code"]
        st_auth = kwargs["st_auth"]
        st_period = kwargs["st_period"]

        sub_para = Base_File_Oper.load_sys_para("./ConfigFiles/sub_para.json")
        sub_para['subplots_dict']['graph_fst']['title'] = st_code + st_period + st_auth

        return sub_para['subplots_dict']

    def call_method( self, f, **kwargs):

        return f(**kwargs)

