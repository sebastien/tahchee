#!/usr/bin/env python
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project   : Tahchee
# -----------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../Sources")
from tahchee.main import Site, SiteBuilder

site = Site(None)
builder = SiteBuilder(site)
a = builder.hasChanged(__file__)
b = builder.hasChanged(__file__)
c = builder.hasChanged(__file__)
d = builder.hasChanged(os.path.abspath(__file__))
print a
print b
print c
print d

assert a == b == c == d == True
builder.changed  = {}
a = builder.hasChanged(__file__)
b = builder.hasChanged(__file__)
c = builder.hasChanged(__file__)
d = builder.hasChanged(os.path.abspath(__file__))

print a
print b
print c
print d
assert a == b == c == d == False

print "OK"
# EOF
