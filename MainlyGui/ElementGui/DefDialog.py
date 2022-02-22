#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt


from CommIf.SysFile import Base_File_Oper
from MainlyGui.ElementGui.DefPanel import GroupPanel


def MessageDialog(info):
    # 提示对话框
    # info:提示内容
    back_info = ""
    dlg_mesg = wx.MessageDialog(None, info, u"温馨提示",
                                wx.YES_NO | wx.ICON_INFORMATION)
    if dlg_mesg.ShowModal() == wx.ID_YES:
        back_info = "点击Yes"
    else:
        back_info = "点击No"
    dlg_mesg.Destroy()
    return back_info

def ChoiceDialog(info, choice):

    dlg_mesg = wx.SingleChoiceDialog(None, info, u"单选提示", choice)
    dlg_mesg.SetSelection(0)  # default selection

    if dlg_mesg.ShowModal() == wx.ID_OK:
        select = dlg_mesg.GetStringSelection()
    else:
        select = None
    dlg_mesg.Destroy()
    return select

def ImportFileDiag():
    # 导入文件对话框
    # return:文件路径
    # wildcard = "CSV Files (*.xls)|*.xls"
    wildcard = "CSV Files (*.csv)|*.csv"
    dlg_mesg = wx.FileDialog(None, "请选择文件", os.getcwd(), "", wildcard,
                             wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)  # 旧版 wx.OPEN wx.CHANGE_DIR
    if dlg_mesg.ShowModal() == wx.ID_OK:
        file_path = dlg_mesg.GetPath()
    else:
        file_path = ''
    dlg_mesg.Destroy()
    return file_path

class GroupPctDiag(wx.Dialog):  # 多股收益率/波动率分析

    def __init__(self, parent, title=u"自定义提示信息", set_stocks=[], mean_val=[], std_val=[], size=(700, 500)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        self.stock_set = set_stocks
        self.mean = mean_val
        self.std = std_val

        self.GroupPanel = GroupPanel(self)  # 自定义
        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(self.GroupPanel, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # 使布局有效
        self.draw_figure()

    def draw_figure(self):

        self.GroupPanel.relate.clear()
        self.GroupPanel.relate.scatter(self.mean, self.std, marker='o',
                                       c=np.linspace(0.1, 1, len(self.stock_set)),
                                       s=500,
                                       cmap=plt.get_cmap('Spectral'))

        self.GroupPanel.relate.set_xlabel("均值%")
        self.GroupPanel.relate.set_ylabel("标准差%")

        for label, x, y in zip(self.stock_set, self.mean, self.std):
            self.GroupPanel.relate.annotate(label, xy=(x, y), xytext=(20, 20),
                                            textcoords="offset points",
                                            ha="right", va="bottom",
                                            bbox=dict(boxstyle='round, pad=0.5',
                                                      fc='red', alpha=0.2),
                                            arrowprops=dict(arrowstyle="->",
                                                            connectionstyle="arc3,rad=0.3"))
        self.GroupPanel.FigureCanvas.draw()

class GroupTrendDiag(wx.Dialog):  # 行情走势叠加分析

    def __init__(self, parent, title=u"自定义提示信息", set_stocks=[], df_stcok=[], size=(700, 500)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        self.stock_set = set_stocks
        self.df_stcok = df_stcok

        self.GroupPanel = GroupPanel(self)  # 自定义
        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(self.GroupPanel, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # 使布局有效
        self.draw_figure()

    def draw_figure(self):

        self.GroupPanel.relate.clear()
        self.df_stcok.plot(ax=self.GroupPanel.relate)

        self.GroupPanel.relate.set_xlabel("日期")
        self.GroupPanel.relate.set_ylabel("归一化走势")

        self.GroupPanel.FigureCanvas.draw()

class UserDialog(wx.Dialog):  # user-defined

    def __init__(self, parent, title=u"自定义提示信息", label=u"自定义日志", size=(700, 500)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        self.log_tx_input = wx.TextCtrl(self, -1, "", size=(600, 400), style=wx.TE_MULTILINE | wx.TE_READONLY)  # 多行|只读
        self.log_tx_input.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))

        self.ok_btn = wx.Button(self, wx.ID_OK, u"确认")
        self.ok_btn.SetDefault()

        self.dialog_info_box = wx.StaticBox(self, -1, label)
        self.dialog_info_sizer = wx.StaticBoxSizer(self.dialog_info_box, wx.VERTICAL)
        self.dialog_info_sizer.Add(self.log_tx_input, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        self.dialog_info_sizer.Add(self.ok_btn, proportion=0, flag=wx.ALIGN_CENTER)
        self.SetSizer(self.dialog_info_sizer)

        self.disp_loginfo()

    def disp_loginfo(self):
        self.log_tx_input.Clear()
        self.log_tx_input.AppendText(Base_File_Oper.read_log_trade())

class ProgressDialog():

    def __init__(self, title=u"下载进度", maximum=1000):

        self.dialog = wx.ProgressDialog(title, "剩余时间", maximum,
                                        style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)

    def update_bar(self, count):
        self.dialog.Update(count)

    def close_bar(self):
        self.dialog.Destroy()

    def reset_range(self, maximum):
        self.dialog.SetRange(maximum)

class BrowserF10(wx.Dialog):

    def __init__(self, parent, title=u"自定义提示信息", code="300180", size=(1000, 900)):
        wx.Dialog.__init__(self, parent, -1, title, size, style=wx.DEFAULT_FRAME_STYLE)

        if '.' in code:
            code = code.split('.')[1]

            if (code[0] == "3" or code[0] == "0" or code[0] == "6") and (len(code) == 6):
                self.code = code

                sizer = wx.BoxSizer(wx.VERTICAL)
                self.browser = wx.html2.WebView.New(self)
                sizer.Add(self.browser, 1, wx.EXPAND, 10)
                self.SetSizer(sizer)
                self.SetSize((1000, 900))

                self.load_f10()

    def load_f10(self):

        self.browser.LoadURL("http://basic.10jqka.com.cn/" + self.code + "/operate.html#intro")  # 加载页面

class WebDialog(wx.Dialog):  # user-defined

    load_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/DataFiles/'

    def __init__(self, parent, title=u"Web显示", file_name='treemap_base.html', size=(1200, 900)):

        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        self.browser = wx.html2.WebView.New(self, -1, size=size)
        with open(self.load_path + file_name, 'r') as f:
            html_cont = f.read()
        self.browser.SetPage(html_cont, "")
        self.browser.Show()

class DouBottomDialog(wx.Dialog):  # 双底形态参数

    load_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/ConfigFiles/'

    def __init__(self, parent, title=u"自定义提示信息", size=(700, 750)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style = wx.DEFAULT_FRAME_STYLE)

        # 创建FlexGridSizer布局网格
        # rows 定义GridSizer行数
        # cols 定义GridSizer列数
        # vgap 定义垂直方向上行间距
        # hgap 定义水平方向上列间距
        self.FlexGridSizer = wx.FlexGridSizer(rows=9, cols=1, vgap=0, hgap=0)

        self.ok_btn = wx.Button(self, wx.ID_OK, u"确认")
        self.ok_btn.SetDefault()
        self.cancel_btn = wx.Button(self, wx.ID_CANCEL, u"取消")

        # 选取K线范围
        self.period_amount_box = wx.StaticBox(self, -1, "选取K线范围(日)")
        self.period_amount_sizer = wx.StaticBoxSizer(self.period_amount_box, wx.VERTICAL)
        self.period_amount_input = wx.TextCtrl(self, -1, "40", style=wx.TE_PROCESS_ENTER)
        self.period_amount_sizer.Add(self.period_amount_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 选取中间区域误差
        self.middle_err_box = wx.StaticBox(self, -1, "选取中间区域误差(日)")
        self.middle_err_sizer = wx.StaticBoxSizer(self.middle_err_box, wx.VERTICAL)
        self.middle_err_input = wx.TextCtrl(self, -1, "5", style=wx.TE_PROCESS_ENTER)
        self.middle_err_sizer.Add(self.middle_err_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 双底低点之间误差
        self.lowbetw_err_box = wx.StaticBox(self, -1, "双底低点之间误差%")
        self.lowbetw_err_sizer = wx.StaticBoxSizer(self.lowbetw_err_box, wx.VERTICAL)
        self.lowbetw_err_input = wx.TextCtrl(self, -1, "2", style=wx.TE_PROCESS_ENTER)
        self.lowbetw_err_sizer.Add(self.lowbetw_err_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 有效突破颈线幅度
        self.backcfm_thr_box = wx.StaticBox(self, -1, "有效突破颈线幅度%")
        self.backcfm_thr_sizer = wx.StaticBoxSizer(self.backcfm_thr_box, wx.VERTICAL)
        self.backcfm_thr_input = wx.TextCtrl(self, -1, "3", style=wx.TE_PROCESS_ENTER)
        self.backcfm_thr_sizer.Add(self.backcfm_thr_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 有效突破当天涨跌幅
        self.break_pctchg_box = wx.StaticBox(self, -1, "有效突破当天涨跌幅%")
        self.break_pctchg_sizer = wx.StaticBoxSizer(self.break_pctchg_box, wx.VERTICAL)
        self.break_pctchg_input = wx.TextCtrl(self, -1, "1", style=wx.TE_PROCESS_ENTER)
        self.break_pctchg_sizer.Add(self.break_pctchg_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 有效突破成交量阈值
        self.volume_thr_box = wx.StaticBox(self, -1, "有效突破成交量阈值(大于平均%)")
        self.volume_thr_sizer = wx.StaticBoxSizer(self.volume_thr_box, wx.VERTICAL)
        self.volume_thr_input = wx.TextCtrl(self, -1, "5", style=wx.TE_PROCESS_ENTER)
        self.volume_thr_sizer.Add(self.volume_thr_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.save_cond_box = wx.RadioBox(self, -1, label=u'选股结果保存', choices=["出现双底即保存","满足突破幅度才保存",
                                                                              "满足首次突破才保存", "满足突破涨幅才保存",
                                                                              "满足突破放量才保存"],
                                                                     majorDimension = 5, style = wx.RA_SPECIFY_ROWS)

        # 加入Sizer中
        self.FlexGridSizer.Add(self.period_amount_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.middle_err_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.lowbetw_err_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.backcfm_thr_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.break_pctchg_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.volume_thr_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.save_cond_box, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.ok_btn, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.cancel_btn, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.SetFlexibleDirection(wx.BOTH)

        # 声明图片对象
        image = wx.Image(self.load_path+r'双底形态识别模型图.png', wx.BITMAP_TYPE_PNG)
        #print('图片的尺寸为{0}x{1}'.format(image.GetWidth(),image.GetHeight()))

        image.Rescale(image.GetWidth(),image.GetHeight())
        embed_pic = image.ConvertToBitmap()
        # 显示图片
        self.embed_bitmap = wx.StaticBitmap(self,-1, bitmap=embed_pic, size=(image.GetWidth(), image.GetHeight()))

        # 添加参数布局
        self.vbox_sizer = wx.BoxSizer(wx.HORIZONTAL)  # 纵向box
        self.vbox_sizer.Add(self.FlexGridSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=2)
        self.vbox_sizer.Add(self.embed_bitmap, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=2)

        self.SetSizer(self.vbox_sizer)

    def feedback_paras(self):

        self.bottom_para = dict()

        self.bottom_para[u"选取K线范围"] = int(self.period_amount_input.GetValue())
        self.bottom_para[u"选取中间区域误差"] = int(self.middle_err_input.GetValue())
        self.bottom_para[u"双底低点之间误差"] = float(self.lowbetw_err_input.GetValue())
        self.bottom_para[u"有效突破当天涨跌幅"] = float(self.break_pctchg_input.GetValue())
        self.bottom_para[u"有效突破颈线幅度"] = int(self.backcfm_thr_input.GetValue())
        self.bottom_para[u"有效突破成交量阈值"] = float(self.volume_thr_input.GetValue())
        self.bottom_para[u"选股结果保存"] = self.save_cond_box.GetStringSelection()

        return self.bottom_para

class RpsTop10Dialog(wx.Dialog):  # RPS-10参数

    def __init__(self, parent, title=u"自定义提示信息", size=(250, 360)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)

        # 创建FlexGridSizer布局网格
        # rows 定义GridSizer行数
        # cols 定义GridSizer列数
        # vgap 定义垂直方向上行间距
        # hgap 定义水平方向上列间距
        self.FlexGridSizer = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        self.ok_btn = wx.Button(self, wx.ID_OK, u"确认")
        self.ok_btn.SetDefault()
        self.cancel_btn = wx.Button(self, wx.ID_CANCEL, u"取消")

        # 过滤次新股
        self.filter_list_time = wx.adv.DatePickerCtrl(self, -1,
                                                  style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#结束时间

        self.filter_list_box = wx.StaticBox(self, -1, u'上市时间\n(过滤该时间之后上市的股票)')
        self.filter_list_sizer = wx.StaticBoxSizer(self.filter_list_box, wx.VERTICAL)
        self.filter_list_sizer.Add(self.filter_list_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.filter_list_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

        # 选取涨跌幅滚动周期
        self.period_roll_box = wx.StaticBox(self, -1, "选取涨跌幅滚动周期")
        self.period_roll_sizer = wx.StaticBoxSizer(self.period_roll_box, wx.VERTICAL)
        self.period_roll_input = wx.TextCtrl(self, -1, "20", style=wx.TE_PROCESS_ENTER)
        self.period_roll_sizer.Add(self.period_roll_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 选取显示的排名范围
        self.sel_order_box = wx.StaticBox(self, -1, "选择观测的排名范围")
        self.sel_order_sizer = wx.StaticBoxSizer(self.sel_order_box, wx.VERTICAL)
        self.sel_order_val = [u"前10", u"前20", u"前30", u"前40", u"前50"]
        self.sel_order_cmbo = wx.ComboBox(self, -1, u"前10", choices=self.sel_order_val,
                                            style=wx.CB_SIMPLE | wx.CB_DROPDOWN | wx.CB_READONLY)  # 选择操作系统
        self.sel_order_sizer.Add(self.sel_order_cmbo, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 输入跟踪排名的代码
        self.track_code_box = wx.StaticBox(self, -1, u'跟踪股票代码')
        self.track_code_sizer = wx.StaticBoxSizer(self.track_code_box, wx.VERTICAL)
        self.track_code_input = wx.TextCtrl(self, -1, "000400.SZ", style=wx.TE_PROCESS_ENTER)
        self.track_code_sizer.Add(self.track_code_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 加入Sizer中
        self.FlexGridSizer.Add(self.filter_list_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.period_roll_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.sel_order_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.track_code_sizer, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.ok_btn, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.Add(self.cancel_btn, proportion=1, border=1, flag=wx.ALL | wx.EXPAND)
        self.FlexGridSizer.SetFlexibleDirection(wx.BOTH)

        self.SetSizer(self.FlexGridSizer)

    def feedback_paras(self):

        self.rps_para = dict()

        filter_obj = self.filter_list_time.GetValue()
        filter_val = datetime.datetime(filter_obj.year, filter_obj.month + 1, filter_obj.day)

        self.rps_para[u"过滤次新股上市时间"] = int(filter_val.strftime('%Y%m%d'))
        self.rps_para[u"选取涨跌幅滚动周期"] = int(self.period_roll_input.GetValue())
        self.rps_para[u"选取显示的排名范围"] = (int(self.sel_order_cmbo.GetSelection())+1)*10
        self.rps_para[u"输入跟踪排名的代码"] = self.track_code_input.GetValue()

        return self.rps_para

class ViewGripDiag(wx.Dialog):

    def __init__(self, parent, title=u"表格数据显示", update_df=[], size=(750, 500)):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style = wx.DEFAULT_FRAME_STYLE)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.data_to_grid(update_df)

        sizer.Add(self.grid, flag=wx.ALIGN_CENTER)

        self.SetSizer(sizer)

    def data_to_grid(self, df):

        self.grid = wx.grid.Grid(self, -1)

        if df.empty != True:
            self.list_columns = df.columns.tolist()
            self.grid.CreateGrid(df.shape[0], df.shape[1]) # 初始化时默认生成

            for col, series in df.iteritems():  # 将DataFrame迭代为(列名, Series)对
                m = self.list_columns.index(col)
                self.grid.SetColLabelValue(m, col)
                for n, val in enumerate(series):
                    self.grid.SetCellValue(n, m, str(val))
                self.grid.AutoSizeColumn(m, True)  # 自动调整列尺寸


