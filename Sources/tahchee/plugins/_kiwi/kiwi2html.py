#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   07-Feb-2006
# Last mod.         :   18-Oct-2006
# -----------------------------------------------------------------------------

import re, xml.dom
import sys
from formatting import *
import templates

#------------------------------------------------------------------------------
#
#  Processing functions
#
#------------------------------------------------------------------------------

class Processor(templates.Processor):

	def defaultProcessElement( self, element, selector ):
		"""We override this for elements with the 'html' attribute."""
		if element.getAttributeNS(None, "_html"):
			res = "<" + element.nodeName
			att = element.attributes
			for i in range(att.length):
				a = att.item(i)
				if a.name == "_html": continue
				res += " %s='%s'" % (a.name, element.getAttributeNS(None, a.name))
			if element.childNodes:
				res += ">"
				for e in element.childNodes:
					res += self.processElement(e)
				res += "</%s>" % (element.tagName)
			else:
				res += "/>"
			return res
		else:
			return templates.Processor.defaultProcessElement(self,element,selector)

	def generate( self, xmlDocument, bodyOnly=False, variables={} ):
		node = xmlDocument.getElementsByTagName("Document")[0]
		self.variables = variables
		if bodyOnly:
			for child in node.childNodes:
				if child.nodeName == "Content":
					return convertContent_bodyonly(child)
		else:
			return convertDocument(node)

#------------------------------------------------------------------------------
#
#  Actual element processing
#
#------------------------------------------------------------------------------

def convertDocument(element):
	return process(element, """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=$(=ENCODING)" />
$(Header)$(=HEADER)
</head>
<body>
$(Header:title)
$(Content)
$(References)
</body>
</html>""")

def element_number( element ):
	"""Utility function that returns the element number (part of the element
	offset attributes)"""
	number = element.getAttributeNS(None, "_number")
	if number: return int(number)
	else: return None

def wdiv( element, text ):
	"""Wraps the given text in a DIV extended with offsets attributes if the
	given element has offset attributes."""
	number = element_number(element)
	if number == None: return text
	return "<div id='KIWI%s' start='%s' end='%s'>%s</div>" % (
		element.getAttributeNS(None, '_number'),
		element.getAttributeNS(None, '_start'),
		element.getAttributeNS(None, '_end'),
		text
	)

def wspan( element, text ):
	"""Wraps the given text in a SPAN extended with offsets attributes if the
	given element has offset attributes."""
	number = element_number(element)
	if number == None: return text
	return "<div id='KIWI%s' start='%s' end='%s'>%s</div>" % (
		element.getAttributeNS(None, '_number'),
		element.getAttributeNS(None, '_start'),
		element.getAttributeNS(None, '_end'),
		text
	)

def wattrs( element ):
	"""Returns the offset attributes of this element if it has any."""
	number = element_number(element)
	if number == None: return ""
	return " id='KIWI%s' start='%s' end='%s'" % (
		element.getAttributeNS(None, '_number'),
		element.getAttributeNS(None, '_start'),
		element.getAttributeNS(None, '_end')
	)

def convertContent( element ):
	return process(element, wdiv(element, """<div class='content'>$(*)</div>"""))

def convertContent_bodyonly( element ):
	return process(element, wdiv(element, """$(*)"""))

def convertContent_table( element ):
	return process(element, """<tbody%s>$(*)</tbody>""" % (wattrs(element)))

def convertHeader( element ):
	return process(element, "<title%s>$(Title/title)</title>" % (wattrs(element)))

def convertHeading( element ):
	return process(element, wspan(element, "$(*)"))

def convertSection( element ):
	offset = element._processor.variables.get("LEVEL") or 0
	level = int(element.getAttributeNS(None, "_depth")) + 1 + offset
	return process(element,
	  '<div class="section">'
	  + '<h%d class="heading">$(Heading)</h%d>' % (level, level)
	  + '<div class="level%d">$(Content:section)</div></div>' % (level)
	)

def convertReferences( element ):
	return process(element, """<div id="references">$(Entry)</div>""")

def convertEntry( element ):
	return process(element, """<div class="entry"><div class="name"><a name="%s">%s</a></div><div class="content">$(*)</div></div>""" %
	(element.getAttributeNS(None, "id"), element.getAttributeNS(None, "id")))

def convertHeader_title( element ):
	return process(element, """<div
	class="title">$(Title/title:header)$(Title/subtitle:header)</div>$(Meta)""")

def converttitle_header( element ):
	return process(element, """<h1%s>$(*)</h1>""" % (wattrs(element)))

def convertsubtitle_header( element ):
	return process(element, """<h2%s>$(*)</h2>""" % (wattrs(element)))

def convertParagraph( element ):
	return process(element, """<p%s>$(*)</p>""" % (wattrs(element)))

def convertParagraph_cell( element ):
	return process(element, """$(*)<br />""")

def convertList( element ):
	return process(element, """<ul%s>$(*)</ul>""" % (wattrs(element)))

def convertListItem( element ):
	return process(element, """<li%s>$(*)</li>""" % (wattrs(element)))

def convertTable( element ):
	return process(element, """<table cellpadding="0" cellspacing="0" align="center">$(Caption)$(Content:table)</table>""")

def convertDefinition( element ):
	return process(element, """<dl%s>$(*)</dl>""" % (wattrs(element)))

def convertDefinitionItem( element ):
	return process(element, """<dt>$(Title)</dt><dd>$(Content)</dd>""")

def convertCaption( element ):
	return process(element, """<caption%s>$(*)</caption>""" % (wattrs(element)))

def convertRow( element ):
	try: index = element.parentNode.childNodes.index(element) % 2 + 1
	except: index = 0 
	classes = ( "", "even", "odd" )
	return process(element, """<tr class='%s'%s>$(*)</tr>""" % (classes[index], wattrs(element)))

def convertCell( element ):
	return process(element, """<td%s>$(*:cell)</td>""" % (wattrs(element)))

def convertBlock( element ):
	title = element.getAttributeNS(None,"title") or element.getAttributeNS(None, "type") or ""
	css_class = ""
	if title:
		css_class=" class='ann%s'" % (element.getAttributeNS(None, "type").capitalize())
		title = "<div class='title'>%s</div>"  % (title.capitalize())
		div_type = "div"
	elif not element.getAttributeNS(None, "type"):
		div_type = "blockquote"
	return process(element, """<%s%s>%s<div class='content'%s>$(*)</div></%s>""" % (div_type, css_class, title, wattrs(element), div_type))

def convertlink( element ):
	if element.getAttributeNS(None, "type") == "ref":
		return process(element, """<a href="#%s">$(*)</a>""" %
		(element.getAttributeNS(None, "target")))
	else:
		# TODO: Support title
		return process(element, """<a href="%s">$(*)</a>""" %
		(element.getAttributeNS(None, "target")))

def convertMeta( element ):
	return process(element, "<table id='meta'>$(*)</table>")

def convertmeta( element ):
	return process(element,
	"<tr><td width='0px' class='name'>%s</td><td width='100%%' class='value'>$(*)</td></tr>" %
	(element.getAttributeNS(None, "name")))

def convertemail( element ):
	mail = ""
	for c in  process(element, """$(*)"""):
		mail += "&#%d;" % (ord(c))
	return """<a href="mailto:%s">%s</a>""" % (mail, mail)

def converturl( element ):
	return process(element, """<a href="$(*)">$(*)</a>""")

def converturl_header( element ):
	return process(element, """<div class='url'>%s</div>""" % (
	converturl(element)))

def convertterm( element ):
	return process(element, """<span class='term'>$(*)</span>""")

def convertquote( element ):
	return process(element, """&ldquo;<span class='quote'>$(*)</span>&rdquo;""")

def convertcitation( element ):
	return process(element, """&laquo;<span class='citation'>$(*)</span>&raquo;""")

def convertemphasis( element ):
	return process(element, """<b>$(*)</b>""")

def convertstrong( element ):
	return process(element, """<strong>$(*)</strong>""")

def convertpre( element ):
	return process(element, """<pre%s>$(*)</pre>""" % (wattrs(element)))

def convertcode( element ):
	return process(element, """<code>$(*)</code>""")

def convertemphasis( element ):
	return process(element, """<b>$(*)</b>""")

def convertbreak( element ):
	return process(element, """<br />""")

def convertnewline( element ):
	return process(element, """<br />""")

def convertarrow( element ):
	arrow = element.getAttributeNS(None, "type")
	if   arrow == "left":
		return "&larr;"
	elif arrow == "right":
		return "&rarr;"
	else:
		return "&harr;"

def convertdots( element ):
	return "&hellip;"

def convertendash( element ):
	return "&ndash;"

def convertemdash( element ):
	return "&mdash;"

def convertentity( element ):
	return "&%s;" % (element.getAttributeNS( None, "num"))

# We create the processor, register the rules and define the process variable
processor      = Processor()
name2functions = {}
for symbol in filter(lambda x:x.startswith("convert"), dir()):
	name2functions[symbol] = eval(symbol)
processor.register(name2functions)
process = processor.process

# EOF
