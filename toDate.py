#! /usr/bin/env python
# -*- coding:utf-8 -*-
import datetime

"""
地域に応じた時差を返す
日本だと+9時間(JST)
GSTなら0かしら？
ニューヨークなら9-14 = -5?
サンフランシスコ 9-17 = -8?
"""
def getLocalTime(timezoneName):
	if timezoneName == "JP":
		return 9
	else:
		return 0

def toDate(date,str):
	from time import strptime
	for i in range(len(date)):
		print ord(date[i]),
	print ""
	dates = strptime(date,str)
	dt = datetime.datetime(*dates[0:7])+datetime.timedelta(hours=getLocalTime("JP"))
	
	return dt

