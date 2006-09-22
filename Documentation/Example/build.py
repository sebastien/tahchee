#!/usr/bin/env python
import os, sys
# We add the Plugins path to the current Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Plugins"))
try:
	from tahchee.main import *
except:
	print "Unable to import Tahchee."
	print "Please check that the 'tahchee' module is in your PYTHONPATH"
	sys.exit(-1)
# You can change the following things
# =============================================================================
URL       = "http://www.mysite.org"
IGNORES   = (".cvs", ".CVS", ".svn", ".DS_Store")
INDEXES   = ("index.*")
MAIN      = "index.html"
SHOW_MAIN = True
# =============================================================================
# Do not modify this code
if __name__ == "__main__":
	print "tahchee v." + version()
	site = Site(URL, locals=locals())
	if len(sys.argv)>1 and sys.argv[1].lower()=="remote": site.setMode("remote")
	SiteBuilder(site).build(filter(lambda x:x not in ('local','remote'),sys.argv[1:]))
