#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
import wx,wx_utils

import main_icon

import twitter3
import simplejson
import Image

import thread

g_config = {}
g_config['mycolor'] = wx.Color(240,248,255)


"""タブ振り分けフィルタ"""
class BranchFilter():
	def __init__(self,tabName,idFilter,bodyFilter,
					moveFrom,searchBoth,regexEnable,setMark):
		import re
		self.tabName = tabName
		self.idFilter = idFilter
		if bodyFilter != "":
			try:
				self.bodyFilter = re.compile(bodyFilter)
			except:
				print "invalid bodyFilter %s" % bodyFilter
				self.bodyFilter = False
		else:
				self.bodyFilter = False
		self.moveFrom = moveFrom
		self.searchBoth = searchBoth
		self.regexEnable = regexEnable
		self.setMark = setMark
	""" 振り分け処理を行う。
		適合すれば振り分けタブ名を、失敗すれば空文字列を返す """
	def doFilter(self,id,body):
		import re
		matchFlag = False
		if self.idFilter == id:
			matchFlag = True
		elif self.bodyFilter and self.bodyFilter.search(body):
			matchFlag = True

		if matchFlag == True:
			return self.tabName,self.moveFrom,self.setMark
		return "",False,False

"""画像取得用スレッド"""
class ImageGetFrame(wx.Frame):
	def __init__(self,url,callbackFunc,result,lock):
		self.url = url 
		self.func = callbackFunc 
		self.result = result
		self.lock = lock
	def start(self):
		thread.start_new_thread(self.run, ())

	def run(self):
		import urllib,time
		#ここに通信処理を書く
		imagePath =urllib.urlopen(self.url).read()
		try:
			#time.sleep(1)
			self.lock.acquire()
			self.func(imagePath,self.result)

		except:
			print "image read error",
		finally:
			self.lock.release()
	def __del__(self):
		pass
		#print "end ImageGetFrame"
"""
twitterにhttpRequestを投げるスレッド
"""
class TwDMHttpFrame(wx.Frame):
	def __init__(self,tw,func,lock):
		self.tw = tw
		self.func = func
		self.lock = lock
	def start(self):
		thread.start_new_thread(self.run, ())
	def run(self):
		#ここに通信処理を書く
		self.lock.acquire()
		try:
			a = self.tw.getDM("")
			self.func(a)
		except:
			print "Error:TwDMHttpFrame", sys.exc_info()[0]
		finally:
			self.lock.release()
"""
twitterにhttpRequestを投げるスレッド
"""
class TwReplyHttpFrame(wx.Frame):
	def __init__(self,tw,func,lock):
		self.tw = tw
		self.func = func
		self.lock = lock
	def start(self):

		thread.start_new_thread(self.run, ())
	
	def run(self):
		#ここに通信処理を書く
		self.lock.acquire()	
		try:
			a = self.tw.getReplies("")
			self.func(a)
		except:
			print "Error:TwReplyHttpFrame", sys.exc_info()[0]
		finally:
			self.lock.release()
"""
twitterにhttpRequestを投げるスレッド
"""
class TwHttpFrame(wx.Frame):
	def __init__(self,tw,func,lock):
		self.tw = tw
		self.func = func
		self.lock = lock
	def start(self):
		thread.start_new_thread(self.run, ())

	def run(self):
		print ("start http frame")
		#ここに通信処理を書く
		#a = self.tw.get("")
		self.lock.acquire()
		try:
			a = self.tw.getWithScraping("")
			self.func(a)
		except:
			print "Error:TwHttpFrame", sys.exc_info()[0]
		finally:
			self.lock.release()
	def __del__(self):
		print "delete HTTP Thread"	

"""
全てのnotebookpageの基になるページクラス
"""
class TmpTwitPage(wx.NotebookPage):
	def __init__(self, title, parent, threadLock):
		
		self.dataList = []
		self.hiddenDataList = []
		self.tmpDataList = []
		self.tmpHiddenDataList = []
		self.count = 0
		self.owner = parent
		self.lock = threadLock
		self.dataListLock = thread.allocate_lock() 
		wx.NotebookPage.__init__(self,parent.getNotebook(),-1)
		parent.getNotebook().AddPage(self,title)
		list = self.list = wx.ListCtrl(self,-1,style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_SINGLE_SEL)
		list.Bind(wx.EVT_KEY_DOWN, self.myKeyHandler)
		list.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDoubleClick)

		list.InsertColumn(0," ",1,20)
		list.InsertColumn(1,u"ユーザ")
		list.InsertColumn(2,u"発言",0,200)
		list.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnTwitListSelect)

	def OnTwitListSelect(self,event):
		import re
		selectedRow = self.selectedRow = event.GetIndex()
		dataList = self.dataList
		label = self.owner.userName
		text = self.owner.messageText
		text.SetValue(dataList[selectedRow][2])
		label.SetLabel(dataList[selectedRow][1])
		self.owner.SetImage(dataList[selectedRow][4])
		#選択したユーザに関する発言の色を変えてみる
				
		user = self.owner.tw.user['user']
		p = re.compile(dataList[selectedRow][1])
		for i in range(0,self.list.GetItemCount()):
			if p.search(dataList[i][1]):
				self.list.SetItemBackgroundColour(i,wx.Color(225,225,225))		
			elif p.search(self.dataList[i][2]) :
				self.list.SetItemBackgroundColour(i,wx.Color(192,225,225))		
			else:
				self.list.SetItemBackgroundColour(i,wx.Color(255,255,255))

			if re.match(user,self.dataList[i][1]):
				self.list.SetItemBackgroundColour(i,g_config['mycolor'])

			if re.search(user,self.dataList[i][2]):
				self.list.SetItemBackgroundColour(i,wx.Color(255,153,153))

	def ResetCount(self):
		self.count = 0
	# 後で多分実装	
	def ChangeItemColour(self,index,data,re,color):
		pass	
	def OnDoubleClick(self,event):
		selectedRow = event.GetIndex()
		user = "@" + self.dataList[selectedRow][1]
		self.owner.addUser2Inputbox(user)

	def myKeyHandler(self,evt):
		print evt.GetKeyCode(), 
		if self.selectedRow != -1:
			if evt.GetKeyCode() in [ord('k'),ord('K'),wx.WXK_UP]:
				print ('up')
				if self.selectedRow > 0:
		 			self.MoveList(self.selectedRow-1)
			if evt.GetKeyCode() in [ord('j'),ord('J'),wx.WXK_DOWN]:
				print ('down')
				if self.selectedRow < self.list.GetItemCount()-1:
					self.MoveList(self.selectedRow+1)
			if evt.GetKeyCode() in [ord('h'),ord('H'),wx.WXK_LEFT]:
				print ('left')
				leftcol = self.GetPrevItem(self.selectedRow)
				if leftcol != -1:
					self.MoveList(leftcol)
			if evt.GetKeyCode() in [ord('l'),ord('L'),wx.WXK_RIGHT]:
				print ('right')	
				rightcol = self.GetNextItem(self.selectedRow)
				if rightcol != -1:
					self.MoveList(rightcol)
			if evt.GetKeyCode() in [ord('s'),ord('S')]:
				print("favorite")
				id = self.hiddenDataList[self.selectedRow][0]
				self.owner.tw.createFavorite(id)
				self.owner.SetStatusBar(u"fav登録しました")
		if evt.GetKeyCode() in [ord('q'), ord('Q')]:
			wx.Exit()

	# 今のユーザ名を含む、前の発言を検索
	def GetPrevItem(self,row):
		import re
		print ('getprevItem')

		userName = self.dataList[row][1]
		p = re.compile(userName)
		currentRow = row-1
		while currentRow >= 0 :
			if (p.search(self.dataList[currentRow][1])): 
				return currentRow 
			currentRow-=1 
		return -1
	
	# 今のユーザ名を含む、後ろの発言を取得
	def GetNextItem(self,row):
		import re
		print ('getnextItem')
		userName = self.dataList[row][1]
		p = re.compile(userName)
		currentRow = row+1
		while currentRow < len(self.dataList) :
			if (p.search(self.dataList[currentRow][1])):
				return currentRow 
			currentRow+=1 
		return -1

	def MoveList(self,newRow):
		self.list.Select(self.selectedRow,0)
		self.list.Select(newRow)
		self.list.Focus(self.selectedRow)

	def InsertData(self,data,hiddenData):
		print ("start insert data")
		i = self.count
		#ここでロック
		self.dataListLock.acquire()
		self.tmpDataList.insert(i,data)# + self.dataList
		self.tmpHiddenDataList.insert(i,hiddenData)# + self.hiddenDataList
		self.dataListLock.release()
		#ここでアンロック
		self.count += 1

	#InsertDataで追加されてるかどうか確認して、あればリストに入れる
	def CheckUpdate(self):
		print ("start checkupdate")
		self.dataListLock.acquire()
		if len(self.tmpDataList) < 1 or len(self.tmpHiddenDataList) < 1:

			self.dataListLock.release()
			return False

		user = self.owner.tw.user['user']
		import re
		i = 0
		for b in self.tmpDataList:
	
			self.list.InsertStringItem(i,"")
			for j in range(3):
				self.list.SetStringItem(i,j,b[j])
		
			if re.match(user,b[1]):
				self.list.SetItemBackgroundColour(i,g_config['mycolor'])

			if re.search(user,b[2]):
				self.list.SetItemBackgroundColour(i,wx.Color(255,153,153))
		
			#import time
			#time.sleep(1)		
			#if 先読み=on
			#try:	
			self.owner.GetImageListElement(b[4])
			#except:
			#	print "Error:GetImageListElement"
			#	pass
			i += 1
		self.dataList[:0] =self.tmpDataList
		self.hiddenDataList[:0] = self.tmpHiddenDataList
		self.tmpDataList = [] 
		self.tmpHiddenDataList = []
		self.dataListLock.release()
		self.ResetCount()
		return True
"""
カスタムページ(自分でフィルタリングする)
"""
class CustomPage(TmpTwitPage):
	def __init__(self,title, parent,threadLock):
		self.dataList = []	
		TmpTwitPage.__init__(self,title,parent, threadLock)	
	
"""
最近のfriendsの発言一覧を表示するページ
customPageは上に移った
"""

try:
	import Growl
	g_growl = True
except:
	print "not exist:Growl sdk"
	g_growl = False

class RecentPage(TmpTwitPage):
	def __init__(self, parent,threadLock,filter):
		TmpTwitPage.__init__(self,"Recent",parent,threadLock)

		#self.dataList = []
		#self.hiddenDataList = []
		self.customPages = {}# フィルタリングページの固まり？
		self.filter = filter
		if g_growl == True:
			self.g = Growl.GrowlNotifier(
				applicationName='crochet',notifications=['newTwit'])
			self.g.register()
		
	def ResetCount(self):
		TmpTwitPage.ResetCount(self)		
		for p in self.customPages:
			self.customPages[p].ResetCount()
	
	def AppendCustomPage(self, customPage,customPageId):
		self.customPages[customPageId] = customPage

	def Reflesh(self):
		t = TwHttpFrame(self.owner.tw,self.RefleshList,self.lock)
		t.start()
		#t.run()

	def RefleshList(self,a):
		#lockかけた方がいいのかも。。
		self.ResetCount()
		user = self.owner.tw.user['user']
		for x in a:
			flag = 0
			
			# 重複発言チェック
			for d in self.dataList:
				if d[2] == x[1]:
					flag = 1
					break

			for p in self.customPages:
				for d in self.customPages[p].dataList:
					if d[2] == x[1]:
						flag = 1
						break
				if flag == 1: break

			if flag == 0 : 
				dataListElement = []
				dataListElement.append("")
				dataListElement.append(x[0])
				dataListElement.append(x[1])
				dataListElement.append(x[2])
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
				
				moveFrom = False 
				#if x[0] == "yuumizusawa" or x[0] == "miz_" or x[0] == "breeziness":
				#	self.customPages[0].InsertData(dataListElement,hiddenDataListElement)
				#	flag2 = 1
				for f in self.filter:
					tabName,moveFrom,setMark = f.doFilter(x[0],x[1]) 
					if tabName != "":
						print "tabHit",tabName
						self.customPages[tabName].InsertData(dataListElement,hiddenDataListElement)
						break
	
				if moveFrom == False:
					self.InsertData(dataListElement,hiddenDataListElement)
					if g_growl == True:
						self.g.notify(noteType='newTwit',title=x[0],
							description=x[1],sticky=False)
				self.owner.SetNowTime2StatusBar()

class ReplyPage(TmpTwitPage):

	def __init__(self, parent,threadLock):
		TmpTwitPage.__init__(self,"Reply",parent,threadLock)
		#self.dataList = []
		#self.hiddenDataList = []
	
	def Reflesh(self):
		t = TwReplyHttpFrame(self.owner.tw,self.RefleshList,self.lock)
		t.start()
			
	def RefleshList(self,a):
		#lockかけた方がいいのかも。。
		self.ResetCount()
		user = self.owner.tw.user['user']
		for x in a:
			flag = 0
			
			# 重複発言チェック
			for d in self.dataList:
				if d[2] == x[1]:
					flag = 1
					break
			if flag == 0 : 
				dataListElement = []
				dataListElement.append("")
				dataListElement.append(x[0])
				dataListElement.append(x[1])
				dataListElement.append(x[2])
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
	
				self.InsertData(dataListElement,hiddenDataListElement)	

class DMPage(TmpTwitPage):

	def __init__(self, parent,threadLock):
		TmpTwitPage.__init__(self,"DM",parent,threadLock)
		dataList = []
	def Reflesh(self):
		t = TwDMHttpFrame(self.owner.tw,self.RefleshList,self.lock)
		t.start()

	def RefleshList(self,a):
		#lockかけた方がいいのかも。。
		self.ResetCount()
		user = self.owner.tw.user['user']
		for x in a:
			flag = 0
			
			# 重複発言チェック
			for d in self.dataList:
				if d[2] == x[1]:
					flag = 1
					break
			if flag == 0 : 
				dataListElement = []
				dataListElement.append("")
				dataListElement.append(x[0])
				dataListElement.append(x[1])
				dataListElement.append(x[2])
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
	
				self.InsertData(dataListElement,hiddenDataListElement)	

class MainFrame(wx.Frame):
	"""MainFrame class deffinition.
	"""
	binder = wx_utils.bind_manager()

	TIMER_ID = 1
	TIMER_ID2= TIMER_ID+1
	TIMER_ID3= TIMER_ID2+1
	imageList = {}
	t = {}
	def loadUserData(self, fileName):
		#ファイルを開いて、データを読み込んで変換する
		#データ形式は(user,password)
		#try
		file = open(fileName,'r')
		a = simplejson.read(file.read())
		file.close()
		return a
		#catch exit(1)
		
	def __init__(self, parent=None):
		#from pit import Pit
		#twUserdata = Pit.get('twitter.com',{'require' : {'user':'','pass':''}})
		twUserdata = self.loadUserData(".chat/twdata")
		twTabConfig = self.loadUserData(".chat/tabconfig")

		wx.Frame.__init__(self,None, -1, "crochet")
		
		self.CreateStatusBar()

		self.selectedRow = -1
		text = self.text = wx.TextCtrl(self,-1,style=wx.TE_PROCESS_ENTER)
		text.Bind(wx.EVT_TEXT_ENTER, self.OnSendTW)
		button = self.button = wx.Button(self, -1, "Send")
		self.button.Bind(wx.EVT_BUTTON, self.OnSendTW) 
	
		notebook = self.notebook = wx.Notebook(self,-1,style=wx.NB_BOTTOM|wx.NB_MULTILINE)

		self.imageThreadLock = thread.allocate_lock()
		self.httpThreadLock = thread.allocate_lock()
		self.dataListThreadLock = thread.allocate_lock()	
		filter = []
		for f in twTabConfig['tabFilter']:
			filter.append(BranchFilter(f[0],f[1],f[2],f[3],f[4],f[5],f[6])	)	
		
		self.recentPage = RecentPage(self,self.httpThreadLock,filter)
		self.replyPage = ReplyPage(self,self.httpThreadLock)
		self.directPage = DMPage(self,self.httpThreadLock) 

		for p in twTabConfig['tabName']:
			page = CustomPage(p,self,self.httpThreadLock)
			self.recentPage.AppendCustomPage(page,p)	
		
		inputSizer = wx.BoxSizer(wx.HORIZONTAL)
		inputSizer.Add(self.text,2)
		inputSizer.Add(self.button,0)
		

		messageText=self.messageText = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_READONLY,size=(-1,65))
		userIcon = self.userIcon = wx.StaticBitmap(self,-1,wx.NullBitmap,(0,0),(64,64))
		userName = self.userName = wx.StaticText(self,-1,"test")
		twitTime = self.twitTime = wx.StaticText(self,-1,"---")
		
		messageSizer3 = wx.BoxSizer(wx.HORIZONTAL)
		messageSizer3.Add(userName,1,wx.EXPAND)
		messageSizer3.Add(twitTime,1,wx.EXPAND)

		messageSizer2 = wx.BoxSizer(wx.VERTICAL)
		messageSizer2.Add(messageSizer3,0,wx.EXPAND)
		messageSizer2.Add(messageText,0,wx.EXPAND)
		
		messageSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		messageSizer1.Add(userIcon,0,wx.EXPAND)
		messageSizer1.Add(messageSizer2,1,wx.EXPAND)
	
		messageSizer = wx.BoxSizer(wx.VERTICAL)	
		messageSizer.Add(messageSizer1,0,wx.EXPAND)
		messageSizer.Add(inputSizer,0,wx.EXPAND)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(notebook,2,wx.EXPAND)
		self.sizer.Add(messageSizer,0,wx.EXPAND)

		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		inputSizer.Fit(self)
		self.sizer.Fit(self)
	
		self.tw = twitter3.Twitter(twUserdata)
		self.tw.setAuthService("twitter")
		self.SetIcon(main_icon.getIcon())
		self.SetSize((300,400))
		self.timer = wx.Timer(self,self.TIMER_ID)
		wx.EVT_TIMER(self,self.TIMER_ID,self.OnUpdate)
		self.timer.Start(60000)
		
		self.timer11 = wx.Timer(self,self.TIMER_ID3+1)
		wx.EVT_TIMER(self,self.TIMER_ID3+1,self.OnUpdate2)
		self.timer11.Start(3000)

		self.timer2 = wx.Timer(self,self.TIMER_ID2)
		wx.EVT_TIMER(self,self.TIMER_ID2,self.OnReplyUpdate)
		self.timer2.Start(300000)
		
		self.timer3 = wx.Timer(self,self.TIMER_ID3)
		wx.EVT_TIMER(self,self.TIMER_ID3,self.OnDMUpdate)
		self.timer3.Start(300000)
		self.RefleshTw()

		self.replyPage.Reflesh()
		self.directPage.Reflesh()

		self.SetNowTime2StatusBar()
	
	def OnSendTW(self, event):
		# 送信する
		# コンボボックスの中身を空にする
		combo =	self.text 
		self.tw.put(combo.GetValue())	
		combo.SetValue("")
		self.RefleshTw()
	
	# チャットのログデータをListCtrlに表示
	def RefleshTw(self):
		self.recentPage.Reflesh()	
	
	def OnUpdate(self, event):
		self.SetStatusBar(u"新着取得中...")
		self.RefleshTw()
	
	def OnUpdate2(self, event):
		#self.SetStatusBar(u"新着取得中...")
		b1 = self.recentPage.CheckUpdate()
		for c in self.recentPage.customPages:
			b2 = self.recentPage.customPages[c].CheckUpdate()
		self.replyPage.CheckUpdate()
		self.directPage.CheckUpdate()
		if b1 == True:
			self.SetNowTime2StatusBar()

	def OnReplyUpdate(self, event):
	
		self.SetStatusBar(u"Reply取得中")
		self.replyPage.Reflesh()

	def OnDMUpdate(self, event):
		
		self.SetStatusBar(u"DM取得中...")
		self.directPage.Reflesh()

	def SetStatusBar(self,str):
		
		sb = wx.GetApp().GetTopWindow().GetStatusBar()
		sb.SetStatusText(str)
	def SetNowTime2StatusBar(self):
		#現在時刻を表示
		from time import localtime, strftime
		nowtime = strftime("%H:%M:%S", localtime())
		sb = wx.GetApp().GetTopWindow().GetStatusBar()
		sb.SetStatusText(nowtime+u"に更新しました")
	
	def myKeyHandler(self,evt):
		print evt.GetKeyCode(), 
		if self.selectedRow != -1:
			if evt.GetKeyCode() in [ord('k'),ord('K'),wx.WXK_UP]:
				print ('up')
				if self.selectedRow > 0:
		 			self.MoveList(self.selectedRow-1)
			if evt.GetKeyCode() in [ord('j'),ord('J'),wx.WXK_DOWN]:
				print ('down')
				if self.selectedRow < self.list.GetItemCount()-1:
					self.MoveList(self.selectedRow+1)
			if evt.GetKeyCode() in [ord('h'),ord('H'),wx.WXK_LEFT]:
				print ('left')
				leftcol = self.GetPrevItem(self.selectedRow)
				if leftcol != -1:
					self.MoveList(leftcol)
			if evt.GetKeyCode() in [ord('l'),ord('L'),wx.WXK_RIGHT]:
				print ('right')	
				rightcol = self.GetNextItem(self.selectedRow)
				if rightcol != -1:
					self.MoveList(rightcol)
			if evt.GetKeyCode() in [ord('s'),ord('S')]:
				print "S"
				#id = self.hiddenDataList[self.selectedRow][0]
				#print "fav"+id
				#self.tw.createFavorite(id)
		#print list.
		if evt.GetKeyCode() in [ord('q'), ord('Q')]:
			wx.Exit()

	"""Web上の画像を読み込みImageListとして保持する。
	   	既に読まれてるなら読みに行かない。ImageList['URL']という形で格納
	"""
	def GetImageListElement(self,url):
		unicodeUrl = url
		if self.imageList.has_key(unicodeUrl):
			if self.imageList[unicodeUrl] == "":
				return None 
			#self.userIcon.SetBitmap(self.imageList[unicodeUrl].ConvertToBitmap())
			return self.imageList[unicodeUrl]
		else:
			self.imageList[unicodeUrl] = "" 
			self.WebImage2StringIO(url,unicodeUrl)
		return None 
	
	# Web上の画像を引っ張ってくる
	def WebImage2StringIO(self,url,result):
		import urllib,sys

		try:

			#print "url:"+url
			urlName = urllib.quote_plus(url,':;/')
			t = ImageGetFrame(urlName,self.WebImageCallback,result,self.imageThreadLock)
			t.start()
			#t.run()
		except:
			print "urlquote error"

			#print "urlName:"+urlName

		#t.run()
		#except:
		#	print "WebImage2StringIO.error", sys.exc_info()[0]


	def WebImageCallback(self,imageData,result):
		from cStringIO import StringIO
		image_pil = Image.open(StringIO(imageData))
		image_pil.thumbnail((64,64))

		image_wx = wx.EmptyImage(image_pil.size[0],image_pil.size[1])
		image_wx.SetData(image_pil.convert('RGB').tostring())
		self.imageList[result] = image_wx
	
	# 画像を読み込んで表示のテスト
	def SetImage(self,imageName):
		bmp = self.userIcon
		image = self.GetImageListElement(imageName)
		if image != None: 
			bmp.SetBitmap(image.ConvertToBitmap())
	
	def addUser2Inputbox(self,user):
		
		text = self.text
		value = text.GetValue()
		
		flag = 1 
		import re
		print value + ":" + user
		if re.search(user,value):
			flag = 0

		if flag == 1:
			text.SetValue(user+value)

	def getNotebook(self):
		return self.notebook

# startup application.
if __name__=='__main__':
	app = wx.App(False)
	frame = MainFrame()
	app.SetTopWindow(frame)
	frame.Show()
	app.MainLoop()
