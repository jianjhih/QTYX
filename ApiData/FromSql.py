#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import os
import time
import sys
import json
import sqlite3
import pandas as pd

from datetime import datetime

#参数设置
pd.set_option('display.expand_frame_repr',False) # False不允许换行
pd.set_option('display.max_rows', 20) # 显示的最大行数
pd.set_option('display.max_columns', 18) # 显示的最大列数
pd.set_option('precision', 2) # 显示小数点后的位数

# 从数据库中获取基金持仓数据
def ReadFundDatFromSql(syslog):

    # 创建数据库存储路径
    store_path = os.path.dirname(os.path.dirname(__file__)) + \
        "/DataFiles/FundData/"

    quarters = {"1":"3/31", "2":"6/30", "3":"9/30", "4":"12/31"}

    conn = sqlite3.connect(store_path+'fund_data_quarter.db') # 如果db不存在会自动创建

    syslog.re_print("连接基金持仓数据库成功...\n")

    cur_month = datetime.now().month
    cur_year = datetime.now().year
    cur_quarter = (cur_month - 1) // 3 + 1

    if cur_quarter == 1:
        pre_fst_year = cur_year - 1
        pre_fst_quarter = 4
    else:
        pre_fst_year = cur_year
        pre_fst_quarter = cur_quarter - 1

    if pre_fst_quarter == 1:
        pre_sec_year = pre_fst_year - 1
        pre_sec_quarter = 4
    else:
        pre_sec_year = pre_fst_year
        pre_sec_quarter = pre_fst_quarter - 1

    pre_fst_issue_date = str(pre_fst_year) + '/' + quarters[str(pre_fst_quarter)]
    pre_sec_issue_date = str(pre_sec_year) + '/' + quarters[str(pre_sec_quarter)]

    try:
        sql_sen = 'select * from "hold_position_top_ten" where 发布日 == '+'\"'+pre_fst_issue_date+'\"'
        df_target_pre_fst = pd.read_sql_query(sql_sen, conn)

        sql_sen = 'select * from "hold_position_top_ten" where 发布日 == '+'\"'+pre_sec_issue_date+'\"'
        df_target_pre_sec = pd.read_sql_query(sql_sen, conn)

    except:
        df_target_cur = pd.DataFrame()  # 如果表不存在，则先用写入方式自动创建表
        df_target_pre = pd.DataFrame()  # 如果表不存在，则先用写入方式自动创建表


    df_analy_cont = pd.concat([df_target_pre_fst["第一名"].append([df_target_pre_fst["第二名"], \
                                                                df_target_pre_fst["第三名"], \
                                                                df_target_pre_fst["第四名"], \
                                                                df_target_pre_fst["第五名"], \
                                                                df_target_pre_fst["第六名"], \
                                                                df_target_pre_fst["第七名"], \
                                                                df_target_pre_fst["第八名"], \
                                                                df_target_pre_fst["第九名"], \
                                                                df_target_pre_fst["第十名"]]).value_counts(),
                               df_target_pre_sec["第一名"].append([df_target_pre_sec["第二名"], \
                                                                df_target_pre_sec["第三名"], \
                                                                df_target_pre_sec["第四名"], \
                                                                df_target_pre_sec["第五名"], \
                                                                df_target_pre_sec["第六名"], \
                                                                df_target_pre_sec["第七名"], \
                                                                df_target_pre_sec["第八名"], \
                                                                df_target_pre_sec["第九名"], \
                                                                df_target_pre_sec["第十名"]]).value_counts()],
                                                  join='outer', axis=1, sort=False)

    df_analy_cont.fillna(0, inplace = True)
    df_analy_cont.columns = ["基金家数","上期基金家数"]
    df_analy_cont = df_analy_cont.applymap(lambda x:int(x))

    df_analy_cont["与上期相比(家)"] = df_analy_cont["基金家数"] - df_analy_cont["上期基金家数"]
    df_analy_cont["与上期相比(%)"] = round((df_analy_cont["基金家数"] - df_analy_cont["上期基金家数"])/\
                                                df_analy_cont["上期基金家数"]*100, 1)

    df_analy_cont.insert(0, u"股票名称", df_analy_cont.index)

    df_analy_cont = df_analy_cont[df_analy_cont["股票名称"].str.len() <= 4]

    conn.close()

    return df_analy_cont
