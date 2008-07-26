# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   23-Mar-2006
# Last mod.         :   26-Jul-2008
# -----------------------------------------------------------------------------

import os, sys, StringIO
try:
	import kiwi.main as kiwi
except ImportError:
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
		if not os.path.exists(path):
			self.site.error("Included file not found: "+ path)
		if kiwi:
			_, r = kiwi.run("-m --body-only " + path, noOutput=True)
			return r
		else:
			self.site.warn("Kiwi is not available, but you used the $site.kiwi function")
			self.site.info("You can get Kiwi from <http://www.ivy.fr/kiwi>")
			return path

	def process( self, text, level=0 ):
		"""If Kiwi is available, the given text will be interpreted as Kiwi
		markup and HTML will be generated from it. If Kiwi is not available, a
		warning will be issued, and the text will be displayed as-is."""
		if kiwi:
			try:
				s = StringIO.StringIO(text)
				_, r = kiwi.run("-m --body-only --level=%s --" % (level), s, noOutput=True)
				s.close()
				return r
			except:
				self.site.error("Can't process kiwi markup in file %s" % self.site.page)
				raise
		else:
			self.site.warn("Kiwi is not available, but you used the $site.kiwi function")
			info("You can get Kiwi from <http://www.ivy.fr/kiwi>")
			return text

	def __call__( self, text, level=0 ):
		return self.process(text,level)

# EOF
