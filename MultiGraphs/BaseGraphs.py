#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import numpy as np
import mpl_finance as mpf

from CommIf.DefPool import DefTypesPool

class MplTypesDraw():

    mpl = DefTypesPool()

    # 参考<8.1.3 可视化图表类型实现>
    @mpl.route_types(u"line")
    def line_plot(df_index, df_dat, graph):
        # 绘制line图
        for key, val in df_dat.items():
            graph.plot(np.arange(0, len(val)), val, label=key, lw=1.0)

    # 参考<8.1.3 可视化图表类型实现>
    @mpl.route_types(u"ochl")
    def ochl_plot(df_index, df_dat, graph):
        # 绘制ochl图——Kline
        # 方案一
        mpf.candlestick2_ochl(graph, df_dat['Open'], df_dat['Close'], df_dat['High'], df_dat['Low'], width=0.5,
                              colorup='r', colordown='g') # 绘制K线走势
        # 方案二
        ohlc = list(zip(np.arange(0,len(df_index)),df_dat['Open'], df_dat['Close'], df_dat['High'], df_dat['Low'])) # 使用zip方法生成数据列表
        mpf.candlestick_ochl(graph, ohlc, width=0.2, colorup='r', colordown='g', alpha=1.0) # 绘制K线走势

    # 参考<8.1.3 可视化图表类型实现>
    @mpl.route_types(u"bar")
    def bar_plot(df_index, df_dat, graph):
        # 绘制bar图——Volume
        #graph.bar(np.arange(0, len(df_index)), df_dat['Volume'], \
        #         color=['g' if df_dat['Open'][x] > df_dat['Close'][x] else 'r' for x in range(0,len(df_index))])

        graph.bar(np.arange(0, len(df_index)), df_dat['bar_red'], facecolor='red')
        graph.bar(np.arange(0, len(df_index)), df_dat['bar_green'], facecolor='green')

    # 参考<8.1.3 可视化图表类型实现>
    @mpl.route_types(u"hline")
    def hline_plot(df_index, df_dat, graph):
        # 绘制hline图
        for key, val in df_dat.items():
            graph.axhline(val['pos'], c=val['c'], label=key)

    # 参考<8.1.3 可视化图表类型实现 - 示例 8.4>
    @mpl.route_types(u"annotate")
    def annotate_plot(df_index, df_dat, graph):
        # 绘制annotate图
        for key, val in df_dat.items():
            for kl_index, today in val['andata'].iterrows():
                x_posit = df_index.get_loc(kl_index)
                graph.annotate(u"{}\n{}".format(key, today.name.strftime("%m.%d")),
                                   xy=(x_posit, today[val['xy_y']]),
                                   xycoords='data',
                                   xytext=(val['xytext'][0], val['xytext'][1]),
                                   va=val['va'],  # 点在标注下方
                                   textcoords='offset points',
                                   fontsize=val['fontsize'],
                                   arrowprops=val['arrow'])

    @mpl.route_types(u"filltrade")
    def filltrade_plot(df_index, df_dat, graph):
        # 绘制filltrade图
        signal_shift = df_dat['signal'].shift(1)
        signal_shift.fillna(value=-1, inplace=True)  # 序列最前面的NaN值用-1填充
        list_signal = np.sign(df_dat['signal'] - signal_shift)
        bs_singal = list_signal[list_signal != 0]

        skip_days = False
        for kl_index, value in bs_singal.iteritems(): # iteritems以迭代器形式返回
            if (value == 1) and (skip_days == False) :
                start = df_index.get_loc(kl_index)
                skip_days = True
            elif (value == -1) and (skip_days == True) :
                end = df_index.get_loc(kl_index) + 1  # 加1用于匹配[start:end]选取到end值
                skip_days = False

                if df_dat['jdval'][end-1] < df_dat['jdval'][start]: # 赔钱显示绿色
                    graph.fill_between(np.arange(start, end), 0, df_dat['jdval'][start:end], color='green', alpha=0.38)
                    is_win = False
                else:  # 赚钱显示红色
                    graph.fill_between(np.arange(start, end), 0, df_dat['jdval'][start:end], color='red', alpha=0.38)
                    is_win = True
                graph.annotate('获利\n' if is_win else '亏损\n',
                             xy=(end, df_dat['jdval'].asof(kl_index)),
                             xytext=(df_dat['xytext'][0], df_dat['xytext'][1]),
                             xycoords='data',
                             va=df_dat['va'], # 点在标注下方
                             textcoords='offset points',
                             fontsize=df_dat['fontsize'],
                             arrowprops=df_dat['arrow'])
        # 整个时间序列填充为底色blue 透明度alpha小于后标注区间颜色
        graph.fill_between(np.arange(0, len(df_index)), 0, df_dat['jdval'], color='blue', alpha=.08)



