#!/usr/bin/env python
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project   : Tahchee
# -----------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../Sources")
from tahchee.main import Site
from tahchee.plugins.linking import LinkingPlugin

__doc__ = "Ensures that the units are properly parsed."


LINKS = (
	(""           , "",   "/"),
	("/"          , "",   "/"),
	(""           , "/",  "/"),
	("/"          , "/",  "/"),
	("."          , "",   "/"),
	(""           , ".",  "/"),
	("."          , ".",  "/"),
	("/"          , ".",  "/"),
	("."          , "/",  "/"),

	("/index.html", "/index.html", "index.html"),
	("/index.html", "index.html", "index.html"),
	("/index.html", "./index.html", "index.html"),

	("index.html", "/index.html", "index.html"),
	("index.html", "index.html", "index.html"),
	("index.html", "./index.html", "index.html"),

	("./index.html", "/index.html", "index.html"),
	("./index.html", "index.html", "index.html"),
	("./index.html", "./index.html", "index.html"),

	("index.html", "index.html", "index.html"),
	("pages/index.html", "index.html", "../index.html"),
	("pages/other/index.html", "./index.html", "../../index.html"),

	("index.html", "pages/index.html", "pages/index.html"),
	("index.html", "pages/other/index.html", "pages/other/index.html"),

	("pages/index.html", "pages/index.html", "index.html"),
	("pages/index.html", "pages/other/index.html", "other/index.html"),
	("pages/index.html", "pages/other/pouet/index.html", "other/pouet/index.html"),

	("pouet/index.html", "pages/index.html", "../pages/index.html"),
	("pouet/index.html", "pages/other/index.html", "../pages/other/index.html"),
	("pouet/index.html", "pages/other/pouet/index.html", "../pages/other/pouet/index.html"),

)

if __name__ == "__main__":
	root = __file__ + ".test"
	if os.path.exists(root): os.rmdir(root)
	os.mkdir(root)
	s = Site("http://www.pouet.org", root=root)
	l = LinkingPlugin(s)
	for src, dst, expected in LINKS:
		res = l.link(src, dst, checkLink=False)
		print "Checking link('%s', '%s') = '%s' ? '%s'" % (src, dst, res, expected )
		assert expected == res
	print "OK"

# EOF
