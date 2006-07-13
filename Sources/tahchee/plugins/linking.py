# vim: ts=4
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   25-Feb-2006
# Last mod.         :   20-Mar-2006
# History           :
#                       20-Mar-2006 Rewrote the link function
#                       13-Mar-2006 Added index support
#                       25-Feb-2006 First implementation
# Bugs              :
# To do             :


import os, sys

class LinkingPlugin:

	def __init__( self, site ):
		self.site = site
	
	def install( self, localdict ):
		localdict["linking"] = self

	def hierarchy( self, pagePath ):
		"""Creates an HTML string that contains the clickable path from the
		website root to the current page. This can be placed in a navigation
		bar."""

		parents  = (pagePath.split("/"))
		page     = parents[-1]
		parents  = parents[:-1]

		# The first element is the site root
		res = "<a href='%s'>%s</a> / " %\
		( self.link(pagePath, "/index.html"), self.name())
		path = ""

		# Now we add links for the parents
		for path_index in range(0, len(parents)):
			path += parents[path_index] + "/"
			res += "<a href='%s'>%s</a> / " % (
				self.link(pagePath,
				path+"/index.html"),
				parents[path_index]
			)

		# We add the last link ofr the file
		radix = os.path.splitext(page)
		if radix!="index":
			return res+"<a href='%s'>%s</a> " % (
				self.link(pagePath, radix), radix
			)
		else:
			# We get rid of the trailing " / "
			return res[:-3]

	def _abspath( self, path ):
		"""Ensures that the path is absolute. This does not use the Python
		os.abspath method, but simply ensures that the path does not starts with
		'.' and starts with a '/'."""
		if not path: return "/"
		if path[0] == ".": path = path[1:]
		if not path or not path[0] == "/": path = "/" + path
		return path

	def a( self, target, content ):
		return "<a href='%s'>%s</a>" % (target, content)

	def link( self, fromPath, toPath, checkLink=True ):
		"""Creates a relative or absolute link (if the site is in local mode,
		then the link is relative, otherwise it is absolute) from the given path
		to the other path. The 'fromPath' is RELATIVE TO THE PAGES DIRECTORY."""
		# WE SHOULD ASSERT THAT FROM PATH IS A FILE, OR IF IT IS A DIRECTORY, IT
		# MUST END WITH /
		fromPath = self._abspath(fromPath)
		toPath   = self._abspath(toPath)
		# Now, all paths are of the form
		# - '/'
		# - '/FILE' or '/DIR'
		# - '/DIR/FILE' or '/DIR/DIR'
		# - ...
		from_el   = fromPath.split("/")[1:]
		to_el     = toPath.split("/")[1:]
		from_dirs = len(from_el) > 1 and from_el[:-1] or []
		to_dirs   = len(to_el) > 1 and to_el[:-1] or []
		from_file = from_el[-1]
		to_file   = to_el[-1]
		common    = -1
		for c in range(0, min(len(from_dirs), len(to_dirs))):
			if from_dirs[c] != to_dirs[c]:
				break
			common = c
		# If there is no "to_file", we force the "/"
		if not to_file: to_file = "/"
		# Both paths have the same directories in common
		if from_dirs == to_dirs:
			return to_file
		else:
			prefix  = ""
			if common == -1:
				prefix += "../" * (len(from_dirs))
				prefix += "/".join(to_dirs)
			else:
				common += 1
				prefix += "../" * (len(from_dirs[common:]))
				if common < len(to_dirs):
					prefix +=  "/".join(to_dirs[common:])
			if prefix and not prefix[-1] == "/": prefix += "/"
			return prefix + to_file

# EOF