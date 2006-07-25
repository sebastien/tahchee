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
assert builder.hasChanged(__file__) == builder.hasChanged(__file__) ==  builder.hasChanged(__file__)

# EOF
