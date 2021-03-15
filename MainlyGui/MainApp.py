#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import wx.adv
import wx.grid
import wx.html2

from MainlyGui.MainFrame import UserFrame


class MainApp(wx.App):

    def OnInit(self):
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        self.frame = UserFrame()
        self.frame.Show()
        self.frame.Center()
        self.SetTopWindow(self.frame)
        return True

def Wx_MainRun():

    app = MainApp()
    app.MainLoop()
