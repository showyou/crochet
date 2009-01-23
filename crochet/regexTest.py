#!/usr/bin/env python
# -*- coding: utf-8 -*-
userData = {}
userData['user'] = ''
userData['pass'] = ''
import twitter3
tw = twitter3.Twitter(userData)
tw.setAuthService("twitter")
print tw.getWithScraping("") 
