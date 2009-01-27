# -*- coding: utf-8 -*-
import cPickle as pickle 
import wx

class Config():
	def __init__(self):
		self.Load()
		pass
	
	def LoadDefaults(self):
		self.d = {}
		self.d['mycolor'] = wx.Color(240,248,255)
		self.d['forMeColor'] = wx.Color(255,153,153)
		self.d['listIcon'] = False
		self.d['popup'] = True
		self.d['narrowmsg'] = True
		self.d['timestring_twitter_api'] = "%a %b %d %H:%M:%S +0000 %Y"
		self.d['timestring_twitter_friend_scraping'] = "%Y-%m-%dT%H:%M:%S+00:00"

	def Load(self):
		try:
			file = open(".chat/config","r")
			self.d = pickle.load(file)
			file.close()
		except:
			print ("config file not exist: create config file")
			self.LoadDefaults()
			self.Save()


	def Save(self):
		
		wfile = open(".chat/config","w")	
		pickle.dump(self.d, wfile)
		wfile.close()
		#except:
		#	print ("write config error")

	def __getitem__(self,key):
		return self.d[key]

	def __setitem__(self,key,item):
		self.d[key] = item
