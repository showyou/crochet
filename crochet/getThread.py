# -*- coding: utf-8 -*-
from threading import Thread

import twitter2
import inachat2
import json

class TwGetThread(Thread):
	# userdata 認証用情報
	# output 出力先
	# name 名前
	def __init__(self,userdata,output,name):
		self.tw = twitter2.Twitter(userdata)
		self.name = name
		self.output = output
		Thread.__init__(self)
	def run(self):
		a = self.tw.get(self.name)
		#a = self.tw.get("showyou")
		allString = ""
		for x in a:
			string = ""
			for y in x:
				string += y +" "
			allString = allString + string +"\n"
		#print(allString)
		self.output.SetValue("")
		self.output.SetValue(allString)

#def loadUserData(fileName):
#	#try
#	file = open(fileName,'r')
#	a = json.read(file.read())
#	file.close()
#	return a

#if __name__=='__main__':
#	a = "a"
#	twUserdata = loadUserData(".chat/twdata")
#	t = TwGetThread(twUserdata,a,name)
#	t.start()
#	for i in range(10):
#		print('a')
#		if t.isAlive() == True:
#			continue
#		t = TwGetThread(twUserdata,a,name)
#		t.start()
#		t.join()
#	raw_input()