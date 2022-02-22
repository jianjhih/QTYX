#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import threading
import queue
import time
import wx

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mplfinance as mpf  # 替换 import mpl_finance as mpf

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

from MainlyGui.ElementGui.DefPanel import BasePanel

# 正常显示画图时出现的中文和负号
from pylab import mpl
mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus'] = False

class AnimationDialog(wx.Dialog):

    bars_range = 100 # 显示100个bars

    def __init__(self, parent, title=u"K线自动播放", update_df=[], size=(850, 800)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        self.SetBackgroundColour(wx.Colour('#EBEDEB'))

        self.disp_panel = BasePanel(self) # 自定义
        self.figure = self.disp_panel.figure
        self.ochl = self.disp_panel.ochl
        self.vol = self.disp_panel.vol

        self.start_btn = wx.Button(self, wx.ID_EXECUTE, u"开始")
        self.start_btn.Bind(wx.EVT_BUTTON, self.ev_start_move)  # 绑定按钮事件
        self.pause_btn = wx.Button(self, wx.ID_EXECUTE, u"暂停")
        self.pause_btn.Bind(wx.EVT_BUTTON, self.ev_pause_move)  # 绑定按钮事件
        self.stop_btn = wx.Button(self, wx.ID_EXECUTE, u"停止")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.ev_stop_move)  # 绑定按钮事件

        self.cancel_btn = wx.Button(self, wx.ID_OK, u"取消")

        self.btns_Sizer = wx.FlexGridSizer(rows=1, cols=4, vgap=2, hgap=2)
        self.btns_Sizer.Add(self.start_btn, flag=wx.ALIGN_CENTER)
        self.btns_Sizer.Add(self.pause_btn, flag=wx.ALIGN_CENTER)
        self.btns_Sizer.Add(self.stop_btn, flag=wx.ALIGN_CENTER)
        self.btns_Sizer.Add(self.cancel_btn, flag=wx.ALIGN_CENTER)

        self.vbox_sizer = wx.BoxSizer(wx.VERTICAL)
        self.vbox_sizer.Add(self.disp_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox_sizer.Add(self.btns_Sizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.vbox_sizer)
        self.Layout()
        #self.vbox_sizer.Fit(self)

        self.line, = self.ochl.plot([], [], '-', color='#239B3F', lw=1)

        self.st_dat = update_df

        self.animQueue = queue.Queue()

        # matplotlib.animation实现动画
        self.ani = animation.FuncAnimation(self.figure,
                                           self.animate,
                                           interval=1000,
                                           blit=False,
                                           init_func=self.init)

        # ani.save('jieky_animation.gif',writer='imagemagick')

        # 线程加载数据
        self.kill_flag = False

        # 动态数据通过队列和异步线程放入queue
        self.thread1 = threading.Thread(target=self.put_data_thread, args=(self.animQueue,))  # 添加线程
        self.thread1.start()
        self.Show()


    def ev_start_move(self, event):
        self.ani.event_source.start()
        self.pause_flag = False

    def ev_pause_move(self, event):
        self.ani.event_source.stop() # 动画停止
        self.pause_flag = True

    def ev_stop_move(self, event):
        self.ani.event_source.stop() # 动画停止
        self.kill_flag = True

    def put_data_thread(self, dummy):

        while True:
            for bar in self.st_dat.itertuples():
                time.sleep(0.5)
                while self.pause_flag == True: # 暂停
                    time.sleep(0.5)
                self.animQueue.put(bar)

                if self.kill_flag == True:
                    break
            break
        print("finish thread!")


    def init(self):

        # 常量
        self.initCount = 0
        self.pause_flag = True # 初始化时先暂停动画

        self.thisx = []
        self.thisy = []
        self.thisIndex = []
        self.thisOCHLV = pd.DataFrame()

        self.thisx = [i for i in range(0, self.bars_range+1)]
        self.thisy = (np.zeros(101, dtype=int) - 1).tolist()
        self.thisIndex = [id for id, _ in self.st_dat[0:self.bars_range+1].iterrows()]
        self.line.set_data([], [])
        # 设置x轴的范围
        self.ochl.set_xlim(min(self.thisx), max(self.thisx))
        # 更新刻度，刻度只要早x轴的范围内就可以
        self.ochl.set_xticks([i for i in range(min(self.thisx), max(self.thisx) + 1, 20)])
        # 设置刻度标签
        self.ochl.set_xticklabels(
            [i if i >= 0 else '' for i in range(min(self.thisx), max(self.thisx) + 1, 20)],
            rotation=0)
        return self.line

    def animate(self, *args):

        try:
            while not self.animQueue.empty():

                if self.pause_flag == True:
                    break

                bar = self.animQueue.get() # animation中取动态数据后, 重画图像。

                df_bar = pd.DataFrame({'Close': bar.Close, 'Open': bar.Open,
                              'High': bar.High,
                              'Low': bar.Low,
                              'Volume': bar.Volume}, index = [bar.Index])

                self.thisOCHLV = self.thisOCHLV.append(df_bar)

                # 清空重新绘制
                if bar.Close == -1:
                    self.initCount = 0
                    self.init()
                    continue
                else:
                    if self.initCount > self.bars_range:
                        del self.thisx[0]
                        del self.thisy[0]
                        self.thisx.append(max(self.thisx) + 1)
                        self.thisIndex.append(bar.Index)
                        self.thisy.append(bar.Close)
                    else:
                        self.thisx[self.initCount] = self.initCount
                        self.thisIndex.append(bar.Index)
                        self.thisy[self.initCount] = bar.Close
                        self.initCount += 1
        except:
            self.stop_anim()
            return

        if self.initCount > 0:

            self.ochl.set_xlim(min(self.thisx), max(self.thisx)) # 设置x轴的范围
            self.ochl.set_xticks([i for i in range(min(self.thisx), max(self.thisx) + 1, 20)]) # 更新x轴刻度

            self.vol.set_xlim(min(self.thisx), max(self.thisx)) # 设置x轴的范围
            self.vol.set_xticks([i for i in range(min(self.thisx), max(self.thisx) + 1, 20)]) # 更新x轴刻度

            self.vol.set_xticklabels(
                [self.thisIndex[i].strftime('%Y-%m-%d %H:%M') for i in range(min(self.thisx),
                                                    max(self.thisx) + 1, 20)], rotation=0) # 设置刻度标签

            for label in self.ochl.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
                label.set_visible(False)
            for label in self.vol.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
                label.set_rotation(15)  # X-轴每个ticker标签都向右倾斜15度
                label.set_fontsize(10)  # 设置标签字体

            # 重新渲染子图
            try:
                self.ochl.figure.canvas.draw()
            except:
                self.stop_anim()
                return

            # 绘制K线
            def_color = mpf.make_marketcolors(up='red', down='green', edge='black', wick='black')
            def_style = mpf.make_mpf_style(marketcolors=def_color, gridaxis='both', gridstyle='-.', y_on_right=False)
            mpf.plot(self.thisOCHLV, type='candle', style=def_style, ax=self.ochl)

            self.vol.bar(np.arange(0, len(self.thisOCHLV.index)), self.thisOCHLV.Volume,
                         color=['g' if self.thisOCHLV.Open[x] > self.thisOCHLV.Close[x]
                                else 'r' for x in range(0, len(self.thisOCHLV.index))])

            self.line.set_data(self.thisx, self.thisy)

        return self.line

