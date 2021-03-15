#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import wx.adv
import wx.grid
import wx.html2
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg  as NavigationToolbar
import matplotlib.gridspec as gridspec # 分割子图

import tushare as ts
import pandas as pd
import mpl_finance as mpf
import matplotlib.pyplot as plt
import datetime
import wx.gizmos

from MultiGraphs.SystemApply import Sys_MultiGraph

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class StockPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=-1)

        # 分割子图实现代码
        self.figure = Figure(figsize=(8, 4))
        gs = gridspec.GridSpec(2, 1, left=0.1, bottom=0.15, right=0.95, top=0.90, wspace=None, hspace=0.1,
                               height_ratios=[3.5, 1])
        self.ochl = self.figure.add_subplot(gs[0, :])
        self.vol = self.figure.add_subplot(gs[1, :])

        self.FigureCanvas = FigureCanvas(self, -1, self.figure)  # figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas, proportion=10, border=2, flag=wx.ALL | wx.EXPAND)

        self.SetSizer(self.TopBoxSizer)

    def clear_subgraph(self):
        # 再次画图前,必须调用该命令清空原来的图形
        self.ochl.clear()
        self.vol.clear()

    def update_subgraph(self):
        self.FigureCanvas.draw()

    def draw_subgraph(self, stockdat, st_name, st_kylabel):
        # 绘制多子图页面
        num_bars = np.arange(0, len(stockdat.index))

        # 绘制K线
        ohlc = list(zip(num_bars, stockdat.Open, stockdat.Close, stockdat.High, stockdat.Low))
        mpf.candlestick_ochl(self.ochl, ohlc, width=0.5, colorup='r', colordown='g')  # 绘制K线走势

        # 绘制成交量
        self.vol.bar(num_bars, stockdat.Volume, color=['g' if stockdat.Open[x] > stockdat.Close[x] else 'r' for x in
                                                    range(0, len(stockdat.index))])

        self.ochl.set_ylabel(st_kylabel)
        self.vol.set_ylabel(u"成交量")
        self.ochl.set_title(st_name + " 行情走势图")

        major_tick = len(num_bars)
        self.ochl.set_xlim(0, major_tick)  # 设置一下x轴的范围
        self.vol.set_xlim(0, major_tick)  # 设置一下x轴的范围

        self.ochl.set_xticks(range(0, major_tick, 15))  # 每五天标一个日期
        self.vol.set_xticks(range(0, major_tick, 15))  # 每五天标一个日期
        self.vol.set_xticklabels(
            [stockdat.index.strftime('%Y%m%d')[index] for index in self.vol.get_xticks()])  # 标签设置为日期

        for label in self.ochl.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
            label.set_visible(False)
        for label in self.vol.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
            label.set_rotation(45)  # X-轴每个ticker标签都向右倾斜45度
            label.set_fontsize(10)  # 设置标签字体

        self.ochl.grid(True, color='k')
        self.vol.grid(True, color='k')



class SubGraphs(wx.Panel):
    def __init__(self, parent):

        # 创建FlexGridSizer布局网格 vgap定义垂直方向上行间距/hgap定义水平方向上列间距
        self.FlexGridSizer = wx.FlexGridSizer(rows=2, cols=2, vgap=1, hgap=1)
        self.DispPanel0 = StockPanel(parent)  # 自定义
        self.DispPanel1 = StockPanel(parent)  # 自定义
        self.DispPanel2 = StockPanel(parent)  # 自定义
        self.DispPanel3 = StockPanel(parent)  # 自定义

        # 加入Sizer中
        self.FlexGridSizer.Add(self.DispPanel0, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel1, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel2, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel3, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.SetFlexibleDirection(wx.BOTH)

class GroupPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=-1)

        # 分割子图实现代码
        self.figure = Figure(figsize=(8, 8))

        self.relate = self.figure.add_subplot(1, 1, 1)

        self.FigureCanvas = FigureCanvas(self, -1, self.figure)  # figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas, proportion=10, border=2, flag=wx.ALL | wx.EXPAND)

        self.SetSizer(self.TopBoxSizer)

class Sys_Panel(Sys_MultiGraph, wx.Panel):
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent=parent, id=-1)
        Sys_MultiGraph.__init__(self, **kwargs)

        self.FigureCanvas = FigureCanvas(self, -1, self.fig) # figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas,proportion = -1, border = 2,flag = wx.ALL | wx.EXPAND)
        self.SetSizer(self.TopBoxSizer)

    def update_subgraph(self):
        self.FigureCanvas.draw()