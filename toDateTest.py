#!/usr/bin/env python
# -*- coding:utf-8 -*-
import toDate,datetime

date = "2008-02-24T06:39:37+00:00"
apiDate = "Thu Jan 22 05:19:28 +0000 2009" 
apiFormat = "%a %b %d %H:%M:%S +0000 %Y"
scrapingFormat = "%Y-%m-%dT%H:%M:%S+00:00"
print toDate.toDate(apiDate,apiFormat)
print datetime.datetime.today()
	

