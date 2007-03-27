#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet fenc=latin-1
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   06-Mar-2006
# Last mod.         :   18-Oct-2006
# -----------------------------------------------------------------------------

import re, xml.dom
import sys
from formatting import *

RE_EXPRESSION    =re.compile("\$\(([^\)]+)\)")

__doc__ = """\
The template module implements a simple way to convert an XML document to another
format (HTML, text, whatever) by expanding very simple XPath-like expressions. Of
course, it is a very-small subset of what you could do in XSLT, but it has a
Python syntax and is very, very easy to use.

At first, your define `convertXXX' functions where XXX is your case-sensitive
tagName. All these functions should take an element as parameter and run the
`process' function with the element and template string as parameter.

Expressions like `$(XXX)' (XXX being the expression) in the template strings
will be expanded by procesing the set of nodes indicated by the XXX expression.

 - $(*) will process all children
 - $(MyNode) will process only nodes with 'MyNode' tagName
 - $(MyParent/MyNode) will process only the children of MyParent named MyNode
 - $(MyNode:alt) will use the function `convertMyNode_alt' instead of the
   default 'convertMyNode', if available. This allows to setup 'processing
   modes' for your document (like table of content, references, etc).
 - $(MyNode:alt?) will use the function `convertMyNode_alt' if it is defined, or
   fallback to `convertMyNode`.

"""

#------------------------------------------------------------------------------
#
#  Processing functions
#
#------------------------------------------------------------------------------

class Processor:
	"""The processor is the core of the template engine. You give it a Python
	module with "convert*" functions, and it will process it."""

	def __init__( self, module=None ):
		self.expressionTable = {}
		self.variables       = {}

	def register( self, name2functions ):
		"""Fills the EXPRESSION_TABLE which maps element names to processing
		functions. This function is only useful when you implement your
		templates in the same way as the `kiwi2html` module, ie. with processing
		functions like `convertXXX_VVV` where `XXX` stands for the element name,
		and `_VVV` is the optional variant (selected by`$(element:variant)`).
		
		You may prefer to use the `registerElementProcessor` instead if you want
		to register a processor for an individual tag.
		"""
		self.expressionTable = {}
		for name, function in name2functions.items():
			if name.startswith("convert"):
				ename = name[len("convert"):]
				ename = ename.replace("_", ":")
				self.expressionTable[ename] = function

	def registerElementProcessor( self, function, elementName, variant=None  ):
		"""Registers the given function to process the given element name and
		the given optional variant.
		
		Note that this will replace any previsously registered processor for the
		element and variant."""
		if variant: elementName += ":" + variant
		self.expressionTable[elementName] = function

	def resolveSet( self, element, names ):
		"""Resolves the set of names in the given element. When ["Paragraph"] is
		given, then all child paragraph nodes of the current node will be returned,
		while ["Section", "Paragraph"] will return all paragraphs for all
		sections."""
		s = []
		if len(names) == 1:
			name = names[0]
			for child in element.childNodes:
				if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE: continue
				if name == "*" or child.tagName == name: s.append(child)
		else:
			name = names[0]
			for child in element.childNodes:
				if name != "*" and not child.nodeType == xml.dom.Node.ELEMENT_NODE: continue
				if name == "*" or child.tagName == name: s.extend(self.resolveSet(child, names[1:]))
		return s

	def processElement( self, element, selector=None ):
		"""Processes the given element according to the EXPRESSION_TABLE, using the
		given selector to select an alternative function."""
		selector_optional = False
		if selector and selector[-1] == "?":
			selector = selector[:-1]
			selector_optional = True
		if element.nodeType == xml.dom.Node.TEXT_NODE:
			return escapeHTML(element.data)
		elif element.nodeType == xml.dom.Node.ELEMENT_NODE:
			element._processor = self
			fname = element.nodeName
			if selector: fname += ":" + selector
			func  = self.expressionTable.get(fname)
			# There is a function for the element in the EXPRESSION TABLE
			if func:
				return func(element)
			elif selector_optional:
				self.processElement(element)
			# Otherwise we simply expand its text
			else:
				return self.defaultProcessElement(element, selector)
		else:
			return ""

	def defaultProcessElement( self, element, selector ):
		"""Default function for processing elements. This returns the text."""
		return "".join([self.processElement(e) for e in element.childNodes])

	def interpret( self, element, expression ):
		"""Interprets the given expression for the given element"""
		assert self.expressionTable
		# =VARIABLE means that we replace the expression by the content of the
		# variable in the varibales directory
		if expression.startswith("="):
			vname = expression[1:].upper()
			return self.variables.get(vname) or ""
		# Otherwise, the expression is a node selection expression, which may also
		# have a selector
		elif expression.rfind(":") != -1:
			names, selector = expression.split(":")
		# There may be no selector as well
		else:
			names           = expression
			selector        = None
		names = names.split("/")
		r     = ""
		for element in self.resolveSet(element, names):
			r += self.processElement(element, selector)
		return r

	# SYNTAX: $(EXPRESSION)
	# Where EXPRESSION is a "/" separated list of element names, optionally followed
	# by a colon ':' and a name
	def process( self, element, text ):
		i = 0
		r = ""
		while i < len(text):
			m = RE_EXPRESSION.search(text, i)
			if not m:
				r += text[i:]
				break
			else:
				r += text[i:m.start()]
			r+= self.interpret(element, m.group(1))
			i = m.end()
		return r

	def generate( self, xmlDocument, bodyOnly=False, variables={} ):
		self.variables = variables
		return self.processElement(xmlDocument.childNodes[0])

# EOF
