# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Joerg Zinke                           <umaxx@oleco.net>
#                       Sebastien Pierre                      <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   29-Jan-2007
# Last mod.         :   31-Oct-2007
# -----------------------------------------------------------------------------

import os, sys, StringIO

try:
	from docutils import core, io
except ImportError:
	core = io = None

NAME	= "rest"
VERSION = None
SUMMARY = "reStructuredText to HTML conversion functions."

class RestPlugin:

	DEFAULT_ENCODING = "iso-8859-1"
	DEFAULT_OUTPUT_ENCODING = "iso-8859-1"

	def __init__( self, site ):
		self.site = site

	def name(self): return NAME
	def summary(self): return SUMMARY
	def version(self): return VERSION
	def doc(self): return __doc__

	def install(self, localdict):
		localdict["rest"] = self

	def __html_body(self, input_string, source_path=None, destination_path=None,
				input_encoding='unicode', output_encoding='unicode',
				doctitle=1, initial_header_level=1):
		"""
		Given an input string, returns an HTML fragment as a string.

		The return value is the contents of the <body> element.

		Parameters:

		- `input_string`: A multi-line text string; required.
		- `source_path`: Path to the source file or object.  Optional, but useful
		  for diagnostic output (system messages).
		- `destination_path`: Path to the file or object which will receive the
		  output; optional.  Used for determining relative paths (stylesheets,
		  source links, etc.).
		- `input_encoding`: The encoding of `input_string`.  If it is an encoded
		  8-bit string, provide the correct encoding.  If it is a Unicode string,
		  use "unicode", the default.
		- `doctitle`: Disable the promotion of a lone top-level section title to
		  document title (and subsequent section title to document subtitle
		  promotion); enabled by default.
		- `initial_header_level`: The initial level for header elements (e.g. 1
		  for "<h1>").

		- `output_encoding`: The desired encoding of the output.  If a Unicode
		  string is desired, use the default value of "unicode" .
		"""
		overrides = {
			'input_encoding': input_encoding,
			'doctitle_xform': doctitle,
			'initial_header_level': initial_header_level
		}
		parts = core.publish_parts(
			source=input_string, source_path=source_path,
			destination_path=destination_path,
			writer_name='html', settings_overrides=overrides)
		fragment = parts['html_body']
		if output_encoding != 'unicode':
			fragment = fragment.encode(output_encoding)
		return fragment

	def include(self, path, encoding=None):
		encoding = encoding or self.DEFAULT_ENCODING
		outputEncoding = outputEncoding or self.DEFAULT_OUTPUT_ENCODING
		if not path[0] == "/":
			path = self.site.pagesDir + "/" + path
			r = self.__html_body(input_string=unicode(text, encoding), source_path=path, output_encoding=outputEncoding)
			return r
		else:
			self.site.warn("Docutils are not available, but you used the $site.rest function")
			self.site.info("You can get Docutils from <http://docutils.sourceforge.net/>")
			return path

	def process(self, text, encoding=None, outputEncoding=None):
		"""If docutils are available, the given text will be interpreted as rest
		markup and HTML will be generated from it. If docutils are not available, a
		warning will be issued, and the text will be displayed as-is."""
		encoding = encoding or self.DEFAULT_ENCODING
		outputEncoding = outputEncoding or self.DEFAULT_OUTPUT_ENCODING
		if core and io:
			r = self.__html_body(input_string=unicode(text, encoding), output_encoding=outputEncoding)
			return r
		else:
			self.site.warn("Docutils are not available, but you used the $site.rest function")
			self.site.info("You can get Docutils from <http://docutils.sourceforge.net/>")
			return text

	def __call__(self, text, encoding=None):
		return self.process(text, encoding)

# EOF
