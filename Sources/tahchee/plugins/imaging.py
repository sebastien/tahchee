# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   25-Feb-2006
# Last mod.         :   13-Jul-2006
# -----------------------------------------------------------------------------

# This is a Kiwi-formatted plugin documentation. This allows to produce
# automatic documentation.
__doc__ = """

Tahchee Imaging Module
======================

The Imaging module is an easy and powerful way to easily generate bitmap images
to integrate into your pages. This module allows you to:

	- Render text using custom fonts (TTF files put in your `Fonts` dir)
	- Generate rounded-corner images, with CSS and HTML code ready for your
	  pages

"""

NAME    = "imaging"
VERSION = None
SUMMARY = "Image generation and processing (fonts, rounded corners)"

# We try to see if the PIL is present
try:
	import Image, ImageFont, ImageDraw
except:
	Image = ImageFront = ImageDraw = None

# This is a CSS file to create a class that will allow to have tables with
# rounded corners
ROUNDED_CSS = """\
table.$(cssclass) tr.upper  td.left
{ background: url('$(images)_ul.png') no-repeat top left; width : $(size)px; height: $(size)px;}
table.$(cssclass) tr.upper  td.middle
{ background: url('$(images)_um.png') repeat-x top; width : $(size)px; }
table.$(cssclass) tr.upper  td.right
{ background: url('$(images)_ur.png') no-repeat top right; width : $(size)px; height: $(size)px;}
table.$(cssclass) tr.middle td.left
{ background: url('$(images)_ml.png') repeat-y top left; width : $(size)px; }
table.$(cssclass) tr.middle td.middle
{ background: url('$(images)_mm.png'); }
table.$(cssclass) tr.middle td.right
{ background: url('$(images)_mr.png') repeat-y top right; width : $(size)px; }
table.$(cssclass) tr.lower  td.left
{ background: url('$(images)_ll.png') no-repeat bottom left; width : $(size)px; height: $(size)px;}
table.$(cssclass) tr.lower  td.middle
{ background: url('$(images)_lm.png') repeat-x bottom left; height: $(size)px;}
table.$(cssclass) tr.lower  td.right
{ background: url('$(images)_lr.png') no-repeat bottom right; width : $(size)px; height: $(size)px;}
"""
ROUNDED_HTML_START = """\
<table class="CLASS" cellpadding="0" cellspacing="0">
	<tr class="upper">
		<td class="left"> </td>
		<td class="middle"> </td>
		<td class="right"> </td>
	</tr>
	<tr class="middle">
		<td class="left"> </td>
		<td class="middle">
"""
ROUNDED_HTML_END = """\	
	</td>
		<td class="right"> </td>
	</tr>
	<tr class="lower">
		<td class="left"> </td>
		<td class="middle"> </td>
		<td class="right"> </td>
	</tr>
</table>"""

class ImagingPlugin:

	def __init__( self, site ):
		self.site = site
	
	def name( self ): return NAME
	def summary( self ): return SUMMARY
	def version( self ): return VERSION
	def doc( self ): return __doc__

	def install( self, localdict ):
		localdict["imaging"] = self

	def text( self, text, fontName, fontSize, color, folder = "images/text" ):
		"""Creates a transparent PNG image containing the given text, printed
		using the given font (taken from the fonts folder), with the given color
		(as a RGB tuple, or as a string with the hexadecimal code prefixed by
		#), and saves the image to the folder (by default, 'images/text'),
		relative to the site root. The image will be named TXXX.png, where the
		XXX is a sequence of 40 characters identifying the text image.
		
		This function returns the path to the image."""
		fontPath = self.fontsDir + "/" + fontName
		if not os.path.exists(fontPath):
			err("Font '%s' does not exist in fonts directory" % (fontName))
			return
		font  = ImageFont.truetype(fontPath, int(fontSize))
		image = Image.new("RGBA", font.getsize(text), (255,255,255,0))
		draw  = ImageDraw.Draw(image)
		draw.text((0,0), text, color, font=font)
		del draw
		output_path = self.pages() + "/" + folder
		if not os.path.exists(output_path): os.makedirs(output_path)
		sig = hashfunc.new(text + fontName + str(fontSize) + str(color))
		f = open(output_path + "/" + sig.hexdigest() + ".png", "w")
		image.save(f, "PNG")
		f.close()
		self.createdFiles.append(folder + "/" + sig.hexdigest() + ".png")
		return folder + "/" + sig.hexdigest() + ".png"

	def roundRectangleCSS(self, cssClass, imagesDir, imagesPrefix, cornerSize):
		"""Returns the definition for a table class that defines a rounded rectangle"""
		if imagesDir:
			css = ROUNDED_CSS.replace("$(images)",   imagesDir + "/" + imagesDir + "/" + imagesPrefix)
		else:
			css = ROUNDED_CSS.replace("$(images)",   imagesDir +"/" + imagesPrefix)
		css = css.replace("$(size)",     cornerSize)
		css = css.replace("$(cssclass)", cssClass)
		return css
	
	def roundRectangleHTML(self, className, start=True, end=False):
		if start:
			return ROUNDED_HTML_START.replace("CLASS", className)
		if end:
			return ROUNDED_HTML_END

# EOF
