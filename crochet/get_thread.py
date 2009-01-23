# -*- coding: utf-8 -*-
from threading import Thread

class TwGetThread(Thread):
	# userdata 認証用情報
	# output 出力先
	# name 名前
	def __init__(self,userdata,output,name)
		self.tw = twitter.Twitter(userdata)
	def run(self):
		self.tw.get(name.GetValue())

		allString = ""
		for x in a:
			string = ""
			for y in x:
				string += y +" "
			allString = allString + string +"\n"
		output.SetValue(allString)

class KchatGetThread(Thread):
	# userdata 認証用情報
	# output 出力先
	def __init__(self,userdata,output)
		self.kchat = inaChat2.InaChat(userdata)
	def run(self):
		pass
