#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2007
# Last mod.         :   19-Nov-2007
# -----------------------------------------------------------------------------

import re, xml.dom
import sys
from formatting import *
import templates

#------------------------------------------------------------------------------
#
#  Actual element processing
#
#------------------------------------------------------------------------------

def convertDocument(element):
	return process(element, """\
$(Header:title)
$(Content)
$(References)
""")

def convertHeader( element ):
	return process(element, "---+ $(Title/title)\n---++ $(Title/subtitle)\n" )

def convertHeading( element ):
	return process(element, "$(*)")

def convertSection( element ):
	level = int(element.getAttributeNS(None, "_depth"))
	prefix = "---+" + "+" * level
	return process(element,
		prefix + " $(Heading)\n\n"
		+ "$(Content:section)"
	)

def convertReferences( element ):
	return process(element, """  $(Entry)""")

def convertParagraph( element ):
	return process(element, """$(*)\n\n""")

def convertParagraph_cell( element ):
	return process(element, """$(*)\n""")

def convertList( element ):
	is_todo = element.getAttributeNS(None, "type")
	attrs = [""]
	return process(element, """$(*)\n\n""")

def convertListItem( element ):
	attrs   = [""]
	is_todo = element.getAttributeNS(None, "todo")
	return process(element, """   * $(*)\n""")

def convertTable( element ):
	return process(element, """$(Content:table)\n\n""")

def convertDefinition( element ):
	return process(element, """$(*)\n\n""")

def convertDefinitionItem( element ):
	return process(element, """   $ $(Title) : $(Content)\n""")

def convertRow( element ):
	try: index = element.parentNode.childNodes.index(element) % 2 + 1
	except: index = 0 
	classes = ( "", "even", "odd" )
	return process(element, """$(*) |\n""")

def convertCell( element ):
	suffix     = ""
	if element.hasAttributeNS(None, "colspan"):
		suffix = " " + "|" * (int(element.getAttributeNS(None,"colspan")) - 2)
	cell = process(element, "$(*:cell)")[:-1]
	return ("| " + cell + suffix)

def convertBlock( element ):
	title = element.getAttributeNS(None,"title") or element.getAttributeNS(None, "type") or ""
	css_class = ""
	if title:
		css_class=" class='ann%s'" % (element.getAttributeNS(None, "type").capitalize())
		title = "<div class='title'>%s</div>"  % (title)
		div_type = "div"
	elif not element.getAttributeNS(None, "type"):
		div_type = "blockquote"
	return process(element, """<%s%s>%s<div class='content'%s>$(*)</div></%s>""" % (div_type, css_class, title, "", div_type))

def stringToTarget( text ):
	return text.replace("  ", " ").strip().replace(" ", "-").upper()

def convertlink( element ):
	if element.getAttributeNS(None, "type") == "ref":
		return process(element, """[[#%s][$(*)]]""" %
		(stringToTarget(element.getAttributeNS(None, "target"))))
	else:
		# TODO: Support title
		return process(element, """[[%s][$(*)]]""" %
		(element.getAttributeNS(None, "target")))

def converttarget( element ):
	name = element.getAttributeNS(None, "name")
	return process(element, """#%s $(*)""" % (stringToTarget(name)))


def convertemail( element ):
	mail = ""
	for c in  process(element, """$(*)"""):
		mail += c
	return """[[mailto:%s][%s]]""" % (mail, mail)

def converturl( element ):
	return process(element, """[[$(*)][(*)]]""")

def convertterm( element ):
	return process(element, """*$(*)*""")

def convertquote( element ):
	return process(element, """''_$(*)_''""")

def convertstrong( element ):
	return process(element, """__$(*)__""")

def convertpre( element ):
	return process(element, """<verbatim>\n$(*)\n</verbatim>\n\n""")
	
def convertcode( element ):
	return process(element, """=$(*)=""")

def convertemphasis( element ):
	return process(element, """_$(*)_""")

def convertbreak( element ):
	return process(element, """ """)

def convertnewline( element ):
	return process(element, """ """)

def convertarrow( element ):
	arrow = element.getAttributeNS(None, "type")
	if   arrow == "left":
		return "<--"
	elif arrow == "right":
		return "-->"
	else:
		return "<-->"

def convertdots( element ):
	return "..."

def convertendash( element ):
	return " -- "

def convertemdash( element ):
	return " -- "

def convertentity( element ):
	return "&%s;" % (element.getAttributeNS( None, "num"))

# We create the processor, register the rules and define the process variable
processor      = templates.Processor()
name2functions = {}
for symbol in filter(lambda x:x.startswith("convert"), dir()):
	name2functions[symbol] = eval(symbol)
processor.register(name2functions)
process = processor.process

# EOF
