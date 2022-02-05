#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import wx.adv
import wx.grid
import wx.html2

from MainlyGui.MainFrame import MainFrame
from MainlyGui.UserFrame import UserFrame
from MainlyGui.ConfFrame import ConfFrame
from MainlyGui.DataFrame import DataFrame


class GuiManager():
    def __init__(self, Fun_SwFrame):
        self.fun_swframe = Fun_SwFrame
        self.frameDict = {}  # 用来装载已经创建的Frame对象

    def MsgDialog(self, info):
        # 提示一些使用注意事项的对话框
        dlg_mesg = wx.MessageDialog(None, info, u"温馨提示",
                                    wx.YES_NO | wx.ICON_INFORMATION)
        dlg_mesg.ShowModal()
        dlg_mesg.Destroy()

    def GetFrame(self, type):
        frame = self.frameDict.get(type)
        if frame is None:
            frame = self.SwitchFrame(type)
            self.frameDict[type] = frame
        return frame

    def SwitchFrame(self, type):
        if type == 0: # 主界面
            return MainFrame(parent=None, id=type, Fun_SwFrame=self.fun_swframe)
        elif type == 1: # 量化分析界面
            self.MsgDialog("确认已经在【配置】页面选择当前的系统为【Mac】或【Win】？")
            return UserFrame(parent=None, id=type, Fun_SwFrame=self.fun_swframe)

        elif type == 2: # 数据管理界面
            return DataFrame(parent=None, id=type, Fun_SwFrame=self.fun_swframe)
        elif type == 3: #
            pass
        elif type == 4: # 系统配置界面
            return ConfFrame(parent=None, id=type, Fun_SwFrame=self.fun_swframe)

class MainApp(wx.App):

    def OnInit(self):
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        self.manager = GuiManager(self.SwitchFrame)
        self.frame = self.manager.GetFrame(0)
        self.frame.Show()
        self.frame.Center()
        self.SetTopWindow(self.frame)
        return True

    def SwitchFrame(self, type):
        # 切换Frame对象
        self.frame.Show(False)
        self.frame = self.manager.GetFrame(type)
        self.frame.Show(True)



