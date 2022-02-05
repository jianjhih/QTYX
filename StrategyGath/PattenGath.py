#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import time
import numpy as np
import pandas as pd

class Base_Patten_Group():

    @staticmethod
    def double_bottom_search(name, code, stock_data, patlog_obj, **kwargs):
        # stock_data的数据格式 索引为'%Y-%m-%d'格式
        DOUBOT_DETECT_DATES_RANGE = kwargs["选取K线范围"]  # 往前寻找的范围 默认40
        DOUBOT_DETECT_DATES_MID = int(kwargs["选取K线范围"]/2)  # 区间划分中间点 默认40/2
        DOUBOT_DETECT_DATES_VAR = kwargs["选取中间区域误差"]  # 可变区间 默认 5

        DOUBOT_MIN_DIFF_FACTOR = kwargs["双底低点之间误差"]/100  # 最小值误差 默认0.03
        DOUBOT_BREAK_PCTCHG_VAR = kwargs["有效突破当天涨跌幅"]/100    # 有效突破当天涨跌幅 默认0.03
        DOUBOT_BREAK_RATIO_FACTOR = kwargs["有效突破颈线幅度"]/100  # 有效突破颈线幅度 默认 0.03
        DOUBOT_BREAK_VOLUME_THR = kwargs["有效突破成交量阈值"]/100  # 放量突破比例 默认超过平均的20%

        df_result = pd.DataFrame(index=[0], columns=["股票名称", "股票代码",
                                                     "形态识别", "左底id", "左底价格", "右底id", "右底价格", "中顶id", "中顶价格",
                                                     "收盘价格", "颈线价格","首次突破",
                                                     "突破幅度", "当日涨幅",
                                                     "突破放量", "当前成交量-手", "平均成交量-手"])

        try:

            # K线区间划分成两个子区间
            data_range1 = stock_data[
                          -DOUBOT_DETECT_DATES_RANGE: -(DOUBOT_DETECT_DATES_MID - DOUBOT_DETECT_DATES_VAR)]
            data_range2 = stock_data[-(DOUBOT_DETECT_DATES_MID + DOUBOT_DETECT_DATES_VAR):]

            # 计算K线区间成交量平均值(手)
            range_mean_vol_val = stock_data[-DOUBOT_DETECT_DATES_RANGE:-1]["Volume"].mean()

            # 分别计算子区间内收盘价最小值及出现日期
            range1_min_close_val = data_range1["Close"].min()
            range2_min_close_val = data_range2["Close"].min()

            range1_min_close_df = data_range1.loc[data_range1["Close"] == range1_min_close_val]
            range2_min_close_df = data_range2.loc[data_range2["Close"] == range2_min_close_val]

            range1_min_close_id = range1_min_close_df.index[0]
            range2_min_close_id = range2_min_close_df.index[0]

            # 分别计算子区间最小值之间的最大值及出现日期
            data_range_between = stock_data.loc[range1_min_close_id:range2_min_close_id]
            between_max_close_val = data_range_between["Close"].max()

            between_max_close_df = data_range_between.loc[data_range_between["Close"] == between_max_close_val]
            between_max_close_id = between_max_close_df.index[0]

            # 选取双底两个低点中的较小值并计算两个低点的误差比例
            relative_min = range2_min_close_val if range1_min_close_val >= range2_min_close_val else range1_min_close_val
            error_ratio = np.abs(range1_min_close_val - range2_min_close_val) / relative_min

            patlog_obj.re_print("\n----------------------分割线----------------------")

            # 判断
            if (error_ratio <= DOUBOT_MIN_DIFF_FACTOR) and (range1_min_close_id != range2_min_close_id):

                patlog_obj.re_print("[形态有效]: 股票{}, 代码{} 分析结果如下：".format(name, code))
                patlog_obj.re_print("  双底形态判断有效：左底 {}/{}元; 右底 {}/{}元; 中顶 {}/{}元;".format
                      (range1_min_close_id, range1_min_close_val, range2_min_close_id, range2_min_close_val,
                       between_max_close_id, between_max_close_val))

                df_result.loc[0, "形态识别"] = True
                df_result.loc[0, "股票名称"] = name
                df_result.loc[0, "股票代码"] = code
                df_result.loc[0, "左底id"] = range1_min_close_id
                df_result.loc[0, "左底价格"] = range1_min_close_val
                df_result.loc[0, "右底id"] = range2_min_close_id
                df_result.loc[0, "右底价格"] = range2_min_close_val
                df_result.loc[0, "中顶id"] = between_max_close_id
                df_result.loc[0, "中顶价格"] = between_max_close_val

                # 选取当前交易日的收盘价和成交量
                current_time_val = stock_data.index[-1]
                current_close_val = stock_data["Close"][-1]
                current_volume_val = stock_data["Volume"][-1]
                current_pctchg_val = round(stock_data["pctChg"][-1], 4)

                # 计算有效突破颈线的价格, 包含了有效突破幅度值
                effective_break_value = between_max_close_val * (1 + DOUBOT_BREAK_RATIO_FACTOR)

                # 选取第二个最低点到当前日期大于有效突破值的天数
                from_min2_to_cur = stock_data.loc[range2_min_close_id:current_time_val]
                effective_break_df = from_min2_to_cur.loc[from_min2_to_cur["Close"] > effective_break_value]

                if current_close_val > effective_break_value:
                    patlog_obj.re_print("  双底形态突破幅度有效：当前收盘价 {}元; 颈线价格 {}元; ".format
                          (current_close_val, between_max_close_val))

                    df_result.loc[0, "突破幅度"] = True
                    df_result.loc[0, "收盘价格"] = current_close_val
                    df_result.loc[0, "颈线价格"] = between_max_close_val

                    if len(effective_break_df) == 1:
                        patlog_obj.re_print("  当日为首次突破！！！")

                        df_result.loc[0, "首次突破"] = True

                        if current_pctchg_val >= DOUBOT_BREAK_PCTCHG_VAR:
                            patlog_obj.re_print("  双底形态突破涨幅有效：当前涨幅 {}%; \n".format(current_pctchg_val))

                            df_result.loc[0, "涨幅有效"] = True
                            df_result.loc[0, "当日涨幅"] = current_pctchg_val

                            if (current_volume_val-range_mean_vol_val)/range_mean_vol_val >= DOUBOT_BREAK_VOLUME_THR: # 成交量放量突破判断
                                patlog_obj.re_print("  双底形态突破放量有效：当前成交量 {}手; 平均成交量 {}手; ".format
                                                    (current_volume_val, range_mean_vol_val))
                                df_result.loc[0, "突破放量"] = True
                                df_result.loc[0, "当前成交量-手"] = current_volume_val
                                df_result.loc[0, "平均成交量-手"] = range_mean_vol_val
                            else:
                                patlog_obj.re_print("  未形成有效突破放量！")
                                df_result.loc[0, "突破放量"] = False
                    else:
                        patlog_obj.re_print("  非首次突破日！\n")
                        df_result.loc[0, "首日突破"] = False
                else:
                    patlog_obj.re_print("  未形成有效突破幅度！")
                    df_result.loc[0, "突破幅度"] = False

            else:
                patlog_obj.re_print("形态无效: 滤除股票 {},代码 {}".format(name, code))
                df_result = pd.DataFrame()

        except:
            patlog_obj.re_print("股票 {},代码 {} 形态识别异常！".format(name, code))
            df_result = pd.DataFrame()

        return df_result