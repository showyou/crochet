#!/usr/bin/local/python
# -*- coding: utf-8 -*-

# Module: wx_utils.py
# Author: Noboru Irieda(Handle Name NoboNobo)
# Contact: admin@python.matrix.jp
# Copyright: This module has been placed in the public domain.

import sys
import os
import imp

if hasattr(sys,"setdefaultencoding"):
    sys.setdefaultencoding("utf-8")

def is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze

def executable():
    if is_frozen():
        return os.path.abspath(sys.executable)
    return os.path.abspath(sys.argv[0])

import wx
import wx.xrc
from wx.xrc import XRCCTRL, XRCID
XRC = wx.xrc.XmlResource.Get

def XrcInit():
  if is_frozen():
    import resource
    resource.InitXmlResource()
  else:
    XRC().Load('chat.xrc')

def manifest(app_name):
  os.system('pywxrc -p chat.xrc')
  return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
  <assembly xmlns="urn:schemas-microsoft-com:asm.v1"
  manifestVersion="1.0">
  <assemblyIdentity
      version="0.64.1.0"
      processorArchitecture="x86"
      name="Controls"
      type="win32"
  />
  <description>%s</description>
  <dependency>
      <dependentAssembly>
          <assemblyIdentity
              type="win32"
              name="Microsoft.Windows.Common-Controls"
              version="6.0.0.0"
              processorArchitecture="X86"
              publicKeyToken="6595b64144ccf1df"
              language="*"
          />
      </dependentAssembly>
  </dependency>
  </assembly>
  """ % app_name

class ImmutableDict(dict):
    '''A hashable dict.'''

    def __init__(self,*args,**kwds):
        dict.__init__(self,*args,**kwds)
    def __setitem__(self,key,value):
        raise NotImplementedError, "dict is immutable"
    def __delitem__(self,key):
        raise NotImplementedError, "dict is immutable"
    def clear(self):
        raise NotImplementedError, "dict is immutable"
    def setdefault(self,k,default=None):
        raise NotImplementedError, "dict is immutable"
    def popitem(self):
        raise NotImplementedError, "dict is immutable"
    def update(self,other):
        raise NotImplementedError, "dict is immutable"
    def __hash__(self):
        return hash(tuple(self.iteritems()))

class bind_manager:
  binds = {}
  def __init__(self):
    self.binds[hash(self)] = set()

  def __call__(self, *args, **keys):
    def deco(func):
      self.binds[hash(self)].add((func.func_name, args, ImmutableDict(keys)))
      return func
    return deco

  def bindall(self, obj):
    for func_name, args, keys in self.binds[hash(self)]:
      keys = dict(keys)
      if keys.has_key('event'):
        event = keys['event']
        del keys['event']
      else:
        event = args[0]
        args = list(args[1:])
      control = obj
      if keys.has_key('id'):
        if isinstance(keys['id'], str):
          keys['id'] = XRCID(keys['id'])
      if keys.has_key('control'):
        control = keys['control']
        if isinstance(control, str):
          control = XRCCTRL(obj, control)
        del keys['control']
      control.Bind(event, getattr(obj, func_name), *args, **keys)