# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   14-Mar-2008
# Last mod.         :   14-Mar-2008
# -----------------------------------------------------------------------------

import os, sys, StringIO
try:
	import pamela.engine as pamela
except ImportError:
	import _pamela.engine as pamela

NAME    = "pamela"
VERSION = None
SUMMARY = "Pamela markup to HTML conversion functions."

class PamelaPlugin:

	def __init__( self, site ):
		self.site = site

	def name( self ): return NAME
	def summary( self ): return SUMMARY
	def version( self ): return VERSION
	def doc( self ): return __doc__

	def install( self, localdict ):
		localdict["pamela"] = self
	
	def include( self, path ):
		if not path[0] == "/":
			path = self.site.pagesDir + "/" + path
		if pamela:
			r = pamela.run(path)
			return r
		else:
			self.site.warn("Pamela is not available, but you used the $site.pamela function")
			self.site.info("You can get Kiwi from <http://www.ivy.fr/pamela>")
			return path

	def process( self, text ):

		if pamela:
			try:
				return pamela.Parser().parseText(text)
			except Exception, e:
				self.site.error("Can't process pamela markup " + str(e))
				raise
		else:
			self.site.warn("Pamela is not available, but you used the $site.pamela function")
			info("You can get Pamela from <http://www.ivy.fr/pamela>")
			return text

	def __call__( self, text):
		return self.process(text)

# EOF
