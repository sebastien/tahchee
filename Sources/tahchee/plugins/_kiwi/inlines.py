#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: ts=4 sw=4 tw=80 noet
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre (SPE)           <sebastien@type-z.org>
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   05-Aug-2008
# -----------------------------------------------------------------------------

import re

__pychecker__ = "unusednames=y"

#------------------------------------------------------------------------------
#
#  Error messages
#
#------------------------------------------------------------------------------

END_WITHOUT_START = "Markup `%s' end found without previous markup start"
START_WITHOUT_END = "Markup `%s' start found without following markup end"
MUST_BE_START_OR_END = \
"Unrecognised markup specifier: 'start' or 'end' would be expected"

#------------------------------------------------------------------------------
#
#  Regular expressions
#
#------------------------------------------------------------------------------

#The regular expressions listed below are ordered conforming to their order
#of insertion into the parser.

# Kiwi core

COMMENT          = u"^\s*#.*$"
RE_COMMENT       = re.compile(COMMENT, re.LOCALE | re.MULTILINE )

ESCAPED_START    = u"<\["
RE_ESCAPED_START = re.compile(ESCAPED_START, re.LOCALE)
ESCAPED_END      = u"\]>"
RE_ESCAPED_END   = re.compile(ESCAPED_END, re.LOCALE)
ESCAPED_REPLACE  = u'\\"'
RE_ESCAPED_REPLACE=re.compile(ESCAPED_REPLACE, re.LOCALE)

ESCAPED_STRING   = u'\\\\"([^"]+)"'
RE_ESCAPED_STRING = re.compile(ESCAPED_STRING, re.MULTILINE|re.LOCALE)

# Text style

CODE             = u"`([^\`]+)`"
RE_CODE          = re.compile(CODE, re.LOCALE|re.MULTILINE)
CODE_2           = u"``((`?[^`])+)``"
RE_CODE_2        = re.compile(CODE_2, re.LOCALE|re.MULTILINE)
CODE_3           = u"'([^']+)'"
RE_CODE_3        = re.compile(CODE_3, re.LOCALE|re.MULTILINE)
PRE              = u"^((\s*\>(\t|   ))(.*)\n?)+"
RE_PRE           = re.compile(PRE, re.LOCALE|re.MULTILINE)
EMPHASIS         = u"\*([^*]+)\*"
RE_EMPHASIS      = re.compile(EMPHASIS, re.LOCALE|re.MULTILINE)
STRONG           = u"\*\*([^*]+)\*\*"
RE_STRONG        = re.compile(STRONG, re.LOCALE|re.MULTILINE)
TERM             = u"\_([^_]+)_"
RE_TERM          = re.compile(TERM, re.LOCALE|re.MULTILINE)
QUOTED           = u"''(('?[^'])+)''"
RE_QUOTED        = re.compile(QUOTED, re.LOCALE|re.MULTILINE)
CITATION         = u"«([^»]+)»"
RE_CITATION      = re.compile(CITATION,re.LOCALE|re.MULTILINE)

# Special Characters

BREAK            = u"\s*\n\s*\|\s*\n()"
RE_BREAK         = re.compile(BREAK)
SWALLOW_BREAK    = u"\s*\|\s*\n()"
RE_SWALLOW_BREAK = re.compile(SWALLOW_BREAK)
NEWLINE          = u"\s*\\\\n\s*()"
RE_NEWLINE       = re.compile(NEWLINE)
LONGDASH         = u" -- ()"
RE_LONGDASH      = re.compile(LONGDASH)
LONGLONGDASH     = u" --- ()"
RE_LONGLONGDASH      = re.compile(LONGLONGDASH)
ARROW            = u"<-+>|-+->|<-+"
RE_ARROW         = re.compile(ARROW,)
DOTS             = u"\.\.\.()"
RE_DOTS          = re.compile(DOTS,)
ENTITIES         = u"(&(\w+|#[0-9]+);)"
RE_ENTITIES      = re.compile(ENTITIES,)

# Linking content

EMAIL            = u"\<([\w.\-_]+@[\w.\-_]+)\>"
RE_EMAIL         = re.compile(EMAIL, re.LOCALE|re.MULTILINE)
URL              = u"\<([A-z]+://[^\>]+)\>"
RE_URL           = re.compile(URL, re.LOCALE|re.MULTILINE)
URL_2            = u"([A-z]+://[^\>]+)"
RE_URL_2         = re.compile(URL_2, re.LOCALE|re.MULTILINE)
LINK             = u"""\[([^\]]+)\]\s*((\(([^ \)]+)(\s+"([^"]+)"\s*)?\))|\[([\w\s]+)\])?"""
RE_LINK          = re.compile(LINK, re.LOCALE|re.MULTILINE)
TARGET           = u"\|([\w\s]+(:[^\|]*)?)\|"
RE_TARGET        = re.compile(TARGET, re.LOCALE)

# Custom markup
MARKUP_ATTR      = u"""\w+\s*=\s*('[^']*'|"[^"]*")"""
MARKUP           = u"\<(\w+)(\s*%s)*\s*/?>|\</(\w+)\s*>" % (MARKUP_ATTR)
RE_MARKUP        = re.compile(MARKUP, re.LOCALE|re.MULTILINE)

def _processText( context, text ):
	"""Common operation for expanding tabs and normalising text. Use by
	acronyms, citations and quotes."""
	if not text: return text
	text = context.parser.expandTabs(text)
	text = context.parser.normaliseText(text)
	return text

#------------------------------------------------------------------------------
#
#  InlineParser
#
#------------------------------------------------------------------------------

class InlineParser:

	def __init__( self, name, regexp, result=lambda x,y: x.group(1),
		requiresLeadingSpace=False):
		"""Creates a new InlineParser.

		Name is the name of the parser, *regexp* is the string expression
		of the regular expression that will match the element that the
		InlineParser is looking for, or regexp can also be a precompiled
		regular expression object.

		Result is a lambda expression that will return the content of the
		Inline generated by the *parse* method. The lambda takes two
		arguments : the match object and the string in which the match object
		has been found."""
		self.name   = name
		#Checks if regexp is a string or a precompiled regular expression
		if type(regexp) in (type(u""), type("")):
			self.regexp = re.compile(regexp, re.LOCALE|re.MULTILINE)
		else:
			self.regexp = regexp
		self.result = result
		self.requiresLeadingSpace = requiresLeadingSpace

	def _recognisesBefore( self, context, match ):
		"""A function that is called to check if the text before the current
		offset is recognized by this parser. This is used by
		'requiresLeadingSpace'."""
		if match.start() == 0: return True
		previous_char = context.currentFragment()[match.start()-1]
		return previous_char in u' \t();:-!?'

	def recognises( self, context ):
		"""Recognises this inlines in the given context, within the current
		context block. It returns (None, None) when the inline was not recognised,
		otherwise it returns the offset of the matching element in the current
		context, plus information that will be given as argument to the parse
		method. This means that the returned offset is RELATIVE TO THE CURRENT
		CONTEXT OFFSET."""
		match = self.regexp.search(context.currentFragment())
		fragment = context.currentFragment()
		if match:
			match_start = max(0,match.start()-1)
			if self.requiresLeadingSpace and not self._recognisesBefore(context, match):
				return (None, None)
			return (match.start(), match)
		else:
			return (None, None)

	def endOf( self, recogniseInfo ):
		"""Returns the end of this inline using the given recogniseInfo."""
		return recogniseInfo.end()

	def parse( self, context, node, recogniseInfo  ):
		"""Parses the given context within the current block range, returning
		the new offset (relative to the block start offset, ie. the start of
		context.currentFragment). Note that the context offsets are the same
		as those given to the recognise method call which created
		recogniseInfo.

		The given context starts at the same offset as when recognises was
		called. Modifications are made to the given node."""
		match = recogniseInfo
		assert match!=None
		text = self.result(match, context.documentText)
		if self.name:
			inline_node = context.document.createElementNS(None, self.name)
			if text:
				text_node   = context.document.createTextNode(text)
				inline_node.appendChild(text_node)
			node.appendChild(inline_node)
		elif not self.name is None:
			inline_node   = context.document.createTextNode(text)
			node.appendChild(inline_node)
		return self.endOf(recogniseInfo)

#------------------------------------------------------------------------------
#
#  Arrow parsers
#
#------------------------------------------------------------------------------

class ArrowInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "arrow", RE_ARROW )

	def parse( self, context, node, match ):
		assert match
		text = match.group()
		arrow_type = None
		if text[0] == "<":
			if text[-1] == ">": arrow_type = "double"
			else: arrow_type = "left"
		else:
			arrow_type = "right"
		arrow_node = context.document.createElementNS(None, "arrow")
		arrow_node.setAttributeNS(None, "type", arrow_type)
		node.appendChild(arrow_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  Entity parsers
#
#------------------------------------------------------------------------------

class EntityInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "entity", RE_ENTITIES )

	def parse( self, context, node, match ):
		assert match
		text = match.group(2)
		entity_node = context.document.createElementNS(None, "entity")
		entity_node.setAttributeNS(None, "num", text)
		node.appendChild(entity_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  Pre parsers
#
#------------------------------------------------------------------------------

class PreInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "pre", PRE )

	def recognises( self, context ):
		return InlineParser.recognises(self,context)

	def parse( self, context, node, match ):
		lines = []
		for text in match.group().split("\n"):
			submatch = RE_PRE.match(text + "\n")
			if text: text = context.parser.expandTabs(submatch.group(4))
			lines.append(text)
		pre_node = context.document.createElementNS(None, 'pre')
		pre_node.appendChild(context.document.createTextNode("\n".join(lines)))
		node.appendChild(pre_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  CommentInlineParser
#
#------------------------------------------------------------------------------

class CommentInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "comment", RE_COMMENT )

	def processText( self, text ):
		new_text = ""
		for line in text.split("\n"):
			line = line.strip()
			if len(line)>1:
				line = line[1:]
				new_text += line + "\n"
		if new_text: new_text = new_text[:-1]
		new_text = " "+new_text+" "
		return new_text

	def parse( self, context, node, recogniseInfo ):
		match = recogniseInfo
		assert match!=None
		node.appendChild(context.document.createComment(
			self.processText(match.group())))
		return match.end()

#------------------------------------------------------------------------------
#
#  Escape inline parser
#
#------------------------------------------------------------------------------

class EscapedInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "escaped", None )

	def recognises( self, context ):
		start_match = RE_ESCAPED_START.search(context.currentFragment())
		if start_match:
			# And search the escape starting from the end of the escaped
			end_match = RE_ESCAPED_END.search(
				context.currentFragment(), start_match.end())
			if end_match:
				return (start_match.start(), (start_match, end_match))
			else:
				return (None, None)
		return (None, None)

	def endOf( self, recogniseInfo ):
		return recogniseInfo[1].end()

	def parse( self, context, node, recogniseInfo  ):
		# We get start and end match, end being relative to the start
		start_match, end_match = recogniseInfo
		assert start_match!=None and end_match!=None

		# Create a text node with the escaped text
		escaped_node = context.document.createTextNode(
			context.currentFragment()[start_match.end():end_match.start()])
		node.appendChild(escaped_node)
		# And increase the offset
		return self.endOf(recogniseInfo)

#------------------------------------------------------------------------------
#
#  Escaped String Inline Parser
#
#------------------------------------------------------------------------------

class EscapedStringInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, None, RE_ESCAPED_STRING )

	def parse( self, context, node, match ):
		res = context.document.createTextNode(match.group(1))
		node.appendChild(res)
		return match.end()

#------------------------------------------------------------------------------
#
#  Link/Reference parser
#
#------------------------------------------------------------------------------

class LinkInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "link", RE_LINK )

	def recognises( self, context ):
		result = InlineParser.recognises(self, context)
		# We avoid conflict with the tasks list. This may not be
		# always necessary, but it's safer to have it.
		if result[1]:
			r = result[1].group().strip()
			if len(r) == 3 and r[0] == "[" and r[2]=="]":
				return (None, None)
		return result

	def parse( self, context, node, match ):
		assert match
		# We detect wether the link is an URL or Ref link
		link_node = context.document.createElementNS(None, "link")
		if match.group(7):
			ref_entry = match.group(7)
			link_node.setAttributeNS(None, "type",   "ref")
			link_node.setAttributeNS(None, "target", ref_entry)
		else:
			ref_url   = match.group(4)
			ref_title = match.group(5)
			if not ref_url:
				link_node.setAttributeNS(None, "type", "ref")
				link_node.setAttributeNS(None, "target", match.group(1))
			else:
				link_node.setAttributeNS(None, "type", "url")
				link_node.setAttributeNS(None, "target", ref_url)
		context._links.append(link_node)
		#Now we parse the content of the link
		offsets = context.saveOffsets()
		context.setCurrentBlock(context.getOffset() + match.start() + 1,
		context.getOffset() + match.start() + 1 + len(match.group(1)))
		context.parser.parseBlock(context, link_node, _processText)
		context.restoreOffsets(offsets)
		node.appendChild(link_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  Target parser
#
#------------------------------------------------------------------------------

class TargetInlineParser( InlineParser ):

	def __init__( self ):
		InlineParser.__init__( self, "target", RE_TARGET )

	def parse( self, context, node, match ):
		assert match
		# We detect wether the link is an URL or Ref link
		target_node = context.document.createElementNS(None, "target")
		name_and_text = match.group(1).split(":", 1)
		if len(name_and_text) == 1:
			name = name_and_text[0]
			text = None
		else:
			name = name_and_text[0]
			text = name_and_text[1]
			if not text: text = name
		target_node.setAttributeNS(None, "name", name.replace("  ", " ").strip().lower())
		if text:
			text_node   = context.document.createTextNode(text)
			target_node.appendChild(text_node)
		context._targets.append(target_node)
		node.appendChild(target_node)
		return match.end()

#------------------------------------------------------------------------------
#
#  MarkupInlineParser
#
#------------------------------------------------------------------------------

def Markup_isStartTag( match ):
	return not Markup_isEndTag(match) and not match.group().endswith("/>")

def Markup_isEndTag( match ):
	return match.group().startswith("</")

def Markup_attributes( match ):
	"""Returns the attribute string of this markup stat element."""
	text = match.group()[1 + len(match.group(1))+1:-1]
	if text and text[-1] == "/": text = text[:-1]
	text = text.strip()
	return text

class MarkupInlineParser( InlineParser ):
	"""Parses Kiwi generic markup elements."""

	def __init__( self ):
		InlineParser.__init__(self, None, RE_MARKUP)

	def parse( self, context, node, recogniseInfo  ):
		"""Parses the given tag, and returns the offset where the parsed tag
		ends. If the tag is an "inline block" tag, then its content is also
		parsed."""
		match = recogniseInfo
		# Is it an inline ?
		if match.group().endswith("/>"):
			# TODO: Check if element name is recognised or not
			markup_name = match.group(1)
			markup_node = context.document.createElementNS(None, markup_name.strip())
			markup_node.setAttributeNS(None, "_html", "true")
			for key, value in context.parseAttributes(Markup_attributes(match)).items():
				markup_node.setAttributeNS(None, key, value)
			node.appendChild(markup_node)
			return match.end()
		# Or is it a block start ?
		elif self.isStartTag(match):
			# We search for an end, taking care of setting the offset after the
			# recognised inline.
			markup_name  = match.group(1).strip()
			markup_range = self.findEnd( markup_name, context, match.end())
			if not markup_range:
				context.parser.error( START_WITHOUT_END % (markup_name), context )
				return match.end()
			else:
				markup_end   = markup_range[0] + context.getOffset()
				# We do not want the context to be altered by block parsing
				offsets = context.saveOffsets()
				context.setCurrentBlock(context.getOffset()+match.end(),
					context.getOffset()+markup_range[0])
				# We check if there is a specific block parser for this markup
				custom_parser = context.parser.customParsers.get(markup_name)
				# Here we have found a custom parser, which is in charge for
				# creating nodes
				if custom_parser:
					custom_parser.process(context, None)
				# Otherwise we create the node for the markup and continue
				# parsing
				else:
					markup_node = context.document.createElementNS(None, "Content")
					markup_node.setAttributeNS(None, "_html", "true")
					node.appendChild(markup_node)
					# We add the attributes to this tag
					for key, value in context.parseAttributes(Markup_attributes(match)).items():
						markup_node.setAttributeNS(None, key, value)
					# FIXME: This should not be necessary
					old_node = context.currentNode
					context.currentNode = markup_node
					context.currentNode = markup_node
					before_offset = context.getOffset()
					next_block = context.parser._findNextBlockSeparator(context)
					# There may be many blocks contained in the markup delimited
					# by the node. Here we try to parse all the blocks until be
					# reach the end of the markup minus 1 (that is the last
					# separator before the block end)
					if context.offsetInBlock(next_block[0]) or context.offsetInBlock(next_block[1]):
						end_offset  = context.blockEndOffset
						context.setOffset(context.blockStartOffset)
						while context.getOffset() < markup_end :
							context.parser._parseNextBlock(context, end=markup_end)
					# If there was no block contained, we parse the text as a
					# single block
					else:
						context.parser.parseBlock(context, markup_node, self.processText)
					markup_node.nodeName = markup_name
					markup_node.tagName = markup_name
					context.currentNode = old_node
				context.restoreOffsets(offsets)
				return markup_range[1]
		# Or is a a closing element ?
		elif self.isEndTag(match):
			context.parser.error( END_WITHOUT_START % (match.group(4).strip()),
			context )
			return match.end()
		else:
			context.parser.error( MUST_BE_START_OR_END, context )
			return match.end()

	def _searchMarkup( self, context ):
		"""Looks for the next markup inline in the current context. This also
		takes care of markups that are contained into an escaped text tag.

		WARNING : this operation mutates the context offsets, so this should
		always be enclosed in offset store and restore. The context offset is
		set BEFORE the searched markup, so that the returned recognition info
		is relative to the context offset.

		Returns the result of this parser `recognise' method, or null."""
		inline_parsers = ( context.parser.escapedParser, self )
		# We look for a block inline
		while not context.blockEndReached():
			result = context.findNextInline(inline_parsers)
			if result:
				if result[2] == self:
					return result[1]
				else:
					context.increaseOffset(result[2].endOf(result[1]))
			else:
				break
		return None

	def isStartTag( self, match ):
		return Markup_isStartTag(match)

	def isEndTag( self, match ):
		return Markup_isEndTag(match)

	def findEnd( self, blockName, context, offsetIncr=0 ):
		"""Finds the end of the given markup end in the current block. Returns
		a couple (start, end) indicating the start and end offsets of the found
		end block, relative to the context offset. The given 'offsetIncr'
		parameter tells the number of characters to skip before searching for
		the end markup. This has no impact on the result.

		The context offsets are left unchanged."""
		depth = markup_match =  1
		block_name = None
		offsets = context.saveOffsets()
		original_offset = context.getOffset()
		context.increaseOffset(offsetIncr)
		# We look for start and end markups
		while depth>0 and markup_match and not context.blockEndReached():
			markup_match = self._searchMarkup(context)
			if markup_match:
				if self.isStartTag(markup_match):
					depth += 1
				elif self.isEndTag(markup_match):
					depth -= 1
					block_name = markup_match.group(4).strip()
				if depth > 0:
					context.increaseOffset(markup_match.end())
		# We have found at least one matching block
		end_markup_range = None
		if depth==0 and block_name and block_name==blockName:
			# The match is relative to the current context offset
			match_start = context.getOffset() - original_offset + markup_match.start()
			match_end   = context.getOffset() - original_offset + markup_match.end()
			end_markup_range = ( match_start, match_end )
		context.restoreOffsets(offsets)
		return end_markup_range

	def processText( self, context, text ):
		return context.parser.normaliseText(text)

# EOF
