from bbfreeze import Freezer
f = Freezer("dist")
f.addScript("chat_allsrc.py",True)

f()

