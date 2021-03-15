#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import wx.adv
import wx.grid
import wx.html2
import os
import numpy as np
import tushare as ts
import pandas as pd
import mpl_finance as mpf
import matplotlib.pyplot as plt
import datetime
import time
from importlib import reload

__version__ = 'V2.0.1'
__author__ = u'元宵大师'

from MainlyGui.ElementGui.DefPanel import (
    StockPanel,
    SubGraphs,
    GroupPanel,
    Sys_Panel
)

from MainlyGui.ElementGui.DefTreelist import (
    CollegeTreeListCtrl
)

from MainlyGui.ElementGui.DefGrid import (
    GridTable
)

from MainlyGui.ElementGui.DefDialog import (
    UserDialog, MessageDiag, ImportFileDiag
)

from ApiData.Baostock import (
    bs_k_data_stock
)

from ApiData.Tushare import (
    Tspro_Backend,
    Tsorg_Backend
)

from ApiData.Csvdata import (
    Csv_Backend
)

# 分离控件事件中调用的子事件
from EventEngine.DefEvent import (
    EventHandle
)

from StrategyGath.StrategyGath import Base_Strategy_Group
from CommIf.SysFile import Base_File_Oper

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class UserFrame(wx.Frame):

    def __init__(self):

        # hack to help on dual-screen, need something better XXX - idfah
        displaySize = wx.DisplaySize()  # (1920, 1080)
        displaySize = 0.85 * displaySize[0], 0.75 * displaySize[1]

        # call base class constructor
        wx.Frame.__init__(self, parent=None, title=u'量化软件', size=displaySize,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX)  # size=(1000,600)

        # 存储策略函数
        self.function = ''

        # 组合加入tushare数据
        self.ts_data = Tspro_Backend()
        self.filter = self.ts_data.filter
        self.tran_col = self.ts_data.tran_col

        self.EventHandle = EventHandle()
        self.call_method = self.EventHandle.call_method
        self.event_task = self.EventHandle.event_task

        # 创建wxGrid表格对象
        self._init_grid_pk()

        self.vbox_sizer_a = wx.BoxSizer(wx.VERTICAL)  # 纵向box
        self.vbox_sizer_a.Add(self._init_treelist_ctrl(), proportion=2, flag=wx.EXPAND | wx.BOTTOM, border=5)  # 添加行情参数布局
        self.vbox_sizer_a.Add(self._init_grid_pl(), proportion=3, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # 加载配置文件
        firm_para = Base_File_Oper.load_sys_para("./ConfigFiles/firm_para.json")
        back_para = Base_File_Oper.load_sys_para("./ConfigFiles/back_para.json")
        # 创建显示区面板
        self.DispPanel = Sys_Panel(self, **firm_para['layout_dict']) # 自定义
        self.BackMplPanel = Sys_Panel(self, **back_para['layout_dict']) # 自定义
        self.DispPanelA = self.DispPanel

        # 第二层布局
        self.vbox_sizer_b = wx.BoxSizer(wx.VERTICAL)  # 纵向box
        self.vbox_sizer_b.Add(self._init_para_notebook(), proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=5)  # 添加行情参数布局
        self.vbox_sizer_b.Add(self.BackMplPanel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)
        self.vbox_sizer_b.Hide(self.BackMplPanel)
        self.vbox_sizer_b.Replace(self.BackMplPanel, self.DispPanel )  # 等类型可替换

        # 第一层布局
        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_a, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_b, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # 使布局有效

        self._init_status_bar()
        self._init_menu_bar()

    def _init_treelist_ctrl(self):

        # 创建一个 treeListCtrl object
        self.treeListCtrl = CollegeTreeListCtrl(parent=self, pos=(-1, 39), size=(150, 400))
        self.treeListCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self._ev_click_on_treelist)

        return self.treeListCtrl

    def _init_para_notebook(self):

        # 创建参数区面板
        self.ParaNoteb = wx.Notebook(self)
        self.ParaStPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaBtPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaPtPanel = wx.Panel(self.ParaNoteb, -1)

        # 第二层布局
        self.ParaStPanel.SetSizer(self.add_stock_para_lay(self.ParaStPanel))
        self.ParaBtPanel.SetSizer(self.add_backt_para_lay(self.ParaBtPanel))
        self.ParaPtPanel.SetSizer(self.add_pick_para_lay(self.ParaPtPanel))

        self.ParaNoteb.AddPage(self.ParaStPanel, "行情参数")
        self.ParaNoteb.AddPage(self.ParaBtPanel, "回测参数")
        self.ParaNoteb.AddPage(self.ParaPtPanel, "条件选股")
        self.ParaNoteb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self._ev_change_noteb)

        return self.ParaNoteb


    def _init_status_bar(self):

        self.statusBar = self.CreateStatusBar() # 创建状态条
        # 将状态栏分割为3个区域,比例为2:1
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusWidths([-2, -1, -1])
        t = time.localtime(time.time())
        self.SetStatusText("公众号：元宵大师带你用Python量化交易", 0)
        self.SetStatusText("当前版本：%s" % __version__, 1)
        self.SetStatusText(time.strftime("%Y-%B-%d %I:%M:%S", t), 2)

    def _init_menu_bar(self):

        # 创建窗口面板
        menuBar = wx.MenuBar(style=wx.MB_DOCKABLE)

        toolmenu = wx.Menu()
        about = wx.MenuItem(toolmenu, wx.ID_ANY, '&使用帮助')
        # self.Bind(wx.EVT_MENU, self.OnQuit, about)
        toolmenu.Append(about)
        toolmenu.AppendSeparator()
        toolmenu.Append(wx.ID_ANY, '&基金持仓') # 预留链接至星球工具
        toolmenu.AppendSeparator()
        toolmenu.Append(wx.ID_ANY, '&离线数据') # 预留链接至星球工具
        toolmenu.AppendSeparator()
        toolmenu.Append(wx.ID_ANY, '&实时数据') # 预留链接至星球工具
        toolmenu.AppendSeparator()
        toolmenu.Append(wx.ID_ANY, '&板块数据') # 预留链接至星球工具
        toolmenu.AppendSeparator()
        toolmenu.Append(wx.ID_ANY, '&事件型回测') # 预留链接至星球工具
        menuBar.Append(toolmenu, '&星球量化工具')

        self.SetMenuBar(menuBar)

    def switch_main_panel(self, org_panel=None, new_panel=None, inplace=True):

        if id(org_panel) != id(new_panel):

            self.vbox_sizer_b.Hide(org_panel)

            if inplace == True:
                self.vbox_sizer_b.Replace(org_panel, new_panel) # 等类型可替换
            else:
                # 先删除后添加
                self.vbox_sizer_b.Detach(org_panel)
                self.vbox_sizer_b.Add(new_panel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)

            self.vbox_sizer_b.Show(new_panel)
            self.SetSizer(self.HBoxPanelSizer)
            self.HBoxPanelSizer.Layout()

    def _ev_change_noteb(self, event):
        #print(self.ParaNoteb.GetSelection())

        old = event.GetOldSelection()
        new = event.GetSelection()
        ex_flag = True

        if old == 0:
            if self.pick_graph_last != 0:
                org_panel = self.FlexGridSizer
                ex_flag = False
            else:
                org_panel = self.DispPanel

        elif old == 1:
            org_panel = self.BackMplPanel
        elif old == 2:
            org_panel = self.grid_pk
        else:
            raise ValueError(u"切换面板号出错！")

        self.vbox_sizer_b.Hide(org_panel)

        if new == 0:
            if self.pick_graph_last != 0:
                new_panel = self.FlexGridSizer
                ex_flag = False
            else:
                new_panel = self.DispPanel

        elif new == 1:
            new_panel = self.BackMplPanel
        elif new == 2:
            new_panel = self.grid_pk
        else:
            raise ValueError(u"切换面板号出错！")

        self.switch_main_panel(org_panel, new_panel, ex_flag)

    def add_stock_para_lay(self, sub_panel):

        # 行情参数
        stock_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 行情参数——日历控件时间周期
        self.dpc_end_time = wx.adv.DatePickerCtrl(sub_panel, -1,
                                                  style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#结束时间
        self.dpc_start_time = wx.adv.DatePickerCtrl(self.ParaStPanel, -1,
                                                    style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#起始时间

        self.start_date_box = wx.StaticBox(sub_panel, -1, u'开始日期(Start)')
        self.end_date_box = wx.StaticBox(sub_panel, -1, u'结束日期(End)')
        self.start_date_sizer = wx.StaticBoxSizer(self.start_date_box, wx.VERTICAL)
        self.end_date_sizer = wx.StaticBoxSizer(self.end_date_box, wx.VERTICAL)
        self.start_date_sizer.Add(self.dpc_start_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.end_date_sizer.Add(self.dpc_end_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.dpc_end_time.SetValue(date_time_now)
        self.dpc_start_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

        # 行情参数——输入股票代码
        self.stock_code_box = wx.StaticBox(sub_panel, -1, u'股票代码')
        self.stock_code_sizer = wx.StaticBoxSizer(self.stock_code_box, wx.VERTICAL)
        self.stock_code_input = wx.TextCtrl(sub_panel, -1, "sz.000876", style=wx.TE_PROCESS_ENTER)
        self.stock_code_sizer.Add(self.stock_code_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.stock_code_input.Bind(wx.EVT_TEXT_ENTER, self._ev_enter_stcode)

        # 行情参数——股票周期选择
        self.stock_period_box = wx.StaticBox(sub_panel, -1, u'股票周期')
        self.stock_period_sizer = wx.StaticBoxSizer(self.stock_period_box, wx.VERTICAL)
        self.stock_period_cbox = wx.ComboBox(sub_panel, -1, u"", choices=[u"30分钟", u"60分钟", u"日线", u"周线"])
        self.stock_period_cbox.SetSelection(2)
        self.stock_period_sizer.Add(self.stock_period_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 行情参数——股票复权选择
        self.stock_authority_box = wx.StaticBox(sub_panel, -1, u'股票复权')
        self.stock_authority_sizer = wx.StaticBoxSizer(self.stock_authority_box, wx.VERTICAL)
        self.stock_authority_cbox = wx.ComboBox(sub_panel, -1, u"", choices=[u"前复权", u"后复权", u"不复权"])
        self.stock_authority_cbox.SetSelection(2)
        self.stock_authority_sizer.Add(self.stock_authority_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 行情参数——多子图显示
        self.pick_graph_box = wx.StaticBox(sub_panel, -1, u'多子图显示')
        self.pick_graph_sizer = wx.StaticBoxSizer(self.pick_graph_box, wx.VERTICAL)
        self.pick_graph_cbox = wx.ComboBox(sub_panel, -1, u"未开启", choices=[u"未开启", u"A股票走势", u"B股票走势", u"C股票走势", u"D股票走势"],
                                           style=wx.CB_READONLY | wx.CB_DROPDOWN)
        self.pick_graph_cbox.SetSelection(0)
        self.pick_graph_last = self.pick_graph_cbox.GetSelection()
        self.pick_graph_sizer.Add(self.pick_graph_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_graph_cbox.Bind(wx.EVT_COMBOBOX, self._ev_select_graph)

        # 导入数据按钮
        self.import_dat_but = wx.Button(sub_panel, -1, "导入数据")
        self.import_dat_but.Bind(wx.EVT_BUTTON, self._ev_import_dat) # 绑定按钮事件

        stock_para_sizer.Add(self.start_date_sizer, proportion=0, flag=wx.EXPAND | wx.CENTER | wx.ALL, border=10)
        stock_para_sizer.Add(self.end_date_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_code_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_period_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_authority_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.pick_graph_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.import_dat_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)

        return stock_para_sizer

    def add_backt_para_lay(self, sub_panel):

        # 回测参数
        back_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.init_cash_box = wx.StaticBox(sub_panel, -1, u'初始资金')
        self.init_cash_sizer = wx.StaticBoxSizer(self.init_cash_box, wx.VERTICAL)
        self.init_cash_input = wx.TextCtrl(sub_panel, -1, "100000", style=wx.TE_LEFT)
        self.init_cash_sizer.Add(self.init_cash_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_stake_box = wx.StaticBox(sub_panel, -1, u'交易规模')
        self.init_stake_sizer = wx.StaticBoxSizer(self.init_stake_box, wx.VERTICAL)
        self.init_stake_input = wx.TextCtrl(sub_panel, -1, "all", style=wx.TE_LEFT)
        self.init_stake_sizer.Add(self.init_stake_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_slippage_box = wx.StaticBox(sub_panel, -1, u'滑点')
        self.init_slippage_sizer = wx.StaticBoxSizer(self.init_slippage_box, wx.VERTICAL)
        self.init_slippage_input = wx.TextCtrl(sub_panel, -1, "0.01", style=wx.TE_LEFT)
        self.init_slippage_sizer.Add(self.init_slippage_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_commission_box = wx.StaticBox(sub_panel, -1, u'手续费')
        self.init_commission_sizer = wx.StaticBoxSizer(self.init_commission_box, wx.VERTICAL)
        self.init_commission_input = wx.TextCtrl(sub_panel, -1, "0.0005", style=wx.TE_LEFT)
        self.init_commission_sizer.Add(self.init_commission_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_tax_box = wx.StaticBox(sub_panel, -1, u'印花税')
        self.init_tax_sizer = wx.StaticBoxSizer(self.init_tax_box, wx.VERTICAL)
        self.init_tax_input = wx.TextCtrl(sub_panel, -1, "0.001", style=wx.TE_LEFT)
        self.init_tax_sizer.Add(self.init_tax_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 回测按钮
        self.start_back_but = wx.Button(sub_panel, -1, "开始回测")
        self.start_back_but.Bind(wx.EVT_BUTTON, self._ev_start_run)  # 绑定按钮事件

        # 交易日志
        self.trade_log_but = wx.Button(sub_panel, -1, "交易日志")
        self.trade_log_but.Bind(wx.EVT_BUTTON, self._ev_trade_log)  # 绑定按钮事件

        back_para_sizer.Add(self.init_cash_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_stake_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_slippage_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_commission_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_tax_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.start_back_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.trade_log_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        return back_para_sizer

    def add_pick_para_lay(self, sub_panel):

        # 选股参数
        pick_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 选股参数——日历控件时间周期
        self.dpc_cur_time = wx.adv.DatePickerCtrl(sub_panel, -1,
                                                  style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE)  # 当前时间

        self.cur_date_box = wx.StaticBox(sub_panel, -1, u'当前日期(Start)')
        self.cur_date_sizer = wx.StaticBoxSizer(self.cur_date_box, wx.VERTICAL)
        self.cur_date_sizer.Add(self.dpc_cur_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.dpc_cur_time.SetValue(date_time_now)
        # self.dpc_cur_time.SetValue(date_time_now.SetDay(9)) # 以9日为例 先不考虑周末的干扰

        # 选股参数——条件表达式分析
        self.pick_stock_box = wx.StaticBox(sub_panel, -1, u'条件表达式选股')
        self.pick_stock_sizer = wx.StaticBoxSizer(self.pick_stock_box, wx.HORIZONTAL)

        self.pick_item_cmbo = wx.ComboBox(sub_panel, -1,  choices=[],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股项

        self.pick_cond_cmbo = wx.ComboBox(sub_panel, -1, u"大于",
                                          choices=[u"大于", u"等于", u"小于"],
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股条件
        self.pick_value_text = wx.TextCtrl(sub_panel, -1, "0", style=wx.TE_LEFT)

        self.sort_values_cmbo = wx.ComboBox(sub_panel, -1, u"不排列",
                                            choices=[u"不排列", u"升序", u"降序"],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 排列条件

        self.pick_stock_sizer.Add(self.pick_item_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_cond_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_value_text, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.sort_values_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 子参数——标记自选股
        self.mark_self_box = wx.StaticBox(sub_panel, -1, u'是否标记自选股')
        self.mark_self_box_sizer = wx.StaticBoxSizer(self.mark_self_box, wx.VERTICAL)
        self.mark_self_box_chk = wx.CheckBox(sub_panel, label='标记')
        self.mark_self_box_chk.Bind(wx.EVT_CHECKBOX, self._ev_mark_self)  # 绑定复选框事件
        self.mark_self_box_sizer.Add(self.mark_self_box_chk, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        radioList = ["ts pro接口","离线csv文件"]
        self.src_dat_radio = wx.RadioBox(sub_panel, -1, label=u'数据源选取', choices=radioList,
                                         majorDimension = 2, style = wx.RA_SPECIFY_ROWS)
        self.src_dat_radio.Bind(wx.EVT_RADIOBUTTON, self._ev_src_choose)

        # 选股按钮
        self.start_pick_but = wx.Button(sub_panel, -1, "开始选股")
        self.start_pick_but.Bind(wx.EVT_BUTTON, self._ev_start_select)  # 绑定按钮事件

        # 复位按钮
        self.start_reset_but = wx.Button(sub_panel, -1, "复位条件")
        self.start_reset_but.Bind(wx.EVT_BUTTON, self._ev_start_reset)  # 绑定按钮事件

        # 保存按钮
        self.start_save_but = wx.Button(sub_panel, -1, "保存结果")
        self.start_save_but.Bind(wx.EVT_BUTTON, self._ev_start_save)  # 绑定按钮事件

        pick_para_sizer.Add(self.cur_date_sizer, proportion=0, flag=wx.EXPAND | wx.CENTER | wx.ALL, border=10)
        pick_para_sizer.Add(self.pick_stock_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER,
                             border=10)
        pick_para_sizer.Add(self.mark_self_box_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER,
                             border=10)
        pick_para_sizer.Add(self.src_dat_radio, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        pick_para_sizer.Add(self.start_pick_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        pick_para_sizer.Add(self.start_reset_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        pick_para_sizer.Add(self.start_save_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)

        return pick_para_sizer

    def _init_grid_pk(self):
        # 初始化选股表格
        self.grid_pk = GridTable(parent=self)
        self.df_use = pd.DataFrame()
        self.filte_result = pd.DataFrame()
        return self.grid_pk

    def _init_grid_pl(self):
        # 初始化股票池表格
        dict_basic = Base_File_Oper.load_sys_para("./ConfigFiles/stock_self_pool.json")
        self.grid_pl = GridTable(parent=self, nrow=0, ncol=2)
        self.grid_pl.SetTable(dict_basic, ["自选股", "代码"])
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self._ev_click_stcode, self.grid_pl)
        return self.grid_pl

    def refresh_grid(self, df, back_col=""):
        self.grid_pk.SetTable(df, self.tran_col)
        self.grid_pk.SetSelectCol(back_col)

    def _ev_select_graph(self, event):

        item = event.GetSelection()

        if item != 0 and self.pick_graph_last == 0:
            #self.pick_graph_last = item
            self.graphs_obj = SubGraphs(self)

            self.FlexGridSizer = self.graphs_obj.FlexGridSizer
            self.DispPanel0 = self.graphs_obj.DispPanel0
            self.DispPanel1 = self.graphs_obj.DispPanel1
            self.DispPanel2 = self.graphs_obj.DispPanel2
            self.DispPanel3 = self.graphs_obj.DispPanel3
            self.switch_main_panel(self.DispPanel, self.FlexGridSizer, False)

        elif item == 0 and self.pick_graph_last != 0:
            #print(self.vbox_sizer_b.GetItem(self.DispPanel))
            self.switch_main_panel(self.FlexGridSizer, self.DispPanel, False)

        if item == 1:
            self.DispPanelA = self.DispPanel0
            self.ochl = self.DispPanel0.ochl
            self.vol = self.DispPanel0.vol
        elif item == 2:
            self.DispPanelA = self.DispPanel1
            self.ochl = self.DispPanel1.ochl
            self.vol = self.DispPanel1.vol
        elif item == 3:
            self.DispPanelA = self.DispPanel2
            self.ochl = self.DispPanel2.ochl
            self.vol = self.DispPanel2.vol
        elif item == 4:
            self.DispPanelA = self.DispPanel3
            self.ochl = self.DispPanel3.ochl
            self.vol = self.DispPanel3.vol
        else:
            self.DispPanelA = self.DispPanel

        self.pick_graph_last = item

    def _ev_start_select(self, event):

        if self.df_use.empty != True:
            for key, val in self.tran_col.items():
                if val == self.pick_item_cmbo.GetStringSelection():

                    para_value = float(self.pick_value_text.GetValue())

                    if self.pick_cond_cmbo.GetStringSelection() == u"大于":
                        self.filte_result = self.df_use[self.df_use[key] > para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"小于":
                        self.filte_result = self.df_use[self.df_use[key] < para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"等于":
                        self.filte_result = self.df_use[self.df_use[key] == para_value]
                    else:
                        pass

                    if self.sort_values_cmbo.GetStringSelection() == u"降序":
                        self.filte_result.sort_values(by=key, axis='index', ascending=False, inplace=True,
                                                      na_position='last')
                    elif self.sort_values_cmbo.GetStringSelection() == u"升序":
                        self.filte_result.sort_values(by=key, axis='index', ascending=True, inplace=True,
                                                      na_position='last')
                    else:
                        pass
                    self.df_use = self.filte_result
                    self.refresh_grid(self.filte_result, key)
                    break

    def _ev_start_reset(self, event): # 复位选股按钮事件

        if self.src_dat_radio.GetStringSelection() == "ts pro接口":
            # 组合加入tushare数据
            self.ts_data = Tspro_Backend()
            self.filter = self.ts_data.filter
            self.tran_col = self.ts_data.tran_col

            self.pick_item_cmbo.Clear()
            self.pick_item_cmbo.Append(self.filter)
            self.pick_item_cmbo.SetValue(self.filter[0])

            sdate_obj = self.dpc_cur_time.GetValue()
            sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)

            self.df_join = self.ts_data.datafame_join(sdate_val.strftime('%Y%m%d'))  # 刷新self.df_join

            if self.df_join.empty == True:
                MessageDiag("该日无数据")
            else:
                self.df_use = self.df_join
                self.refresh_grid(self.df_use, self.df_use.columns.tolist()[0])

        elif self.src_dat_radio.GetStringSelection() == "离线csv文件":

            # 第一步:收集导入文件路径
            get_path = ImportFileDiag()

            # 组合加入tushare数据
            self.ts_data = Csv_Backend()
            self.filter = self.ts_data.filter
            self.tran_col = self.ts_data.tran_col

            self.pick_item_cmbo.Clear()
            self.pick_item_cmbo.Append(self.filter)
            self.pick_item_cmbo.SetValue(self.filter[0])
            self.df_join = self.ts_data.load_pick_data(get_path)
            print(self.df_join)

            if self.df_join.empty == True:
                MessageDiag("文件内容为空！\n")
            else:
                self.df_use = self.df_join
                self.refresh_grid(self.df_use, self.df_use.columns.tolist()[0])

        else:
            MessageDiag("无效数据源！")

    def _ev_mark_self(self, event):
        # 标记自选股事件

        if self.df_use.empty == True:
            MessageDiag("无选股数据！")
        else:
            self.df_use.reset_index(drop=True, inplace=True) # 重排索引

            # 加载自选股
            dict_basic = Base_File_Oper.load_sys_para("./ConfigFiles/stock_self_pool.json")

            if self.mark_self_box_chk.GetValue() == True: # 复选框被选中

                for code in list(dict_basic['股票'].values()):
                    symbol, number = code.upper().split('.')
                    new_code = number + "." + symbol
                    n_list = self.df_use[self.df_use.ts_code == new_code].index.tolist()
                    if n_list != []:
                        self.grid_pk.SetCellBackgroundColour(n_list[0], 0, wx.YELLOW)
                        self.grid_pk.SetCellBackgroundColour(n_list[0], 1, wx.YELLOW)
            else:
                for code in list(dict_basic['股票'].values()):
                    symbol, number = code.upper().split('.')
                    new_code = number + "." + symbol
                    n_list = self.df_use[self.df_use.ts_code == new_code].index.tolist()
                    if n_list != []:
                        self.grid_pk.SetCellBackgroundColour(n_list[0], 0, wx.WHITE)
                        self.grid_pk.SetCellBackgroundColour(n_list[0], 1, wx.WHITE)
            self.grid_pk.Refresh()

    def _ev_start_save(self, event):
        # 保存选股按钮事件
        codes = self.df_use.ts_code.values
        names = self.df_use.name.values
        st_name_code_dict = dict(zip(names, codes))

        for k, v in st_name_code_dict.items():
            code_split = v.lower().split(".")
            st_name_code_dict[k] = code_split[1] + "." + code_split[0] # tushare转baostock

        dict_basic = Base_File_Oper.load_sys_para("./ConfigFiles/stock_self_pool.json")
        dict_basic['股票'].clear()
        dict_basic['股票'].update(st_name_code_dict)
        Base_File_Oper.save_sys_para("./ConfigFiles/stock_self_pool.json", dict_basic)
        self.grid_pl.SetTable(dict_basic, ["自选股", "代码"])
        #self.df_use.to_csv('table-stock.csv', columns=self.df_use.columns, index=True, encoding='GB18030')

    def _ev_trade_log(self, event):

        user_trade_log = UserDialog(self, title=u"回测提示信息", label=u"交易详细日志")

        """ 自定义提示框 """
        if user_trade_log.ShowModal() == wx.ID_OK:
            pass
        else:
            pass

    def _ev_click_on_treelist(self, event):

        self.curTreeItem = self.treeListCtrl.GetItemText(event.GetItem())

        if self.curTreeItem != None:
            # 当前选中的TreeItemId对象操作

            MessageDiag('当前点击:{0}!'.format(self.curTreeItem))
            for m_key, m_val in self.treeListCtrl.colleges.items():
                for s_key in m_val:
                    if s_key.get('名称', '') == self.curTreeItem:
                        if s_key.get('函数', '') != "未定义":
                            if (m_key == u"衍生指标") or (m_key == u"K线形态"):
                                # 第一步:收集控件中设置的选项
                                st_label = s_key['标识']
                                st_code = self.stock_code_input.GetValue()
                                st_period = self.stock_period_cbox.GetStringSelection()
                                st_auth = self.stock_authority_cbox.GetStringSelection()
                                sdate_obj = self.dpc_start_time.GetValue()
                                edate_obj = self.dpc_end_time.GetValue()

                                # 第二步:获取股票数据-调用sub event handle
                                stock_dat = self.call_method(self.event_task['get_stock_dat'],
                                                             st_code=st_code,
                                                             st_period=st_period,
                                                             st_auth=st_auth,
                                                             sdate_obj=sdate_obj,
                                                             edate_obj=edate_obj)

                                if stock_dat.empty == True:
                                    MessageDiag("获取股票数据出错！\n")
                                else:
                                    # 第三步:绘制可视化图形
                                    if self.pick_graph_cbox.GetSelection() != 0:
                                        self.DispPanelA.clear_subgraph()  # 必须清理图形才能显示下一幅图
                                        self.DispPanelA.draw_subgraph(stock_dat, st_code, st_period + st_auth)
                                    else:
                                        # 配置图表属性
                                        firm_para = self.call_method(self.event_task['cfg_firm_para'],
                                                                     st_code=st_code,
                                                                     st_period=st_period,
                                                                     st_auth=st_auth,
                                                                     st_label=st_label)

                                        self.DispPanelA.firm_graph_run(stock_dat, **firm_para)

                                    self.DispPanelA.update_subgraph()  # 必须刷新才能显示下一幅图
                            else:
                                self.function = getattr(Base_Strategy_Group, s_key.get('define', ''))
                        else:
                            MessageDiag("该接口未定义！")
                        break

    def _ev_start_run(self, event): # 点击运行回测

        # 第一步:收集控件中设置的选项
        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()
        sdate_obj = self.dpc_start_time.GetValue()
        edate_obj = self.dpc_end_time.GetValue()
        st_code = self.stock_code_input.GetValue()

        cash_value = self.init_cash_input.GetValue()
        stake_value = self.init_stake_input.GetValue()
        slippage_value = self.init_slippage_input.GetValue()
        commission_value = self.init_commission_input.GetValue()
        tax_value = self.init_tax_input.GetValue()

        # 第二步:获取股票数据-调用sub event handle
        stock_dat = self.call_method(self.event_task['get_stock_dat'],
                                     st_code=st_code,
                                     st_period=st_period,
                                     st_auth=st_auth,
                                     sdate_obj=sdate_obj,
                                     edate_obj=edate_obj)

        # 第三步:绘制可视化图形
        # 配置图表属性
        back_para = self.call_method(self.event_task['cfg_back_para'],
                                     st_code=st_code,
                                     cash_value=cash_value,
                                     stake_value=stake_value,
                                     slippage_value=slippage_value,
                                     commission_value=commission_value,
                                     tax_value=tax_value)

        if self.function == '':
            MessageDiag("未选择回测策略！")
        else:
            self.BackMplPanel.back_graph_run(self.function(stock_dat), **back_para)
            # 修改图形的任何属性后都必须更新GUI界面
            self.BackMplPanel.update_subgraph()

    def _ev_enter_stcode(self, event):  # 输入股票代码

        # 第一步:收集控件中设置的选项
        st_code = self.stock_code_input.GetValue()
        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()
        sdate_obj = self.dpc_start_time.GetValue()
        edate_obj = self.dpc_end_time.GetValue()

        # 第二步:获取股票数据-调用sub event handle
        stock_dat = self.call_method(self.event_task['get_stock_dat'],
                                     st_code=st_code,
                                     st_period=st_period,
                                     st_auth=st_auth,
                                     sdate_obj=sdate_obj,
                                     edate_obj=edate_obj)

        if stock_dat.empty == True:
            MessageDiag("获取股票数据出错！\n")
        else:
            # 第三步:绘制可视化图形
            if self.pick_graph_cbox.GetSelection() != 0:
                self.DispPanelA.clear_subgraph()  # 必须清理图形才能显示下一幅图
                self.DispPanelA.draw_subgraph(stock_dat, st_code, st_period + st_auth)

            else:
                # 配置图表属性
                firm_para = self.call_method(self.event_task['cfg_firm_para'],
                                             st_code=st_code,
                                             st_period=st_period,
                                             st_auth=st_auth)

                self.DispPanelA.firm_graph_run(stock_dat, **firm_para)

            self.DispPanelA.update_subgraph()  # 必须刷新才能显示下一幅图

    def _ev_click_stcode(self, event):  # 点击股票代码

        # 第一步:收集控件中设置的选项
        st_code = self.grid_pl.GetCellValue(event.GetRow(), 1)
        st_name = self.grid_pl.GetCellValue(event.GetRow(), 0)
        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()
        sdate_obj = self.dpc_start_time.GetValue()
        edate_obj = self.dpc_end_time.GetValue()

        # 第二步:获取股票数据-调用sub event handle
        stock_dat = self.call_method(self.event_task['get_stock_dat'],
                                     st_code=st_code,
                                     st_period=st_period,
                                     st_auth=st_auth,
                                     sdate_obj=sdate_obj,
                                     edate_obj=edate_obj)

        if stock_dat.empty == True:
            MessageDiag("获取股票数据出错！\n")
        else:
            # 第三步:绘制可视化图形
            if self.pick_graph_cbox.GetSelection() != 0:
                self.DispPanelA.clear_subgraph()  # 必须清理图形才能显示下一幅图
                self.DispPanelA.draw_subgraph(stock_dat, st_code, st_period + st_auth)

            else:
                # 配置图表属性
                firm_para = self.call_method(self.event_task['cfg_firm_para'],
                                             st_code=st_code,
                                             st_period=st_period,
                                             st_auth=st_auth)

                self.DispPanelA.firm_graph_run(stock_dat, **firm_para)

            self.DispPanelA.update_subgraph()  # 必须刷新才能显示下一幅图

    def _ev_import_dat(self, event): # 点击导入股票数据

        # 第一步:收集导入文件路径
        get_path = ImportFileDiag()

        # 第二步:加载csv文件中的数据
        stock_dat = self.call_method(self.event_task['get_csvst_dat'],
                                        get_path=get_path)

        if stock_dat.empty == True:
            MessageDiag("文件内容为空！\n")
        else:
            # 第三步:绘制可视化图形
            if self.pick_graph_cbox.GetSelection() != 0:
                self.DispPanelA.clear_subgraph()  # 必须清理图形才能显示下一幅图
                self.DispPanelA.draw_subgraph(stock_dat, "csv导入", "离线股票数据")
            else:
                # 配置图表属性
                firm_para = self.call_method(self.event_task['cfg_firm_para'],
                                             st_code="csv导入离线股票数据",
                                             st_period="",
                                             st_auth="")
                self.DispPanelA.firm_graph_run(stock_dat, **firm_para)
            self.DispPanelA.update_subgraph()  # 必须刷新才能显示下一幅图

    def _ev_src_choose(self, event):
        # 预留
        pass