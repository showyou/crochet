# -*- coding: utf-8 -*-
import wx


#chgdep = ConfigDialog(None, -1, 'crochet config')

class ConfigDialog(wx.Dialog):
    # ダイアログを表示しイベント処理を行う
    def __init__(self, parent, id, title, user='', password=''):
        self.dialog = wx.Dialog(parent, id, title, size=(250, 170))
        self.user = user
        self.password = password
        
        panel = wx.Panel(self.dialog, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)

        wx.StaticBox(panel, -1, 'Twitter Account', (5, 5), (240, 90))
        wx.StaticText(panel, -1, 'ID', (15, 30))
        wx.StaticText(panel, -1, 'Password', (15, 60))
        self.userFld = wx.TextCtrl(panel, -1, self.user, (100, 30))
        self.passwordFld = wx.TextCtrl(panel, -1, self.password, (100, 60), style=wx.TE_PASSWORD)

        okButton = wx.Button(self.dialog, 1, 'OK', size=(70, 30))
        okButton.SetDefault()
        self.dialog.Bind(wx.EVT_BUTTON, self.OnSave, id=1)

        vbox.Add(panel)
        vbox.Add(okButton, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.dialog.SetSizer(vbox)
        self.dialog.ShowModal()

    # OKボタンが押されたら値を保存してダイアログを閉じる
    def OnSave(self, event):
        self.user = self.userFld.GetValue()
        self.password = self.passwordFld.GetValue()
        self.dialog.Destroy()
    
    # ユーザ,パスワードを返す
    def GetAccount(self):
        return {"user": self.user, "pass": self.password}
