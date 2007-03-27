# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   27-Mar-2007
# Last mod.         :   27-Mar-2007
# -----------------------------------------------------------------------------

import re, string, htmlentitydefs

NAME    = "escape"
VERSION = None
SUMMARY = """Escapes a string so that it can be safely included into an HTML \
document."""

class EscapePlugin:

	def __init__( self, site ):
		self.site = site

	def name( self ): return NAME
	def summary( self ): return SUMMARY
	def version( self ): return VERSION
	def doc( self ): return __doc__

	def install( self, localdict ):
		localdict["escape"] = self

	def toHTML( self, text ):
		"Returns the given HTML with ampersands, quotes and carets encoded"
		# NOTE: This is ripped from Django utils.html module
		if not isinstance(text, basestring):
			text = str(text)
		return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

	def toText( self, text ):
		"""Expands the entities found in the given text and returns it as text."""
		# NOTE: This is based on
		# <http://www.shearersoftware.com/software/developers/htmlfilter/>
		entityStart = text.find('&')
		if entityStart != -1:          # only run bulk of code if there are entities present
			preferUnicodeToISO8859 = 1 #(outputEncoding is not 'iso-8859-1')
			prevOffset = 0
			textParts = []
			while entityStart != -1:
				textParts.append(text[prevOffset:entityStart])
				entityEnd = text.find(';', entityStart+1)
				if entityEnd == -1:
					entityEnd = entityStart
					entity = '&'
				else:
					entity = text[entityStart:entityEnd+1]
					if len(entity) < 4 or entity[1] != '#':
						entity = htmlentitydefs.entitydefs.get(entity[1:-1],entity)
					if len(entity) == 1:
						if preferUnicodeToISO8859 and ord(entity) > 127 and hasattr(entity, 'decode'):
							entity = entity.decode('iso-8859-1')
					else:
						if len(entity) >= 4 and entity[1] == '#':
							if entity[2] in ('X','x'):
								entityCode = int(entity[3:-1], 16)
							else:
								entityCode = int(entity[2:-1])
							if entityCode > 255:
								entity = unichr(entityCode)
							else:
								entity = chr(entityCode)
								if preferUnicodeToISO8859 and hasattr(entity, 'decode'):
									entity = entity.decode('iso-8859-1')
					textParts.append(entity)
				prevOffset = entityEnd+1
				entityStart = text.find('&', prevOffset)
			textParts.append(text[prevOffset:])
			text = ''.join(textParts)
		return text

	def __call__( self, text ):
		return self.toHTML(text)

# EOF
