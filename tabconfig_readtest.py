#!/usr/bin/env python
# -*- coding: utf-8 -*-

import simplejson as json

def loadUserData(fileName):
    #ファイルを開いて、データを読み込んで変換する
    file = open(fileName,'r')
    a = json.read(file.read())
    file.close()
    return a
	#except:
	#	print "error:fileNotFound",fileName


twTabConfig = loadUserData("tabconfig")

