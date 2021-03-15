#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import os

from CommIf.SysFile import Base_File_Oper


def MessageDiag(info):
    # 提示对话框
    # info:提示内容
    dlg_mesg = wx.MessageDialog(None, info, u"温馨提示",
                                wx.YES_NO | wx.ICON_INFORMATION)
    if dlg_mesg.ShowModal() == wx.ID_YES:
        print("点击Yes")
    else:
        print("点击No")
    dlg_mesg.Destroy()


def ImportFileDiag():
    # 导入文件对话框
    # return:文件路径
    wildcard = "CSV Files (*.csv)|*.csv"
    dlg_mesg = wx.FileDialog(None, "请选择文件", os.getcwd(), "", wildcard,
                             wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)  # 旧版 wx.OPEN wx.CHANGE_DIR
    if dlg_mesg.ShowModal() == wx.ID_OK:
        file_path = dlg_mesg.GetPath()
        print("点击Yes")
    else:
        print("点击No")
    dlg_mesg.Destroy()
    return file_path


class UserDialog(wx.Dialog):  # user-defined

    def __init__(self, parent, title=u"自定义提示信息", label=u"自定义日志"):
        wx.Dialog.__init__(self, parent, -1, title, size=(700, 500),
                           style=wx.CAPTION | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)

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
