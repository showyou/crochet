#!/usr/bin/env python
# -*- coding: utf-8 -*-
import twitter3

userData = {"user":'showyou',"pass":"yoshinosakura"}
tw = twitter3.Twitter(userData)
#tw.setAuthService("twitter")
print tw.get("")
