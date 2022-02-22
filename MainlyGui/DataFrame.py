#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import os
import threading
import queue
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt

from io import StringIO

from datetime import datetime

import wx
import wx.gizmos
import wx.grid

from ApiData.Tushare import basic_code_list
from ApiData.Csvdata import Csv_Backend
from MainlyGui.ElementGui.DefDialog import MessageDialog, ViewGripDiag, ProgressDialog, DouBottomDialog, RpsTop10Dialog
from StrategyGath.PattenGath import Base_Patten_Group
from StrategyGath.IndicateGath import Base_Indicate_Group
from CommIf.PrintLog import PatLogIf
from CommIf.SysFile import Base_File_Oper
from CommIf.RemoteInfo import auto_send_email

q_codes = queue.Queue(5000)
q_results = queue.Queue(5000)

def get_content_from_internet(url, max_try_num = 10, sleep_time = 5):
	"""
	从网页爬取数据
	@param:url
	@param:max_try_num
	@param:sleep_time
	@return:返回爬取的网页内容
	"""
	is_success = False
	for i in range(max_try_num):
		try:
			content = requests.get(url, timeout = 30)
			content.encoding = 'GBK'
			is_success = True
			break
		except Exception as e:
			print('第{}次下载数据报错,请检查'.format(i+1))
			time.sleep(sleep_time)

	if is_success:
		return content.text.strip()

def save_df_to_csv(df, path, max_try_num = 5, sleep_time = 5):
    """
    保存df到csv文件
    :param:df
    :param:path
    :param:max_try_num
    :return:
    """
    is_success = False
    for i in range(max_try_num):
        try:
            df.to_csv(path, encoding = 'GBK')
            is_success = True
            break
        except Exception as e:
            print('第{}次保存csv文件报错,请检查'.format(i+1))
            time.sleep(sleep_time)
    return is_success

def init_down_path(data_path):
    # 数据保存路径
    if not os.path.exists(data_path):
        os.mkdir(data_path) # 创建目录
    # 已下载历史行情的股票
    down_stock_list = []
    for _root, _dirs, _files in os.walk(data_path):
        down_stock_list = [f.rstrip('.csv') for f in _files if f.endswith('.csv')]
    return down_stock_list

# 创建本地存储路径
data_path = os.path.dirname(os.path.dirname(__file__)) + '/DataFiles/stock_history/'

# 创建已下载股票清单
down_stock_list = init_down_path(data_path) # global

def save_to_csv(df, path, sleep_time = 5):
    """
    保存df到csv文件
    :param:df
    :param:path
    :param:max_try_num
    :return:
    """
    is_success = False

    try:
        df.to_csv(path, encoding = 'GBK')
        is_success = True
    except Exception as e:
        print('保存csv文件报错!')
        time.sleep(sleep_time)
    return is_success

def download_stock_hist_from_netease(stock, start = '19900101', end = datetime.now().strftime('%Y%m%d')):
    """
    根据股票代码，从网易财经下载股票历史行情数据
    :param stock: 单支股票的代码 sz000001
    :param start: 历史行情数据开始时间，默认'19900101'
    :param end: 历史行情数据结束时间，默认当天
    :return df: 历史行情DataFrame
    """
    stock_type = stock[0:2]
    stock_symbol = stock[2:8]

    code = '0' + stock_symbol if stock_type == 'sh' else '1' + stock_symbol
    url = 'http://quotes.money.163.com/service/chddata.html?code={0}&start={1}&end={2}&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'.format(code, start, end)
    content = get_content_from_internet(url)
    content = StringIO(content)
    df = pd.read_csv(content, parse_dates = ["日期"], na_values = 'None')
    df['股票代码'] = df['股票代码'].str.lstrip("'")
    df['股票代码'] = stock_type.lower() + df['股票代码']
    df.sort_values(by = ['日期'], ascending = True, inplace = True)
    df.reset_index(drop = True, inplace = True)
    return df

def get_stock_data(stcok_code):
    """
    获取历史行情数据
    :param stock: 单支股票的代码 sz000001
    :return:
    """
    res_info = {}
    res_info["code"] = stcok_code
    # 如果已下载该股票历史行情数据，即csv文件存在，则更新数据
    if stcok_code in down_stock_list:

        try:
            df = pd.read_csv(data_path + stcok_code + '.csv', index_col=0, parse_dates=[u"日期"], encoding='GBK',
                             engine='python') # 文件名中含有中文时使用engine为python

            # 已经有数据，更新到今日
            if len(df):
                df.sort_values(by=['日期'], ascending=True, inplace=True)
                df.reset_index(drop=True, inplace=True)
                recent_date = df.iloc[-1]['日期']
                start = recent_date.strftime('%Y%m%d')
                end = datetime.now().strftime('%Y%m%d')
                # 至少更新最后一根K线，因为程序是在当天收盘前运行，最后一根K线的数据不完整
                if start <= end:
                    try:
                        df_new = download_stock_hist_from_netease(stcok_code, start, end)
                        df = df.append(df_new, ignore_index=True)
                        df.drop_duplicates(subset=['日期'], keep='last', inplace=True)
                        is_saved = save_to_csv(df, data_path + stcok_code + '.csv')
                        if is_saved:
                            #print('{0}更新了{1}条数据'.format(stcok_code, df_new.shape[0]))
                            res_info["status"] = "Success"
                            res_info["number"] = df_new.shape[0]
                    except:
                        print(u"反扒出现:{}".format(stcok_code))
                        res_info["status"] = "Fail"
                        res_info["number"] = "None"
                else:
                    print('{0}数据已最新，无需更新'.format(stcok_code))
                    res_info["status"] = "Success"
                    res_info["number"] = 0

            else: # 有文件没数据，下载全部数据
                df = download_stock_hist_from_netease(stcok_code)
                is_saved = save_to_csv(df, data_path + stcok_code + '.csv')
                if is_saved:
                    #print('{0}更新了{1}条数据'.format(stcok_code, df.shape[0]))
                    res_info["status"] = "Success"
                    res_info["number"] = df.shape[0]

        except Exception as e:
            print('读取csv文件报错！跳过股票{0}:{1}'.format(stcok_code, e))
            res_info["status"] = "Fail"
            res_info["number"] = "None"
    # 如果未下载该股票历史行情数据，即csv文件不存在，下载截止今日的历史数据
    else:

        try:
            df = download_stock_hist_from_netease(stcok_code)
            is_saved = save_to_csv(df, data_path + stcok_code + '.csv')
            if is_saved:
                #print('{0}更新了{1}条数据'.format(stcok_code, df.shape[0]))
                res_info["status"] = "Success"
                res_info["number"] = df.shape[0]
        except:
            print(u"反扒出现:{}".format(stcok_code))
            res_info["status"] = "Fail"
            res_info["number"] = "None"
    return res_info

class ProgressBarThread(threading.Thread):
    """ 进度条类 """

    def __init__(self, parent):
        """
        :param parent:  主线程UI
        :param timer:  计时器
        """
        super(ProgressBarThread, self).__init__()  # 继承
        self.parent = parent
        self.setDaemon(True)  # 设置为守护线程， 即子线程是守护进程，主线程结束子线程也随之结束。

    def run(self):

        q_size = q_codes.qsize()  # 返回队列的大小

        while q_size != 0:
            q_size = q_codes.qsize()
            time.sleep(0.5)
            wx.CallAfter(self.parent.update_process_bar, q_size)  # 更新进度条进度
        wx.CallAfter(self.parent.close_process_bar)  # destroy进度条

class CrawlerThread(threading.Thread):
    """爬虫类"""
    def __init__(self, parent):

        super(CrawlerThread, self).__init__()
        self.parent = parent
        self.setDaemon(True)

    def run(self):
        while not q_codes.empty():
            code = q_codes.get()
            results = get_stock_data(code)
            if q_results.full() != True:
                q_results.put(results)

class CollegeTreeListCtrl(wx.gizmos.TreeListCtrl):

    def __init__(self, parent=None, id=-1, pos=(0, 0), size=wx.DefaultSize,
                 style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT):

        wx.gizmos.TreeListCtrl.__init__(self, parent, id, pos, size, style)

        self.root = None
        self.InitUI()

    def InitUI(self):
        self.il = wx.ImageList(16, 16, True)
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16)))
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        self.SetImageList(self.il)
        self.AddColumn(u'文件名称')
        self.AddColumn(u'股票名称')
        self.SetColumnWidth(0, 150)
        self.SetColumnWidth(1, 100)

    def refDataShow(self, newDatas):

        if down_stock_list != None:
            self.root = self.AddRoot(data_path)
            self.SetItemText(self.root, data_path, 0)
            self.SetItemText(self.root, u" (共" + str(len(down_stock_list)) + u"个)", 1) # 第1列上添加

            for cityID in down_stock_list: # 将本地csv文件填充整个树

                child = self.AppendItem(self.root, cityID)
                self.SetItemText(child, cityID+".csv", 0)
                self.SetItemText(child, newDatas.get(cityID[2:8]+"."+cityID[0:2].upper(), ''), 1)
                self.SetItemImage(child, 0, which=wx.TreeItemIcon_Normal) # wx.TreeItemIcon_Expanded
                self.Expand(self.root)

class DataFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, displaySize=(1600, 900), Fun_SwFrame=None):

        wx.Frame.__init__(self, parent, title="股票历史数据下载工具", size=displaySize, style=wx.DEFAULT_FRAME_STYLE)

        # 用于量化工具集成到整体系统中
        self.fun_swframe = Fun_SwFrame

        ################################### 变量初始化 ###################################

        # 获取股票代码
        df_basic = basic_code_list(['ts_code', 'name'])
        self.stock_list_all = df_basic.ts_code.values

        self.stock_tree_info = dict(zip(df_basic.ts_code.values, df_basic.name.values))
        self.total_len = len(self.stock_list_all)

        self.failed_list = [] # 更新失败列表

        self.start_time = time.perf_counter()
        self.elapsed_time = time.perf_counter()
        self.dialog = None

        ################################### 第一层布局 Left ###################################

        # 创建并初始化策略树
        self.init_tree()

        # 下载按钮
        self.start_but = wx.Button(self, -1, "开始下载")
        self.start_but.Bind(wx.EVT_BUTTON, self.on_click_start)  # 绑定按钮事件

        # 刷新按钮
        self.fresh_but = wx.Button(self, -1, "刷新文件")
        self.fresh_but.Bind(wx.EVT_BUTTON, self.on_click_fresh) # 绑定按钮事件

        # 补全按钮
        self.compt_but = wx.Button(self, -1, "补全下载")
        self.compt_but.Bind(wx.EVT_BUTTON, self.on_click_compt) # 绑定按钮事件

        self.btnSizer = wx.FlexGridSizer(rows=1, cols=3, vgap=2, hgap=3)
        self.btnSizer.Add(self.start_but, flag=wx.ALIGN_CENTER)
        self.btnSizer.Add(self.fresh_but, flag=wx.ALIGN_CENTER)
        self.btnSizer.Add(self.compt_but, flag=wx.ALIGN_CENTER)

        ################################### 第一层布局 right ###################################

        self.ParaPanel = wx.Panel(self, -1)
        self.ParaPanel.SetSizer(self.add_patten_para_lay(self.ParaPanel)) # 形态选股 patten

        vboxnetB = wx.BoxSizer(wx.VERTICAL) # 纵向box
        vboxnetB.Add(self.ParaPanel, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=2)  # proportion参数控制容器尺寸比例
        vboxnetB.Add(self._init_patten_log(), proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=2)  # proportion参数控制容器尺寸比例

        ################################### 第二层布局 ###################################

        vboxnetA = wx.BoxSizer(wx.VERTICAL) # 纵向box
        vboxnetA.Add(self.treeListCtrl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)  # proportion参数控制容器尺寸比例
        vboxnetA.Add(self._init_startup_log(), proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2) # 创建并初始化日志框
        vboxnetA.Add(self.btnSizer, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)  # proportion参数控制容器尺寸比例

        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(vboxnetA, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.HBoxPanelSizer.Add(vboxnetB, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(self.HBoxPanelSizer) # 使布局有效

        ################################### 辅助配置 ###################################
        # 创建形态选股日志
        self.patlog = PatLogIf(self.patten_log_tx)

        # 创建菜单栏
        self._init_menu_bar()
        # 创建状态栏
        self._init_status_bar()

    def _init_menu_bar(self):

        # 创建窗口面板
        menuBar = wx.MenuBar(style=wx.MB_DOCKABLE)

        toolmenu = wx.Menu()
        about = wx.MenuItem(toolmenu, wx.ID_ANY, '&使用帮助')
        toolmenu.Append(about)
        menuBar.Append(toolmenu, '&数据下载工具')

        mainmenu = wx.Menu()
        backitem = wx.MenuItem(mainmenu, wx.ID_ANY, '&返回')
        # 返回主菜单按钮
        self.Bind(wx.EVT_MENU, self._ev_switch_menu, backitem)  # 绑定事件
        mainmenu.Append(backitem)
        menuBar.Append(mainmenu, '&主菜单')

        self.SetMenuBar(menuBar)

    def _init_status_bar(self):

        self.statusBar = self.CreateStatusBar() # 创建状态条
        # 将状态栏分割为3个区域,比例为2:1
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusWidths([-2, -1, -1])
        t = time.localtime(time.time())
        self.SetStatusText("公众号：元宵大师带你用Python量化交易", 0)
        self.SetStatusText("当前版本：%s" % Base_File_Oper.load_sys_para("sys_para.json")["__version__"], 1)
        self.SetStatusText(time.strftime("%Y-%B-%d %I:%M:%S", t), 2)
        self.Center()

    def init_tree(self):
        self.treeListCtrl = CollegeTreeListCtrl(parent=self, size=(200, 400))
        self.treeListCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.event_OnTreeListCtrlClickFunc)
        self.treeListCtrl.refDataShow(self.stock_tree_info) # TreeCtrl显示数据接口

    def update_process_bar(self, count):
        self.dialog.Update(self.total_len - count)

    def close_process_bar(self):

        self.dialog.Destroy()
        self.startup_log_tx.Clear()
        update_all_count = 0
        update_success_count = 0
        update_fail_count = 0
        self.failed_list.clear()
        self.elapsed_time = time.perf_counter()

        while not q_results.empty():
            info = q_results.get()

            self.startup_log_tx.AppendText("股票代码:{}; 更新状态:{}; 更新数目:{} \n".format(info["code"], info["status"], info["number"]))

            if info["status"] == "Success":
                update_success_count += 1
                update_all_count += 1
            elif info["status"] == "Fail":
                update_fail_count += 1
                #self.log_tx.AppendText('更新失败的股票为：{}\n'.format(info["code"]))
                self.failed_list.append(info["code"])

        self.startup_log_tx.AppendText('*'*10)
        self.startup_log_tx.AppendText('\n共更新{}支股票，{}支股票增加数据，{}支股票更新失败\n'.format(update_all_count, update_success_count, update_fail_count))
        self.startup_log_tx.AppendText('\n共耗时{}秒\n'.format(self.elapsed_time - self.start_time))

    ################################### 形态选股相关 ###################################

    def add_patten_para_lay(self, sub_panel):

        # 形态选股参数
        patten_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 形态选股参数——日历控件时间周期
        self.patten_end_time = wx.adv.DatePickerCtrl(sub_panel, -1,
                                                  style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#结束时间
        self.patten_start_time = wx.adv.DatePickerCtrl(sub_panel, -1,
                                                    style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#起始时间

        self.patten_start_date_box = wx.StaticBox(sub_panel, -1, u'开始日期(Start)')
        self.patten_end_date_box = wx.StaticBox(sub_panel, -1, u'结束日期(End)')
        self.patten_start_date_sizer = wx.StaticBoxSizer(self.patten_start_date_box, wx.VERTICAL)
        self.patten_end_date_sizer = wx.StaticBoxSizer(self.patten_end_date_box, wx.VERTICAL)
        self.patten_start_date_sizer.Add(self.patten_start_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.patten_end_date_sizer.Add(self.patten_end_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.patten_end_time.SetValue(date_time_now)
        self.patten_start_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

        # 形态选股参数——股票周期选择
        self.patten_period_box = wx.StaticBox(sub_panel, -1, u'股票周期')
        self.patten_period_sizer = wx.StaticBoxSizer(self.patten_period_box, wx.VERTICAL)
        self.patten_period_cbox = wx.ComboBox(sub_panel, -1, u"", choices=[u"日线"])
        self.patten_period_cbox.SetSelection(0)
        self.patten_period_sizer.Add(self.patten_period_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 形态选股参数——股票复权选择
        self.patten_authority_box = wx.StaticBox(sub_panel, -1, u'股票复权')
        self.patten_authority_sizer = wx.StaticBoxSizer(self.patten_authority_box, wx.VERTICAL)
        self.patten_authority_cbox = wx.ComboBox(sub_panel, -1, u"", choices=[u"前复权", u"后复权", u"不复权"])
        self.patten_authority_cbox.SetSelection(2)
        self.patten_authority_sizer.Add(self.patten_authority_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 形态选股参数———形态类型选取
        self.patten_type_box = wx.StaticBox(sub_panel, -1, u'选股模型')
        self.patten_type_sizer = wx.StaticBoxSizer(self.patten_type_box, wx.HORIZONTAL)

        self.patten_type_cmbo = wx.ComboBox(sub_panel, -1,  choices=["不启用", "双底形态", "RPS-Top10", "跳空缺口-预留","金叉死叉-预留","线性回归-预留"],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股项
        self.patten_type_cmbo.SetSelection(1)
        self.patten_type_sizer.Add(self.patten_type_cmbo, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 形态选股参数———股票池选取
        self.patten_pool_box = wx.StaticBox(sub_panel, -1, u'股票池选取')
        self.patten_pool_sizer = wx.StaticBoxSizer(self.patten_pool_box, wx.HORIZONTAL)

        self.patten_pool_cmbo = wx.ComboBox(sub_panel, -1,  choices=["全市场股票"],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股项
        self.patten_pool_cmbo.SetSelection(0)
        self.patten_pool_sizer.Add(self.patten_pool_cmbo, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 选股按钮
        self.pick_patten_but = wx.Button(sub_panel, -1, "开始选股")
        self.pick_patten_but.Bind(wx.EVT_BUTTON, self._ev_patten_select)  # 绑定按钮事件

        # 保存按钮
        #self.save_patten_but = wx.Button(sub_panel, -1, "保存结果")
        #self.save_patten_but.Bind(wx.EVT_BUTTON, self._ev_patten_save)  # 绑定按钮事件

        patten_para_sizer.Add(self.patten_start_date_sizer, proportion=0, flag=wx.EXPAND | wx.CENTER | wx.ALL, border=10)
        patten_para_sizer.Add(self.patten_end_date_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        patten_para_sizer.Add(self.patten_period_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        patten_para_sizer.Add(self.patten_authority_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        patten_para_sizer.Add(self.patten_type_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        patten_para_sizer.Add(self.patten_pool_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        patten_para_sizer.Add(self.pick_patten_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        #patten_para_sizer.Add(self.save_patten_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)

        return patten_para_sizer

    def _init_startup_log(self):

        self.startup_log_tx = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(200, 300)) # 启动相关日志

        return self.startup_log_tx

    def _init_patten_log(self):

        # 创建形态选股日志
        self.patten_log_tx = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(250, 300))

        return self.patten_log_tx
    ################################### 表格相关 ###################################

    def init_grid(self):
        self.grid = wx.grid.Grid(self, -1)
        self.grid.CreateGrid(50, 11) # 初始化时默认生成

    def data_to_grid(self, df):

        self.grid = wx.grid.Grid(self, -1)

        if df.empty != True:
            self.list_columns = df.columns.tolist()
            self.grid.CreateGrid(df.shape[0], df.shape[1])

            for col, series in df.iteritems(): # 将DataFrame迭代为(列名, Series)对
                m = self.list_columns.index(col)
                self.grid.SetColLabelValue(m, col)
                for n, val in enumerate(series):
                    self.grid.SetCellValue(n, m, str(val))
                self.grid.AutoSizeColumn(m, True)  # 自动调整列尺寸

    def refresh_grid(self, update_df):

        self.grid.Destroy()  # 先摧毁 后创建
        self.data_to_grid(update_df)

        self.HBoxPanelSizer.Add(self.grid, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # 使布局有效
        self.HBoxPanelSizer.Layout()

    ################################### 事件函数 ###################################
    def event_OnTreeListCtrlClickFunc(self, event):

        self.currentTreeItem = self.treeListCtrl.GetItemText(event.GetItem())

        try:
            df = pd.read_csv(data_path + self.currentTreeItem, index_col=0, parse_dates=[u"日期"], encoding='GBK',
                             engine='python')  # 文件名中含有中文时使用engine为python

            view_stock_data = ViewGripDiag(self, u"查看离线日线数据csv", df)
            """ 自定义提示框 """
            if view_stock_data.ShowModal() == wx.ID_OK:
                pass
            else:
                pass

        except:
            MessageDialog("读取文件出错! \n")

    def on_click_start(self, event):

        for code in self.stock_list_all:
            if q_codes.full() != True:
                code_split = code.lower().split(".")
                stcok_code = code_split[1] + code_split[0]
                q_codes.put(stcok_code)

        self.dialog = wx.ProgressDialog("下载进度", "剩余时间", self.total_len,
                                        style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)

        self.progress = ProgressBarThread(self)
        self.progress.start()

        for i in range(8):
            t = CrawlerThread(self)
            t.start()

        self.start_time = time.perf_counter()

    def on_click_fresh(self, event):
        pass

    def on_click_compt(self, event):

        if self.failed_list != []:

            for code in self.failed_list:
                if q_codes.full() != True:
                    q_codes.put(code)

            self.dialog = wx.ProgressDialog("下载进度", "剩余时间", self.total_len,
                                            style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)

            self.progress = ProgressBarThread(self)
            self.progress.start()

            t = CrawlerThread(self)
            t.start()
            self.start_time = time.perf_counter()
        else:
            MessageDialog("补充下载列表为空! \n")

    def _ev_switch_menu(self, event):
        self.fun_swframe(0)  # 切换 Frame 主界面

    def _ev_patten_select(self, event):

        # 第一步: 收集控件中设置的选项
        st_period = self.patten_period_cbox.GetStringSelection()
        st_auth = self.patten_authority_cbox.GetStringSelection()
        sdate_obj = self.patten_start_time.GetValue()
        edate_obj = self.patten_end_time.GetValue()

        sdate_val = datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)
        edate_val = datetime(edate_obj.year, edate_obj.month + 1, edate_obj.day)

        patten_pool = self.patten_pool_cmbo.GetStringSelection()

        MessageDialog("温馨提示：为解决全市场股票扫描时的效率问题，在本页面增加选股功能！")

        self.patlog.clr_print()
        self.patlog.re_print(f"启动{patten_pool} 选股模型分析......\n")

        # 初始化变量
        count = 0
        df_search = pd.DataFrame()  # 构建一个空的dataframe用来装数据

        if self.patten_type_cmbo.GetStringSelection() == "双底形态":

            proc_dialog = ProgressDialog("开始分析", len(down_stock_list)+1)  # 根据股票数量设置进度条刻度长度

            patten_recognize = DouBottomDialog(self, "双底形态识别参数配置")

            if patten_recognize.ShowModal() == wx.ID_OK:

                for stcok_code in down_stock_list:

                    try:
                        code = stcok_code[2:8] + "." + stcok_code[0:2].upper()
                        name = self.stock_tree_info.get(code)

                        stock_dat = Csv_Backend.load_history_st_data(data_path + stcok_code + '.csv', st_auth)

                        recon_data = {'High': stock_dat["最高价"], 'Low': stock_dat["最低价"], 'Open': stock_dat["开盘价"],
                                      'Close': stock_dat["收盘价"], 'Volume': stock_dat["成交量"], 'pctChg': stock_dat["涨跌幅"]}

                        df_recon = pd.DataFrame(recon_data)

                        df_return = Base_Patten_Group.double_bottom_search(name, code, df_recon, self.patlog,
                                                               **patten_recognize.feedback_paras())

                        if df_return.empty != True:
                            # 有效则添加至分析结果文件中
                            df_search = pd.concat([df_search, df_return], ignore_index=True, sort=False)

                        proc_dialog.update_bar(count)
                        count = count + 1
                    except:
                        self.patlog.re_print(f"\n形态分析出错！股票代码:{stcok_code}")

            self.patlog.re_print("\n形态分析完成！形态分析明细查看ConfigFiles路径的双底形态分析结果-高速版.csv")
            proc_dialog.close_bar()

            df_search = df_search[["股票名称", "股票代码",
                                   "形态识别", "左底id", "左底价格", "右底id", "右底价格", "中顶id", "中顶价格",
                                   "收盘价格", "颈线价格","首次突破",
                                   "突破幅度", "当日涨幅",
                                   "突破放量", "当前成交量-手", "平均成交量-手"]]

            if patten_recognize.feedback_paras()[u"选股结果保存"] == u"满足突破幅度才保存":
                df_search = df_search[df_search["突破幅度"] == True]

            elif patten_recognize.feedback_paras()[u"选股结果保存"] == u"满足首次突破才保存":
                df_search = df_search[df_search["首次突破"] == True]

            elif patten_recognize.feedback_paras()[u"选股结果保存"] == u"满足突破涨幅才保存":
                df_search = df_search[df_search["涨幅有效"] == True]

            elif patten_recognize.feedback_paras()[u"选股结果保存"] == u"满足突破放量才保存":
                df_search = df_search[df_search["突破放量"] == True]

            else:
                pass

            Base_File_Oper.save_patten_analysis(df_search, f"{datetime.now().strftime('%y-%m-%d')}-双底形态分析结果-高速版")

            sys_para = Base_File_Oper.load_sys_para("sys_para.json")

            auto_send_email('主人！你的双底形态分析报告来啦', "\n形态分析明细查看ConfigFiles路径的双底形态分析结果-高速版.csv",
                            f"{datetime.now().strftime('%y-%m-%d')}-双底形态分析结果-高速版.csv",
                            self.patlog, **sys_para["mailbox"])

        elif self.patten_type_cmbo.GetStringSelection() == "RPS-Top10":

            proc_dialog = ProgressDialog("开始分析", self.total_len+1)  # 根据股票数量设置进度条刻度长度

            rpstop_recognize = RpsTop10Dialog(self, "RPS-Top10识别参数配置")

            if rpstop_recognize.ShowModal() == wx.ID_OK:

                rps_para = rpstop_recognize.feedback_paras()
                df_basic = basic_code_list(['ts_code', 'name', 'area', 'list_date'])

                # 剔除出新股和次新股 即只考虑2017年1月1日以前上市的股票
                df_basic = df_basic[df_basic['list_date'].apply(int).values < rps_para["过滤次新股上市时间"]]  # 转换为int后筛选

                # 获取当前所有非新股/次新股代码和名称
                codes = df_basic.ts_code.values
                names = df_basic.name.values
                # 构建一个字典方便调用
                code_name = dict(zip(names, codes))

                track_name = ""
                track_close = []

                for name, code in code_name.items():

                    try:
                        num, sym = code.lower().split(".")
                        stock_dat = Csv_Backend.load_history_st_data(data_path + sym + num + '.csv', st_auth)
                        if rps_para[u"输入跟踪排名的代码"] == code:
                            track_name = name
                            track_close = stock_dat["收盘价"][-rps_para["选取涨跌幅滚动周期"]:]

                        # w:周5; 月20; 半年120; 一年250
                        stock_dat["涨跌幅"] = stock_dat["涨跌幅"].rolling(window=rps_para["选取涨跌幅滚动周期"]).mean().round(2)
                        df_search[name] = stock_dat["涨跌幅"][-rps_para["选取涨跌幅滚动周期"]:].fillna(0)
                        self.patlog.re_print(f"完成{name} {sym + num}涨跌幅计算......\n")
                        proc_dialog.update_bar(count)
                        count = count + 1
                    except:
                        self.patlog.re_print(f"警告！{name} {sym + num}涨跌幅计算时数据有误！......\n")

                df_search.fillna(0, inplace=True)
                df_return, df_track = Base_Indicate_Group.rps_top10_order(df_search, rps_para["选取显示的排名范围"], track_name)

                self.patlog.re_print("\nRPS排名分析完成！排名明细查看ConfigFiles路径的RPS—Top10分析结果-高速版.csv")
                proc_dialog.close_bar()

                Base_File_Oper.save_patten_analysis(df_return, f"{datetime.now().strftime('%y-%m-%d')}-RPS—Top10分析结果-高速版")

                if (rps_para[u"输入跟踪排名的代码"].find('.') != -1) and track_name != "":  # 输入代码正常
                    self.patlog.re_print(f"\n开始跟踪个股{rps_para['输入跟踪排名的代码']}排名动态!")
                    df_track["close"] = track_close

                    fig = plt.figure(figsize=(12, 8))
                    # 在Figure对象中创建一个Axes对象，每个Axes对象即为一个绘图区域 
                    ax1 = fig.add_subplot(211)
                    ax2 = fig.add_subplot(212)

                    df_track['close'].plot(ax=ax1, color='r')
                    ax1.set_title(track_name + '股价走势', fontsize=15)
                    # ax = plt.gca()
                    ax1.spines['right'].set_color('none')
                    ax1.spines['top'].set_color('none')

                    df_track['rps'].plot(ax=ax2, color='b')
                    ax2.set_title(track_name + 'RPS相对强度', fontsize=15)
                    my_ticks = pd.date_range(df_track.index[0], df_track.index[-1], freq='m')
                    ax2.set_xticklabels(my_ticks)
                    # ax = plt.gca()

                    ax2.spines['right'].set_color('none')
                    ax2.spines['top'].set_color('none')
                    # 保存图片到本地
                    plt.savefig(os.path.dirname(os.path.dirname(__file__)) + '/ConfigFiles/'+f'跟踪{track_name}的RPS.jpg')
                    self.patlog.re_print(f"\n跟踪{rps_para['输入跟踪排名的代码']}排名动态完成!已保存至ConfigFiles目录")

        #print(self.patlog.get_values()) # 返回控件中所有的内容

    def _ev_patten_save(self,event):
        pass