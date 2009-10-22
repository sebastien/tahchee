#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project           :   Kiwi
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   19-Nov-2003
# Last mod.         :   26-Jul-2008
# -----------------------------------------------------------------------------

import os, sys, StringIO

__doc__ = """Kiwi is an advanced markup text processor, which can be used as
an embedded processor in any application. It is fast, extensible and outputs an
XML DOM."""

__version__ = "0.8.6"
__pychecker__ = "blacklist=cDomlette,cDomlettec"

import re, string, operator, getopt, codecs

# NOTE: I disabled 4Suite support, as minidom is good as it is right now
# We use 4Suite domlette
#import Ft.Xml.Domlette
#dom = Ft.Xml.Domlette.implementation
# We use minidom implementation
import xml.dom.minidom
dom = xml.dom.minidom.getDOMImplementation()

import core, kiwi2html, kiwi2lout, kiwi2twiki

FORMATS = {
	"html":kiwi2html,
#	"lout":kiwi2lout,
	"twiki":kiwi2twiki
}

#------------------------------------------------------------------------------
#
#  Command-line interface
#
#------------------------------------------------------------------------------

USAGE = u"Kiwi v."+__version__+u""",
   A flexible tool for converting plain text markup to XML and HTML.
   Kiwi can be used to easily generate documentation from plain files or to
   convert exiting Wiki markup to other formats.

   See <http://www.ivy.fr/kiwi>

Usage: kiwi [options] source [destination]

   source:
      The text file to be parsed (usually an .stx file, "-" for stdin)
   destination:
      The optional destination file (otherwise result is dumped on stdout)

Options:

   -i --input-encoding           Allows to specify the input encoding
   -o --output-encoding          Allows to specify the output encoding
   -t --tab                      The value for tabs (tabs equal N sapces).
                                 Set to 4 by default.
   -f --offsets                  Add offsets information
   -p --pretty                   Pretty prints the output XML, this should only
                                 be used for viewing the output.
   -m --html                     Outputs an HTML file corresponding to the Kiwi
                                 document
      --no-style                 Does not include the default CSS in the HTML
      --body-only                Only returns the content of the <body< element
      --level=n                  If n>0, n will transform HTML h1 to h2, etc...
   -O --output-format            Specifies and alternate output FORMAT
                                 (see below)
								 
   The available encodings are   %s
   The available formats are     %s
   
Misc:
   -h,  --help                    prints this help.
   -v,  --version                 prints the version of Kiwi.
"""

# Error codes

ERROR   = -1
INFO    = 0
SUCCESS = 1

# Normalised encodings

ASCII  = "us-ascii"
LATIN1 = "iso-8859-1"
LATIN2 = "iso-8859-2"
UTF8   = "utf-8"
UTF16  = "utf-16"
MACROMAN  = "macroman"
NORMALISED_ENCODINGS = (LATIN1, LATIN2, UTF8, UTF16, MACROMAN)

# Supported encodings

ENCODINGS = {
	ASCII:ASCII, "usascii":ASCII, "plain":ASCII, "text":ASCII, "ascii":ASCII,
	LATIN1:LATIN1, "latin-1":LATIN1, "latin1":LATIN1, "iso8859":LATIN1,
	"iso8859-1":LATIN1, "iso88591":LATIN1, "iso-88591":LATIN1,
	LATIN2:LATIN2, "latin2":LATIN2, "latin-2":LATIN2, "iso8859-2":LATIN2,
	"iso88592":LATIN2, "iso-88592":LATIN2,
	UTF8:UTF8, "utf8":UTF8,
	UTF16:UTF16, "utf16":UTF16,
	MACROMAN:MACROMAN, "mac-roman":MACROMAN
}

def run( arguments, input=None, noOutput=False ):
	"""Returns a couple (STATUS, VALUE), where status is 1 when OK, 0 when
	informative, and -1 when error, and value is a string.
	
	The given arguments can be either a string or an array, the input can be
	None (it will be then taken from the arguments), or be a file-like object,
	and the noOutput flag will not output the result on stdout or whatever file
	is given on the command line.
	"""
	if type(arguments) == str: arguments = arguments.split()

	# --We extract the arguments
	try:
		optlist, args = getopt.getopt(arguments, "hpmfO:vi:o:t:",\
		["input-encoding=", "output-encoding=", "output-format=",
		"offsets", "help", "html", "tab=", "version",
		"pretty", "no-style", "nostyle",
		"body-only", "bodyonly", "level="])
	except:
		args=[]
		optlist = []

	# We get the list of available encodings
	available_enc = []
	ENCODINGS_LIST=""
	for encoding in NORMALISED_ENCODINGS:
		try:
			codecs.lookup(encoding)
			available_enc.append(encoding)
			ENCODINGS_LIST+=encoding+", "
		except:
			pass
	ENCODINGS_LIST=ENCODINGS_LIST[:-2]+"."

	usage = USAGE % (ENCODINGS_LIST, ", ".join(FORMATS.keys()))

	# We set attributes
	pretty_print    = 0
	show_offsets    = False
	validate_output = 0
	generate_html   = 1
	no_style        = 0
	body_only       = 0
	level_offset    = 0
	input_enc       = ASCII
	output_enc      = ASCII
	output_format   = "html"
	if LATIN1 in ENCODINGS:
		input_enc  = LATIN1
		output_enc = LATIN1
	elif UTF8 in ENCODINGS:
		input_enc  = UTF8
		output_enc = UTF8

	# We parse the options
	for opt, arg in optlist:
		if opt in ('-h', '--help'):
			return (INFO, usage.encode(LATIN1))
		elif opt in ('-v', '--version'):
			return (INFO, __version__)
		elif opt in ('-i', '--input-encoding'):
			arg = string.lower(arg)
			if arg in ENCODINGS.keys() and ENCODINGS[arg] in available_enc:
				input_enc=output_enc=ENCODINGS[arg]
			else:
				r  = "Kiwi error : Specified input encoding is not available, choose between:"
				r += ENCODINGS_LIST
				return (ERROR, r)
		elif opt in ('-o', '--output-encoding'):
			arg = string.lower(arg)
			if arg in ENCODINGS.keys() and ENCODINGS[arg] in available_enc:
				output_enc=ENCODINGS[arg]
			else:
				r  = "Kiwi error: Specified output encoding is not available, choose between:"
				r += ENCODINGS_LIST
				return (ERROR, r)
		elif opt in ('-O', '--output-format'):
			arg = string.lower(arg)
			if arg in FORMATS.keys():
				output_format=arg
			else:
				r  = "Kiwi error: Given format (%s) not supported. Choose one of:\n" % (arg)
				r += "\n  - ".join(FORMATS)
				return (ERROR, r)
		elif opt in ('-t', '--tab'):
			TAB_SIZE = int(arg)
			if TAB_SIZE<1:
				return (ERROR, "Kiwi error: Specified tab value (%s) should be superior to 0." %\
				(TAB_SIZE))
		elif opt in ('--no-style', "--nostyle"):
			no_style      = 1
			generate_html = 1
			pretty_print  = 0
		elif opt in ('--body-only', "--bodyonly"):
			no_style      = 1
			body_only     = 1
			generate_html = 1
			pretty_print  = 0
		elif opt in ('-p', '--pretty'):
			pretty_print  = 1
			generate_html = 0
		elif opt in ('-m', '--html'):
			generate_html = 1
			output_format = "html"
			pretty_print  = 0
		elif opt in ('-f', '--offsets'):
			show_offsets = True
		elif opt in ('--level'):
			level_offset = min(10, max(0, int(arg)))

	# We check the arguments
	if input==None and len(args)<1:
		return (INFO, usage.encode("iso-8859-1"))

	# We set default values
	if input == None: source = args[0]
	else: source = None
	output = None
	if len(args)>1: output = args[1]

	#sys.stderr.write("Kiwi started with input as %s and output as %s.\n"\
	#% (input_enc, output_enc))
	if input: base_dir = os.getcwd()
	elif source=='-': base_dir = os.path.abspath(".")
	else: base_dir = os.path.abspath(os.path.dirname(source))

	parser = core.Parser(base_dir, input_enc, output_enc)

	if source == output and not noOutput:
		return(ERROR, "Cannot overwrite the source file.")

	# We open the input file, taking care of stdin
	if input != None:
		ifile = input
	elif source=="-":
		ifile = sys.stdin
	else:
		try:
			ifile = codecs.open(source,"r",input_enc)
		except:
			return (ERROR, "Unable to open input file: %s" % (input))

	if noOutput: pass
	elif output==None: ofile = sys.stdout
	else: ofile = open(output,"w")

	try:
		data = ifile.read()
	except UnicodeDecodeError, e:
		r  = "Impossible to decode input %s as %s\n" % (source, input_enc)
		r += "--> %s\n" % (e)
		return (ERROR, r)

	if source!="-": ifile.close()

	if type(data) != unicode:
		data = data.decode(input_enc)
	xml_document = parser.parse(data, offsets=show_offsets)

	result = None
	if generate_html:
		variables = {}
		variables["LEVEL"] = level_offset
		css_file = file(os.path.join(os.path.dirname(kiwi2html.__file__), "screen-kiwi.css"))
		if not no_style:
			variables["HEADER"] = "\n<style><!-- \n%s --></style>" % (css_file.read())
			variables["ENCODING"] = output_enc
		css_file.close()
		result = FORMATS[output_format].processor.generate(xml_document, body_only, variables)
		if result: result = result.encode(output_enc)
		else: result = ""
		if not noOutput: ofile.write(result)
	elif pretty_print:
		#Ft.Xml.Lib.Print.PrettyPrint(xml_document, ofile, output_enc)
		#MiniDom:
		result = xml_document.toprettyxml("  ").encode(output_enc)
		if not noOutput: ofile.write(result)
	else:
		#Ft.Xml.Lib.Print.Print(xml_document, ofile, output_enc)
		#MiniDom:
		result = xml_document.toxml().encode(output_enc)
		if not noOutput: ofile.write(result)
	return (SUCCESS, result)

def text2htmlbody( text, inputEncoding=None, outputEncoding=None ):
	"""Converts the given text to HTML, returning only the body."""
	s = StringIO.StringIO(text)
	command = "-m --body-only"
	if inputEncoding: command += " -i " + inputEncoding
	if outputEncoding: command += " -o " + outputEncoding
	_, text = run(command + " --", s, noOutput=True)
	s.close()
	return text

def runAsCommand():
	status, result = run(sys.argv[1:])
	if status == ERROR:
		sys.stderr.write(result + "\n")
		sys.exit(-1)
	elif status == INFO:
		sys.stdout.write(result + "\n")
		sys.exit(0)

if __name__ == "__main__":
	runAsCommand()

# EOF
