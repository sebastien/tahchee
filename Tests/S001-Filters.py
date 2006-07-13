#!/usr/bin/env python
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project   : Tahchee
# -----------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../Sources")
from tahchee.main import Site

__doc__ = "Ensures that the units are properly parsed."


INDEXES = ("index.*", "pouet.php", "hello.world")
VALID   = (
	"index.htm", "index.html", "pouet.php", "hello.world", "index.py",
	"hello/index.htm", "hello/index.html", "hello/pouet.php", "hello/hello.world", "hello/index.py",
	"/index.htm", "/index.html", "/pouet.php", "/hello.world", "/index.py",
	"./index.htm", "./index.html", "./pouet.php", "./hello.world", "./index.py",
)
INVALID = ( "_index.htm", "windex.html", "xpouet.php", "hello.wrld")


if __name__ == "__main__":
	root = __file__ + ".test"
	if os.path.exists(root): os.rmdir(root)
	os.mkdir(root)
	s = Site("http://www.pouet.org", root=root, indexes=INDEXES)
	print "Checking indexes:"
	for path in VALID:
		print " - ", path
		assert s.isIndex(path), path
	print "Checking not indexes:"
	for path in INVALID:
		print " - ", path
		assert not s.isIndex(path), path
	print "OK"

# EOF
