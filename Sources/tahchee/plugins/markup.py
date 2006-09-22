# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   23-Mar-2006
# Last mod.         :   13-Jul-2006
# -----------------------------------------------------------------------------

import os, sys, StringIO
try:
	import kiwi.main as kiwi
except ImportError e:
	import _kiwi.main as kiwi

NAME    = "kiwi"
VERSION = None
SUMMARY = "Kiwi markup to HTML conversion functions."

class KiwiPlugin:

	def __init__( self, site ):
		self.site = site

	def name( self ): return NAME
	def summary( self ): return SUMMARY
	def version( self ): return VERSION
	def doc( self ): return __doc__

	def install( self, localdict ):
		localdict["kiwi"] = self
	
	def include( self, path ):
		if not path[0] == "/":
			path = self.site.pagesDir + "/" + path
		if kiwi:
			_, r = kiwi.run("-m --body-only " + path, noOutput=True)
			return r
		else:
			warn("Kiwi is not available, but you used the $site.kiwi function")
			info("You can get Kiwi from <http://www.ivy.fr/kiwi>")
			return path

	def process( self, text ):
		"""If Kiwi is available, the given text will be interpreted as Kiwi
		markup and HTML will be generated from it. If Kiwi is not available, a
		warning will be issued, and the text will be displayed as-is."""
		if kiwi:
			s = StringIO.StringIO(text)
			_, r = kiwi.run("-m --body-only --", s, noOutput=True)
			s.close()
			return r
		else:
			warn("Kiwi is not available, but you used the $site.kiwi function")
			info("You can get Kiwi from <http://www.ivy.fr/kiwi>")
			return text
	
	def __call__( self, text ):
		return self.process(text)
# EOF
