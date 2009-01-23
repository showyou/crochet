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
	import time
	dates = time.strptime(date,str)
	dt = datetime.datetime(dates[0],dates[1],dates[2],dates[3],dates[4],dates[5],dates[6])+datetime.timedelta(hours=getLocalTime("JP"))
	
	return dt

if __name__ == "__main__":
	date = "2008-02-24T06:39:37+00:00"
	apiDate = "Thu Jan 22 05:19:28 +0000 2009" 
	apiFormat = "%a %b %d %H:%M:%S +0000 %Y"
	scrapingFormat = "%Y-%m-%dT%H:%M:%S+00:00"
	print toDate(apiDate,apiFormat)
	print datetime.datetime.today()
	
