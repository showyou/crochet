#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys,os,time,re
import wx
import wx.lib.ClickableHtmlWindow
import main_icon
import urllib

import twitter3
import simplejson
import Image

import thread
import toDate
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

import configDialog
import config

"""自動で chdirし，working directory を crochet のあるディレクトリにする"""
dir = os.path.split(sys.argv[0])[0]
os.chdir(dir)

g_config = config.Config()
"""自動リサイズするListCtrl"""
class ListCtrlAutoWidth(wx.ListCtrl, ListCtrlAutoWidthMixin):
 	def __init__(self, parent):
 		wx.ListCtrl.__init__(self,parent,style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_SINGLE_SEL)
 		ListCtrlAutoWidthMixin.__init__(self)

"""タブ振り分けフィルタ"""
class BranchFilter():
	def __init__(self,tabName,idFilter,bodyFilter,
					moveFrom,searchBoth,regexEnable,setMark):
		self.tabName = tabName
		self.idFilter = idFilter
		if bodyFilter != "":
			if regexEnable == True: #正規表現あり
				try:
					self.bodyFilter = re.compile(bodyFilter)
				except:
					print "invalid bodyFilter %s" % bodyFilter
					self.bodyFilter = False
			else:
				self.bodyFilter = bodyFilter
		else:
				self.bodyFilter = False
		self.bodyF = bodyFilter
		self.moveFrom = moveFrom
		self.searchBoth = searchBoth
		self.regexEnable = regexEnable
		self.setMark = setMark
	""" 振り分け処理を行う。
		適合すれば振り分けタブ名を、失敗すれば空文字列を返す """
	def doFilter(self,id,body):
		matchFlag = False
		if self.idFilter != "" and self.idFilter == id:
			print "id hit",self.idFilter
			matchFlag = True
		elif self.bodyFilter:
			if self.regexEnable:
				if self.bodyFilter.search(body):
					matchFlag = True
			else:
				if body.find(self.bodyFilter) != -1:
					matchFlag = True
		if matchFlag == True:
			return self.tabName,self.moveFrom,self.setMark
		return "",False,False


"""リスト用画像リスト"""
class ListImageList(wx.ImageList):
	def __init__(self):
		wx.ImageList.__init__(self,16,16)
	def Add(self,imageUrl):
		imageData = urllib.urlopen(imageUrl).read()
		image_pil = Image.open(StringIO(imageData))
		image_pil.thumbnail((16,16))

		image_wx = wx.EmptyImage(image_pil.size[0],image_pil.size[1])
		image_wx.SetData(image_pil.convert('RGB').tostring())
		wx.ImageList.Add(self,image_wx.ConvertToBitmap())
		return self.GetImageCount()-1

"""wx.ImageListが辞書使えなさそうなので辞書使うためのプロキシクラス""" 
class ImageListProxy():
	def __init__(self):
		self.list = {}
		self.imageList = ListImageList()
	def GetIndex(self,imageName):
		if self.list.has_key(imageName):
			return self.list[imageName]
		else:
			try:
				p=self.imageList.Add(imageName)
				self.list[imageName]=p
			except:
				print "ILP Error"
				return -1
			return p

"""画像取得用スレッド"""
class ImageGetFrame(wx.Frame):
	def __init__(self,url,callbackFunc,result,lock):
		self.url = url 
		self.func = callbackFunc 
		self.result = result
		self.lock = lock
	def start(self):
		thread.start_new_thread(self.run, ())
		pass
	def run(self):
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
		#ここに通信処理を書く
		self.lock.acquire()
		#try:
		a = self.tw.get("")
		self.func(a)
		#except:
		#	print "Error:TwHttpFrame", sys.exc_info()[0]
		#finally:
		self.lock.release()
	def __del__(self):
		pass#print "delete HTTP Thread"	


try:
	import Growl
	g_growl = True

except:
	print "not exist:Growl sdk"
	g_growl = False

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
		self.selectedRow = 0
		self.title = title
		self.owner = parent
		self.lock = threadLock
		self.dataListLock = thread.allocate_lock() 
		wx.NotebookPage.__init__(self,parent.getNotebook(),-1)
		parent.getNotebook().AddPage(self,title)
		list = self.list = ListCtrlAutoWidth(self)
		list.Bind(wx.EVT_KEY_DOWN, self.myKeyHandler)
		list.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDoubleClick)

		a = self.imageListProxy = ImageListProxy()
		self.list.AssignImageList( a.imageList, wx.IMAGE_LIST_SMALL)	
		
		list.InsertColumn(0," ",1,20)
		list.InsertColumn(1,u"ユーザ")
		list.InsertColumn(2,u"発言",width=300)
		list.InsertColumn(3,u"時刻",width=60);
		list.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnTwitListSelect)
		
		if g_growl == True:
			self.g = parent.g
			self.img = parent.img
	def OnTwitListSelect(self,event):
		selectedRow = self.selectedRow = event.GetIndex()
		dataList = self.dataList
		label = self.owner.userName
		text = self.owner.messageText
		twittime = self.owner.twitTime
		mainText = dataList[selectedRow][2]
		mainText = mainText.replace("href=\"/","href=\"http://twitter.com/")

		""" 30文字折り返し"""

					
		#print "mainText",mainText
		
		text.SetValue(mainText)
		label.SetLabel(dataList[selectedRow][1])
		twittime.SetLabel(dataList[selectedRow][3])
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
				self.list.SetItemBackgroundColour(i,g_config['forMeColor'])

	def ResetCount(self):
		self.count = 0
	# 後で多分実装	
	def ChangeItemColour(self,index,data,re,color):
		pass	
	def OnDoubleClick(self,event):
		selectedRow = event.GetIndex()
		user = "@" + self.dataList[selectedRow][1] + ' '
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
	def CallGrowl(self,gtitle,gdescription,img=False):
		if( img != False ):
			self.g.notify(noteType='newTwit',title=gtitle,
					description=gdescription,icon = img,sticky=False)
		else:
			self.g.notify(noteType='newTwit',title=gtitle,
					description=gdescription,sticky=False)
	def RemoveATag(self,text):
		regATagBegin = re.compile("<a href=.*?>")
		text2 = regATagBegin.sub("",text)
		text3 = text2.replace("</a>","")
		return text3	
	def InsertData(self,data,hiddenData):
		#print ("start insert data")
		i = self.count
		#ここでロック
		self.dataListLock.acquire()
		self.tmpDataList.insert(i,data)# + self.dataList
		self.tmpHiddenDataList.insert(i,hiddenData)# + self.hiddenDataList
		self.dataListLock.release()
		#ここでアンロック
		self.count += 1

		#print ("end insert data")
	#InsertDataで追加されてるかどうか確認して、あればリストに入れる
	def CheckUpdate(self):
		self.dataListLock.acquire()
		if len(self.tmpDataList) < 1 or len(self.tmpHiddenDataList) < 1:
			self.dataListLock.release()
			return False

		user = self.owner.tw.user['user']
		i = 0
		for b in self.tmpDataList:
	
			self.list.InsertStringItem(i,"")
			b2 = []
			b2.append(b[0])
			b2.append(b[1])
			b2.append(self.RemoveATag(b[2]))
			b2.append(b[3]);
			for j in range(4):
				self.list.SetStringItem(i,j,b2[j])
		
			if re.match(user,b[1]):
				self.list.SetItemBackgroundColour(i,g_config['mycolor'])

			if re.search(user,b[2]):
				self.list.SetItemBackgroundColour(i,g_config['forMeColor'])
		
			#import time
			#time.sleep(1)		
			#if 先読み=on
			#try:	
			"""リストに画像入れて割り当てる"""
			try:
				"""ToDo:ここで負荷がかかっているので、
					スレッドに分けるとか64x64のリストとうまく兼用できないのか"""
				if(g_config['listIcon']):
					imageIndex = self.imageListProxy.GetIndex(b[4])
					if( imageIndex != -1):self.list.SetStringItem(i,0,"", imageIndex)
			except:
				print "Error:smallImage"

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
		self.list.Refresh()
		self.selectedRow+=i
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
class RecentPage(TmpTwitPage):
	def __init__(self, parent,threadLock,filter):
		TmpTwitPage.__init__(self,u"最新",parent,threadLock)

		self.customPages = {}# フィルタリングページの固まり？
		self.filter = filter

	def ResetCount(self):
		TmpTwitPage.ResetCount(self)		
		for p in self.customPages:
			self.customPages[p].ResetCount()
	
	def AppendCustomPage(self, customPage,customPageId):
		self.customPages[customPageId] = customPage

	def Refresh(self):
		t = TwHttpFrame(self.owner.tw,self.RefreshList,self.lock)
		#t.start()
		t.run()
	def RefreshList(self,a):
		#print "start recent:refreshList" 
		#lockかけた方がいいのかも。。
		self.ResetCount()

		outString = ""
		outCount = 0
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
				x2 = "--"
				#x2 = toDate.toDate(x[2],g_config["timestring_twitter_api"]).strftime("%b %d %H:%M:%S")
				dataListElement.append(x2)
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
				
				moveFrom = False 
				for f in self.filter:
					tabName,moveFrom,setMark = f.doFilter(x[0],x[1]) 
					if tabName != "":
						print "tabHit",tabName,x[1]
						self.customPages[tabName].InsertData(dataListElement,hiddenDataListElement)
						break
				#print ("x3-1")	
				if moveFrom == False:
					self.InsertData(dataListElement,hiddenDataListElement)

				#print ("x3-2"),	
				if g_growl == True:
					outCount += 1
					x[1]= self.RemoveATag(x[1])
					outString += x[0]+" : "+x[1]+"\n"

		user = self.owner.tw.user['user']
		if g_growl == True and g_config['popup'] and outCount > 0:
			if outString.find("@"+user) != -1:
				TmpTwitPage.CallGrowl(self,"Recent 新着"+str(outCount)+"件",
					outString,self.img)
			else:
				TmpTwitPage.CallGrowl(self,"Recent 新着"+str(outCount)+"件",outString)

class ReplyPage(TmpTwitPage):

	def __init__(self, parent,threadLock):
		TmpTwitPage.__init__(self,"Re",parent,threadLock)
		#self.dataList = []
		#self.hiddenDataList = []
	
	def Refresh(self):
		t = TwReplyHttpFrame(self.owner.tw,self.RefreshList,self.lock)
		t.start()
			
	def RefreshList(self,a):
		#lockかけた方がいいのかも。。
		self.ResetCount()
		outCount = 0
		outString = ""
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
				#x2 = toDate2.toDate2(x[2]).strftime("%y-%m-%d %H:%M:%S")
				x2 = "--"

				dataListElement.append(x2)
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
	
				self.InsertData(dataListElement,hiddenDataListElement)	

				if g_growl == True:
					outCount += 1
					x[1]= self.RemoveATag(x[1])
					outString += x[0]+" : "+x[1]+"\n"

		if g_growl == True and g_config['popup']:
			if(outCount > 0):
				TmpTwitPage.CallGrowl(self,"Reply 新着"+str(outCount)+"件",
					outString,self.img)

class DMPage(TmpTwitPage):

	def __init__(self, parent,threadLock):
		TmpTwitPage.__init__(self,"DM",parent,threadLock)
		dataList = []
	def Refresh(self):
		t = TwDMHttpFrame(self.owner.tw,self.RefreshList,self.lock)
		t.start()

	def RefreshList(self,a):
		#lockかけた方がいいのかも。。
		self.ResetCount()
		user = self.owner.tw.user['user']
		outCount = 0
		outString = ""
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
				#x2 = toDate2.toDate2(x[2]).strftime("%y-%m-%d %H:%M:%S")
				x2 = "--"
				dataListElement.append(x2)
				dataListElement.append(x[3])

				hiddenDataListElement = []
				hiddenDataListElement.append(x[4])#発言id
	
				self.InsertData(dataListElement,hiddenDataListElement)	

				if g_growl == True:
					outCount += 1
					x[1]= self.RemoveATag(x[1])
					outString += x[0]+" : "+x[1]+"\n"

		if g_growl == True and g_config['popup']:
			if(outCount > 0):
				TmpTwitPage.CallGrowl(self,"DM 新着"+str(outCount)+"件",
					outString,self.img)

class TwitHtml(wx.lib.ClickableHtmlWindow.PyClickableHtmlWindow):
	def __init__(self, parent):
		wx.lib.ClickableHtmlWindow.PyClickableHtmlWindow.__init__(self,parent,-1,size=(90,50),style=wx.VSCROLL)

	def SetValue(self, text):
		self.SetPage(text)
		pass


from time import localtime, strftime
from cStringIO import StringIO
import wx.aui
class MainFrame(wx.Frame):
	"""MainFrame class deffinition.
	"""

	TIMER_ID = 1
	TIMER_ID2= TIMER_ID+1
	TIMER_ID3= TIMER_ID2+1
	
	ID_MNU_VIEW_POPUP = 100
	ID_MNU_VIEW_LISTICON = 101
	imageList = {}
	t = {}
	def loadUserData(self, fileName):
		#ファイルを開いて、データを読み込んで変換する
		#データ形式は(user,password)
		#try
		file = open(fileName,'r')
		a = simplejson.loads(file.read())
		file.close()
		return a
		#catch exit(1)
		
	def __init__(self, parent=None):
		#from pit import Pit
		#twUserdata = Pit.get('twitter.com',{'require' : {'user':'','pass':''}})
		try:
			twUserdata = self.loadUserData(".chat/twdata")
		except:
			twUserdata = configDialog.ConfigDialog(None, -1, 'crochet config').GetAccount()
			if twUserdata["user"] and twUserdata["pass"]:
				file = open(".chat/twdata","w")
				file.write("{\"user\":\""+twUserdata["user"]+
					   "\",\"pass\":\""+twUserdata["pass"]+"\"}\n")
				file.close()
			else:
				exit(1)
		twTabConfig = self.loadUserData(".chat/tabconfig")

		wx.Frame.__init__(self,None, -1, "crochet")
		
		if g_growl == True:
			self.g = Growl.GrowlNotifier(
				applicationName='crochet',notifications=['newTwit','newReply'])
			self.g.register()
			self.img = Growl.Image.imageFromPath('reply.png')	
		self.CreateStatusBar()

		self.selectedRow = -1
		text = self.text = wx.TextCtrl(self,-1,style=wx.TE_PROCESS_ENTER)
		text.Bind(wx.EVT_TEXT_ENTER, self.OnSendTW)
		button = self.button = wx.Button(self, -1, "Send")
		self.button.Bind(wx.EVT_BUTTON, self.OnSendTW) 
	
		notebook = self.notebook = wx.aui.AuiNotebook(self,-1,style=wx.aui.AUI_NB_BOTTOM|wx.aui.AUI_NB_WINDOWLIST_BUTTON|wx.aui.AUI_NB_TAB_SPLIT)

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

		#messageText=self.messageText = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_READONLY,size=(-1,65))
		messageText = self.messageText = TwitHtml(self)
		userIcon = self.userIcon = wx.StaticBitmap(self,-1,wx.NullBitmap,(0,0),(64,64))
		userName = self.userName = wx.StaticText(self,-1,"test")
		twitTime = self.twitTime = wx.StaticText(self,-1,"---")
		
		messageSizer3 = wx.BoxSizer(wx.HORIZONTAL)
		messageSizer3.Add(userName,2,wx.EXPAND)
		messageSizer3.Add(twitTime,3,wx.EXPAND,wx.ALIGN_RIGHT)

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
		self.SetSize((600,400))
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
		
		self.RefreshTw()
		self.replyPage.Refresh()
		self.directPage.Refresh()

		self.SetNowTime2StatusBar()
		self.CreateMenu()	
	def CreateMenu(self):
		#表示メニュー項目作る
		viewMenu = wx.Menu()
		self.popupCheck = viewMenu.Append(self.ID_MNU_VIEW_POPUP,u"新着通知",u"新着表示",kind = wx.ITEM_CHECK)
		self.listIconCheck = viewMenu.Append(self.ID_MNU_VIEW_LISTICON,u"リストアイコン",u"リストボックスの横のアイコンの表示／非表示を切り替えます",kind=wx.ITEM_CHECK)

		viewMenu.Check(self.ID_MNU_VIEW_POPUP, g_config['popup'])
		menuBar = wx.MenuBar()
		menuBar.Append(viewMenu,u"表示")

		wx.EVT_MENU(self, self.ID_MNU_VIEW_POPUP, self.OnMenuViewPopUp_Click)
		wx.EVT_MENU(self, self.ID_MNU_VIEW_LISTICON, self.OnMenuViewListIcon_Click)
		self.SetMenuBar(menuBar)

	def OnMenuViewPopUp_Click(self,e):
		g_config['popup'] = self.popupCheck.IsChecked();

	def OnMenuViewListIcon_Click(self,e):
		g_config['listIcon'] = self.listIconCheck.IsChecked();

	def OnSendTW(self, event):
		# 送信する
		# コンボボックスの中身を空にする
		combo =	self.text 
		self.tw.put(combo.GetValue())	
		combo.SetValue("")
		self.RefreshTw()
	
	# チャットのログデータをListCtrlに表示
	def RefreshTw(self):
		self.recentPage.Refresh()	
	
	def OnUpdate(self, event):
		self.SetStatusBar(u"新着取得中...")
		self.RefreshTw()
	
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
		self.replyPage.Refresh()

	def OnDMUpdate(self, event):
		
		self.SetStatusBar(u"DM取得中...")
		self.directPage.Refresh()

	def SetStatusBar(self,str):
		#print ("setstatusbar"+str,)	
		sb = wx.GetApp().GetTopWindow().GetStatusBar()
		sb.SetStatusText(str)

	def SetNowTime2StatusBar(self):
		#現在時刻を表示

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
			return self.imageList[unicodeUrl]
		else:
			self.imageList[unicodeUrl] = "" 
			self.WebImage2StringIO(url,unicodeUrl)
		return None 
	
	# Web上の画像を引っ張ってくる
	def WebImage2StringIO(self,url,result):

		try:
			urlName = urllib.quote_plus(url,':;/')
			t = ImageGetFrame(urlName,self.WebImageCallback,result,self.imageThreadLock)
			t.start()
			#t.run()
		except:
			print "urlquote error"
			#print "urlName:"+urlName

	def WebImageCallback(self,imageData,result):
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
