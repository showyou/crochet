#!/usr/bin/env python
# -*- coding: utf-8 -*-
import twitter3

userData = {}
userData['user'] = ''
userData['pass'] = ''
tw = twitter3.Twitter(userData)
tw.setAuthService("twitter")
print tw.get("")
