#!/usr/bin/python
# Encoding: ISO-8859-1
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project           :   Tahchee                     <http://www.ivy.fr/tahchee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Contibutors       :   Rafael Villar Burke                 <pachi@rvburke.com>
#                       Juan Fiol
# -----------------------------------------------------------------------------
# Creation date     :   20-Mar-2005
# Last mod.         :   27-Apr-2010
# -----------------------------------------------------------------------------

# Requires: Python 2.4, Cheetah
# Recommends: PIL, HTML Tidy

__version__ = "1.0.0"

def version(): return __version__

import os, sys, time, shutil, stat, pickle, glob, fnmatch, re, StringIO, webbrowser

try:
	from hashlib import sha1 as hashfunc
except ImportError,e:
	import sha as hashfunc

try:
	import Cheetah
	from Cheetah.Template import Template
	from Cheetah.Compiler import Compiler
	from Cheetah.Version import Version
	if Version.count(".") == 3:
		cheeta_ver = map(int, Version.split("."))
		if cheeta_ver[0]==0 and cheeta_ver[1] <= 9: assert cheeta_ver[2] >= 17
except:
	print "Cheetah 0.9.17+ is required. See <http://www.cheetahtemplate.org>"
	sys.exit()

CHANGE_CHECKSUM   ="signature"
CHANGE_DATE       ="date"
RE_ALWAYS_REBUILD = re.compile("^\s*##\s*ALWAYS_REBUILD\s*$")
RE_DEPENDS        = re.compile("^\s*##\s*DEPENDS\s*=(.+)$")

#------------------------------------------------------------------------------
#
# Logging functions
#
#------------------------------------------------------------------------------

def log( msg ):
	msg = str(msg)
	for l in msg.split("\n"):
		if not l: continue
		sys.stdout.write(" [ ] " + l + "\n")

def warn( msg ):
	msg = str(msg)
	for l in msg.split("\n"):
		if not l: continue
		sys.stdout.write("[0m[00;32m")
		sys.stdout.write(" [#] " + l )
		sys.stdout.write("[0m" + "\n")

def err( msg ):
	msg = str(msg)
	for l in msg.split("\n"):
		if not l: continue
		sys.stdout.write("[0m[00;31m")
		sys.stdout.write(" [!] " + l)
		sys.stdout.write("[0m" + "\n")

def fatal( msg ):
	err(msg)
	err("You will have to correct this error to build your website.")
	sys.exit(-1)

def info( msg ):
	log(msg)

#------------------------------------------------------------------------------
#
#  Utility functions
#
#------------------------------------------------------------------------------

def ensure_path(path):
	"""Ensures that the path is well-formed. In particular, it escapes spaces
	from the the path name."""
	return path.replace(" ", " ")

def shorten_path( path ):
	cwd = os.getcwd()
	if path.startswith(cwd): path = path[len(cwd) + 1:]
	return path

#------------------------------------------------------------------------------
#
#  Plugins Class
#
#------------------------------------------------------------------------------

class Plugins:
	"""A class that allows to easily manage plugins."""

	@classmethod
	def _instanciatePlugins(self, module, site=None):
		"""Private helper function."""
		p = []
		for plugin_name in dir(module):
			if not plugin_name.endswith("Plugin"): continue
			else: p.append(getattr(module, plugin_name)(site))
		return p

	@classmethod
	def list(self, pluginsDir=None, site=None):
		base_plugins   = os.path.join(os.path.dirname(__file__), "plugins")
		plugins = []
		# Parses the plugins in the tahchee.plugins directory
		for f in os.listdir(base_plugins):
			if not os.path.isfile(os.path.join(base_plugins, f)) or not f.endswith(".py"): continue
			m = None
			try:
				exec "import tahchee.plugins.%s as m" % (os.path.splitext(f)[0])
				plugins.extend(self._instanciatePlugins(m, site))
			except:
				pass
		# Now parses the plugins in the pluginsDir
		if pluginsDir and os.path.exists(pluginsDir):
			for f in os.listdir(pluginsDir):
				if not os.path.isfile(os.path.join(pluginsDir, f)) or not f.endswith(".py"): continue
				m = None ; exec "import %s as m" % (os.path.splitext(f)[0])
				plugins.extend(self._instanciatePlugins(m, site))
		return plugins

#------------------------------------------------------------------------------
#
#  Page Class
#
#------------------------------------------------------------------------------

class Page:
	"""The Page object is created by Tahchee and made available to Pages when
	each page is compiled. It holds information on the page content."""

	def __init__(self, name, path, url ):
		self._name = name
		self._path = path
		self._url  = url
		self.lastmod = None
	
	def name( self ):
		"""Returns this page name (the filename without the directory name)"""
		return self._name
	
	def path( self ):
		"""Returns the path to this page. The path is relative to the site
		root (that is the Pages directory)."""
		return self._path
	
	def url( self ):
		"""This is the relative or absolute URL of the page."""
		return self._url

	def htmlPath( self, sep="/" ):
		"""Returns an HTML string with links for the whole page path"""
		components = self.path().split("/")
		res        = []
		for c in components:
			link = "<a href='%s'>%s</a>" % (
				"/".join(components[:len(c)-1]),
				os.path.splitext(c)[0]
			)
			res.append("<span class='component'>%s</span>" % (link))
		return "<span class='location'>%s</span>" % (
			("<span class='sep'>%s</span>" % (sep)).join(res)
		)

#------------------------------------------------------------------------------
#
#  Site Class
#
#------------------------------------------------------------------------------

class Site:
	"""The site object holds all information relative to a website, which are:
	the pages directory, which contains the pages, the output directory where
	the pages will be generated, and the templates directory that holds the
	Cheetah templates used to generate the files."""

	def __init__( self, websiteURL, root=os.getcwd(), mode="local", locals=None, **kwargs ):
		"""Initializes this basic site object. Pages are stored under the "Pages"
		directory, output directory is "Site", templates are stored in
		"Templates", all in the site root directory."""
		self._name        = websiteURL
		self._websiteURL  = websiteURL
		self._mode        = mode
		self.rootDir      = ensure_path(os.path.abspath(root))
		self.pagesDir     = os.path.join(self.rootDir, "Pages")
		self.outputDir    = os.path.join(self.rootDir, "Site")
		self.templatesDir = os.path.join(self.rootDir, "Templates")
		self.fontsDir     = os.path.join(self.rootDir, "Fonts")
		self.pluginsDir   = os.path.join(self.rootDir, "Plugins")
		self.sourcesDir   = os.path.join(self.rootDir, "Sources")
		self._changeDetectionMethod = CHANGE_CHECKSUM
		self._plugins     = []
		self._accepts     = []
		self._ignores     = []
		self._indexes     = []
		self._tidy        = None
		self._tidyEnabled = True
		self._tidyConf    = os.environ.get("TIDYCONF") or ""
		self._tidyFlags   = os.environ.get("TIDYFLAGS") or ""
		self._main        = "index.html"
		self._showMain    = True
		self._processOptions(locals)
		self._processOptions(kwargs)
		# We insert the plugins directory into the Python modules path
		sys.path.insert(0, self.pluginsDir)
		sys.path.insert(0, self.sourcesDir)
		# This array contains a list of files created during the generation of
		# the templates. These files will be copied after the templates are
		# applied.
		self.createdFiles = []
		# This is a list of files that are remaining to be processed by the site
		# buidler when applying templates
		self._toProcess    = []
		sys.path.append(self.rootDir)

	def _detectHTMLTidy(self, tidypath):
		"""Utility function that looks if HTML tidy is installed"""
		tidypath = os.path.normpath(tidypath)
		try:
			_in, _out, _err = os.popen3("%s -v" % tidypath)
			if _out.read().strip():
				return tidypath
			else:
				return None
		except:
			return None

	def _processOptions( self, options ):
		if not options: return
		def has(k):
			return options.get(k) or options.get(k.upper()) or ""
		def m(k, a = None):
			if type(a) == list:
				if options.get(k): a.extend(options[k])
				if options.get(k.upper()): a.extend(options[k.upper()])
			else:
				if options.get(k): setattr(self, a, options[k])
				if options.get(k.upper()): setattr(self, a, options[k.upper()])
		m("accepts", self._accepts)
		m("ignores", self._ignores)
		m("indexes", self._indexes)
		m("tidyConf", "_tidyConf")
		m("tidyflags", "_tidyFlags")
		for tidy_path in [has("TIDY"), "tidy"]:
			tidy_path = self._detectHTMLTidy(tidy_path)
			if tidy_path is not None:
				self._tidy = tidy_path
				if self._tidy == "tidy":
					log("Found tidy in default path")
				else:
					log("Found tidy in %s" % self._tidy)
				break
		if has("USE_TIDY").lower() == "no" or not has("USE_TIDY") or not self._tidy:
			self._tidyEnabled = False
		if has("CHECKSUM").lower(): self._changeDetectionMethod = CHANGE_CHECKSUM
		if has("DATE").lower(): self._changeDetectionMethod = CHANGE_DATE
		if has("CHANGE").lower() == "date": self._changeDetectionMethod = CHANGE_DATE
		if has("CHANGE").lower().startswith("sig"): self._changeDetectionMethod = CHANGE_CHECKSUM
		if has("MAIN"): self._main = has("MAIN")
		if options.get("SHOW_MAIN") is False: self._showMain = False
		if options.get("SHOW_MAIN") is True: self._showMain  = True
		if self._tidyEnabled is False:
			warn("Tidy enables HTML file clean-up and compression but is disabled")
			warn("See the TIDY and TIDY_USE options or check tidy is your path")

	def willProcess( self, inputPath, outputPath=None, force=False ):
		"""Registers the given file to be processed by the SiteBuilder when
		applying templates."""
		inputPath  = os.path.abspath(inputPath)
		if outputPath: outputPath = os.path.abspath(outputPath)
		self._toProcess.append((inputPath, outputPath, force))

	def nextToProcess( self ):
		"""Returns a triple (inputpath, outputpath, force) that indicates the
		next file that should be processed by the builder. This is an iteration
		method, which means that if the file is not processed and not re-added
		using 'willProcess' it will not be processed."""
		res = self._toProcess[0]
		self._toProcess = self._toProcess[1:]
		return res

	def hasToProcess( self ):
		"""Tells if there are remaining files to be processed."""
		return len(self._toProcess) > 0

	def accepts( self, *args ):
		"""Adds the glob and specifies that it is accepted as a file by this
		site."""
		self._accepts.extend(args)

	def ignores( self, *args ):
		"""The given globs idenitfy files that won't be accepted by this
		site."""
		self._ignores.extend(args)

	def index( self, *args ):
		"""Tells that the given globs match index files."""
		self._indexes.extend(args)

	def isIndex( self, path ):
		"""Tells wether the given path corresponds to an index or not."""
		path = os.path.basename(path)
		for index in self._indexes:
			if fnmatch.fnmatch(path, index):
				return True
		return False

	def isAccepted( self, path ):
		"""Tells wether this file is accepted or not."""
		if path[-1] == "/": path = path[:-1]
		path = os.path.basename(path)
		if not path: path = os.path.basename(os.path.dirname(path))
		for ignores in self._ignores:
			if fnmatch.fnmatch(path, ignores): return False
		if self._accepts:
			for accepts in self._accepts:
				if fnmatch.fnmatch(path, accepts): return True
			return False
		else:
			return True

	def isTemplate( self, path ):
		"""Tells if the given path represents a template, and returns the
		result."""
		res = path.split(".tmpl")
		if len(res) == 2:
			return "".join(res)
		else:
			return None

	def templates( self ):
		"""Returns a list of Cheetah templates (files ending in .tmpl or like
		.tmpl.xxxx) contained in the templates directory."""
		if not os.path.exists(self.templatesDir):
			err("Templates directory does not exist: " + self.templatesDir)
		# Ensures that the "__init__.py" exists
		if not os.path.exists(self.templatesDir + "/__init__.py"):
			log("Generating templates Python module:"
				+ self.templatesDir + "/__init__.py")
			f = open(self.templatesDir + "/__init__.py", "wb")
			f.write("# Generated by Tahchee\n")
			f.close()
		for file_or_dir in os.listdir(self.templatesDir):
			current_path = os.path.join(self.templatesDir, file_or_dir)
			if not os.path.isdir( current_path ):
				if current_path.endswith(".tmpl"):
					#templates.append(current_path)
					yield current_path
		#return templates

	def plugins( self ):
		"""Returns a list of plugin instances that were detected for this
		site."""
		if self._plugins: return self._plugins
		self._plugins = Plugins.list(self.pluginsDir, self)
		return self._plugins

	def changeDetectionMethod( self ):
		"""Returns the type of file change detection method. The 'cheksum'
		method computes the SHA-1 signature for the file, while the
		'modification' method uses the file last modification time."""
		return self._changeDetectionMethod

	def useTidy( self ):
		"""Tells wether this site should use tidy to postprocess HTML
		templates."""
		return self._tidyEnabled

	def root( self ):
		"""Returns the root directory for this site."""
		return self.rootDir

	def pages( self ):
		"""Returns the pages directory for this site."""
		return self.pagesDir

	def output( self ):
		"""Returns the output directory for this site."""
		if self.mode() == "local":
			return self.outputDir + "/Local"
		else:
			return self.outputDir + "/Remote"

	def name( self ):
		"""Returns the name for this website."""
		return self._name

	def url( self ):
		"""Returns the URL for this website."""
		return self._websiteURL

	def setMode( self, mode ):
		"""Sets the mode to be local or remote. Mode is local by default."""
		self._mode = mode

	def mode( self ):
		"""Returns the site mode, which is local by default."""
		return self._mode

	def sig( self ):
		"""Returns this site signature as a string. The signature uniquely
		identifies this site. Each instance has a different signature."""
		sig =  self.pages() + self.output() + self.templatesDir
		return hashfunc.new(sig).hexdigest()

	def absolutePath( self, path="" ):
		"""Returns the absolute normalized path for the given path, which must
		be relative to the current site root. When called with no argument, the
		site root is returned."""
		return os.path.normpath(os.path.join(self.root, path))

	def log(self,msg): log(msg)
	def err(self,msg): err(msg)
	def error(self,msg): err(msg)
	def info(self,msg): info(msg)
	def warn(self,msg): warn(msg)
	def warning(self,msg): warn(msg)
	def fatal(self,msg): fatal(msg)

#------------------------------------------------------------------------------
#
#  SiteBuilder Class
#
#------------------------------------------------------------------------------

class SiteBuilder:
	"""The SiteBuilder is the core of Tahchee, it uses the informations stored
	in the Site object from which it is initialized to build the web pages."""

	def __init__( self, site ):
		"""Creates a new site builder that will create the HTML (and whatever
		other file types) from the website description held in the site
		object."""
		self.site = site
		# Appends the site root to the Python module seach path, so that any
		# subdirectory of the root containing Python modules will be accessible
		# in Cheetah templates.
		if self.site.root() not in sys.path: sys.path.append(self.site.root())
		# The checksums allow to track changes made to resource and files
		self.checksums = {}
		self.changed   = {}
		self.loadChecksums()

	# ------------------------------------------------------------------------
	#
	# File detection module
	#
	# ------------------------------------------------------------------------

	def hasChanged( self, path ):
		"""Tells wether the given resource has changed since last build for this
		website or not. The path is converted to an absolute location, so
		moving the website directory will cause a rebuild."""
		# Maybe we already know if the path has changed
		path = os.path.abspath(path)
		res  = self.changed.get(path) 
		if not self.site.isTemplate(path) and res != None:
			return res
		data = None
		def load_data(path):
			fd  = file(path, 'r')
			res = fd.read()
			fd.close()
			return res
		# Is the page a template ?
		template_has_changed = res or False
		if self.site.isTemplate(path):
			data = load_data(path)
			# If so, we look for the extends defintion
			template = None
			for line in data.split("\n"):
				line = line.strip()
				if line and not line.startswith("##") and not line.startswith("#extends"): break
				if line.startswith("#extends"):
					template = line.strip()[len("#extends"):].strip()
				# If the template was flagged with ALWAYS_REBUILD, then we force
				# the build
				if RE_ALWAYS_REBUILD.match(line):
					template_has_changed = True
					break
				depends = RE_DEPENDS.match(line)
				# Handles dependencies
				if depends:
					dep_path = depends.group(1).strip()
					dep_path = os.path.expanduser(dep_path)
					dep_abspath = os.path.abspath(dep_path)
					# The path may be relative to the current path
					if dep_abspath != dep_path:
						dep_abspath = os.path.abspath(os.path.dirname(path) + "/" + dep_path)
					dep_path = dep_abspath
					for dependency in glob.glob(dep_path):
						if self.hasChanged(dependency):
							template_has_changed = True
							break
					if template_has_changed: break
			# If there was a template extended, we check if it is present in the
			# templates directory
			if template and template.startswith("Templates"):
				template_path = apply(os.path.join, template.split(".")[1:])
				template_path = os.path.join(self.site.templatesDir, template_path + ".tmpl")
				# And if this template has changed, then this one too
				if self.hasChanged(template_path):
					template_has_changed = True
		# There is a SHA1 mode for real checksum change detection
		if self.site.changeDetectionMethod() == CHANGE_CHECKSUM:
			chksum = hashfunc.new(data or load_data(path)).hexdigest()
		# Default is modification time (faster)
		else:
			if os.path.exists(path):
				chksum  = os.stat(path)[stat.ST_MTIME]
			else:
				warn("Path does not exists: " + path)
				chksum  = "0"
		# We get the previous checksum
		checksums = self.checksums.get(self.site.sig())
		if checksums:
			old_checksum = checksums.get(path)
		else:
			old_checksum = None
		# Then we compare to registered checksums
		# If the checksum has changed
		if template_has_changed or old_checksum != chksum:
			# We take care of the mode
			if not self.checksums.get(self.site.sig()):
				self.checksums[self.site.sig()] = {}
			self.checksums[self.site.sig()][path] = chksum
			self.changed[path] = True
			return True
		else:
			self.changed[path] = False
			return False

	def saveChecksums( self ):
		"""Saves the cheksums to a file named 'site.checksums' in the site
		root."""
		path = os.path.join(self.site.root(), "site.checksums")
		fd = open(path, "wb")
		pickle.dump(self.checksums, fd, pickle.HIGHEST_PROTOCOL)
		fd.close()

	def loadChecksums(self):
		"""Loads the cheksums from a file named 'site.checksums' in the site
		root."""
		path = os.path.join(self.site.root(), "site.checksums")
		if os.path.exists(path):
			fd = open(path, "rb")
			res = pickle.load(fd)
			fd.close()
			assert type(res) == type(self.checksums)
			self.checksums = res

	# ------------------------------------------------------------------------
	#
	# Building the web site
	#
	# ------------------------------------------------------------------------

	def build( self, paths=None):
		"""Builds the website, or builds specifically the given paths."""
		log("Mode is '%s', generating in '%s'" % (self.site.mode(),
		shorten_path(self.site.output())))
		log("Changes are detected by %s" % (self.site.changeDetectionMethod()))
		self.usedResources = {}
		self.precompileTemplates()
		self.applyTemplates(paths)
		self.copyCreatedFiles()
		self.saveChecksums()
		if self.site._showMain:
			webbrowser.open("file://" + os.path.join(self.site.output(), self.site._main))

	def precompileTemplates( self ):
		"""Looks for Cheetah templates and precompile them (into Python code)
		if necessary"""
		# Iterates on the site templates
		for template in self.site.templates():
			filename = os.path.basename(os.path.splitext(template)[0])
			# Templates are only compiled if they were not previouly compiled or
			# if the changed.
			if self.hasChanged(template) or \
			not os.path.exists(os.path.splitext(template)[0]+".py"):
				log("Precompiling template '%s'" % (shorten_path(os.path.splitext(template)[0])))
				temp = Compiler(
					file=template,
					moduleName=filename,
					mainClassName=filename
				)
				try:
					temp = str(temp)
				except Cheetah.Parser.ParseError, e:
					fatal(e)
					temp = None
				if temp != None:
					output = open(os.path.splitext(template)[0]+".py", "wb")
					output.write("# Encoding: ISO-8859-1\n" + str(temp))
					output.close()

	def applyTemplates( self, templatePaths=None):
		"""Apply the templates to every page template present in the pages
		directory."""
		# Iterates on the given files
		if templatePaths:
			for path in templatePaths:
				path = os.path.abspath(path)
				# If the path is not contained within the pages, it has no
				# basedir, and we force the rebuild anyway
				if not path.startswith(os.path.abspath(self.site.pages())):
					self.site.willProcess(path, None, True)
				# Otherwise it is a page, and we rebuild it
				else:
					self.site.willProcess(path, None ,True)
		# Otherwise we do that for the Pages
		else:
			for root, dirs, files in os.walk(os.path.join(self.site.pages())):
				for f in files: self.site.willProcess(os.path.join(root, f))
		# And we eventually process the pages we have to process
		while self.site.hasToProcess():
			input_path, output_path, force = self.site.nextToProcess()
			# If not output path was specified and that input was within the
			# Pages directory, then we update the output path
			if not output_path and input_path.startswith(self.site.pages()):
				output_path = os.path.join(self.site.output(), input_path[len(self.site.pages())+1:])
			# We process the file
			self.processFile( input_path, output_path, force )

	def copyCreatedFiles( self ):
		"""Copies the files created during the application of templates."""
		map(self.processFile, self.site.createdFiles)
	
	def processFile( self, inputpath, outputpath, force=False ):
		"""Processes the given file, which is relative to the pages directory.
		If it is a .tmpl file, the template will be applied, otherwise, the file
		is just copied.
		
		The given file must be given WITHIN the pages directory
		"""
		ifile = inputpath
		ofile = outputpath
		filename = os.path.basename(ifile)
		# We test if the file is accepted
		if not force and not self.site.isAccepted(ifile):
			log("Skipping '%s'" % (shorten_path(ifile)))
			return False
		# We ensure that it is not a directory
		if not os.path.isdir(ifile):
			# If there is a page template, then we simply apply it
			if self.site.isTemplate(filename):
				self.applyTemplate(ifile, force)
			# If it is a resource, we simply copy it
			elif force or self.hasChanged( ifile ):
				info("Copying  '%s'" % (ofile))
				dest_dir  = os.path.dirname(ofile)
				if not os.path.exists(dest_dir): os.makedirs(dest_dir)
				shutil.copyfile(ifile, ofile)
		# If we found a directory, we recurse
		else:
			if not os.path.exists(ofile):
				os.makedirs(ofile)
				log("Creating '%s'" % (shorten_path(ofile)))
			self.applyTemplates(filepath)

	def applyTemplate( self, template, force=False ):
		"""Expands the given template to a file (generally an HTML or CSS
		file). The given path must be absolute."""
		assert template == os.path.abspath(template), "Path must be absolute"
		# The local path is the path to the template that is relative to the
		# site pages directory. The template extension is removed.
		template_localpath  = self.site.isTemplate(template[len(self.site.pages())+1:])
		template_url        = template_localpath
		# The template outputpath corresponds to the file that will be created
		# after expanding the template.
		template_outputpath = os.path.join(self.site.output(), template_localpath)
		template_outputpath.replace(" ", "\ ")

		# We do nothing if the template was already applied
		if not force and not self.hasChanged( template ) \
		and os.path.exists(template_outputpath):
			return

		# And create a dictionary with the file attributes. This dictionnary
		# will be available to every template.
		path = template_localpath
		name = os.path.basename(template_localpath)
		url  = self.site.url() + "/" + template_url
		page = Page(name, path, url)

		lmod = time.localtime(os.stat(template)[stat.ST_MTIME])
		page.lastmod = time.strftime("%d-%b-%Y", lmod)
		localdict = {
			"page" : page,
			"site" : self.site
		}
		for plugin in self.site.plugins():
			plugin.install(localdict)

		# We generate the page
		log("Generating file '%s'" % (shorten_path(template_localpath)))
		try:
			template = Template(file=template, searchList=[localdict])
		except ImportError, e:
			err("Unable to compile template.")
			err("This may be because an extended template did not compile.")
			err("Python says: " + str(e))
			return

		# template._searchList.append(localdict)
		# Adds a "self" in the template
		localdict["self"] = template

		# In case the template output path directories do not exist, we ensure
		# that they are present.
		if not os.path.exists(os.path.dirname(template_outputpath)):
			os.makedirs(os.path.dirname(template_outputpath))

		def generate(template, template_outputpath):
			assert isinstance(template, Template)
			output = open(template_outputpath, "wb")
			#try:
			template_text = str(template)
			if not template_text:
				warn("Template output is empty, you may want to check your template code.")
			output.write(template_text)
			output.close()
			#except Exception, e:
			#	# FIXME: Get the exception name
			#	err("Cannot generate template: " + str(e))
			#	import traceback
			#	traceback.print_last()
			#	return False
			return True

		# If the template destination file ends in html, we may use tidy to
		# post-process it
		if os.path.splitext(template_outputpath)[1].lower() in (".html", ".htm"):
			if generate(template, template_outputpath + ".tmp"):
				if self.site.useTidy():
					flags = ""
					if self.site._tidyConf:  flags += " -f '%s'" % (self.site._tidyConf)
					if self.site._tidyFlags: flags += " " + self.site._tidyFlags
					_in, _out, _err = os.popen3("%s %s %s > %s" % (
						self.site._tidy,
						flags,
						template_outputpath+".tmp", template_outputpath)
					)
					# Cut the crap out of HTML tidy output
					errors = _err.read().split("\n")
					warn("\n".join(errors[:-7]))
					# TODO: LOOK FOR
					# 4 warnings, 0 errors were found!
					# summary  = errors[-10]
					# print "SU???", summary
					# warnings, errors = summary.split(",")
					# warnings = int(warnings.strip().split()[0])
					# errors   = int(errors.strip().split()[0])
					# if errors > 0:
					# 	# If there was a failure, we do not create the file
					# 	os.unlink(template_outputpath)
					# 	err(summary)
					# else:
					# 	warn(summary)
				else:
					shutil.copy(template_outputpath+".tmp", template_outputpath)
				os.unlink(template_outputpath+".tmp")
				return True
			else:
				return False
		# Otherwise we simply output the file
		else:
			return generate(template, template_outputpath)

#------------------------------------------------------------------------------
#
#  Templates
#
#------------------------------------------------------------------------------

MAKEFILE_TEMPLATE = """\
# Tahchee makefile template version %s
PYTHON  = /usr/bin/env python
LOCAL   = Site/Local
REMOTE  = Site/Remote

local:
	$(PYTHON) build.py local

remote:
	$(PYTHON) build.py remote

clean:
	find . -name "*~" -or -name "*.sw?" -or -name "*.pyc" -exec rm {} ';'
	rm -rf $(LOCAL)/*
	rm -rf $(REMOTE)/*
	rm site.checksums

info:
	@echo 'local    - builds local website'
	@echo 'remote   - builds remote website'
	@echo 'clean    - cleans build and removes temp files'

archive: Pages Templates Makefile build.py 
	mkdir tahchee-sources
	cp -r Pages Templates Makefile build.py tahchee-sources
	tar cvfj tahchee-sources.tar.bz2 tahchee-sources
	rm -rf tahchee-sources

.PHONY: local remote archive info clean 
""" % ( __version__ )

BUILD_PY_TEMPLATE = """\
#!/usr/bin/env python
import os, sys
# We add the Plugins path to the current Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Plugins"))
try:
	from tahchee.main import *
except:
	print "Unable to import Tahchee."
	print "Please check that the 'tahchee' module is in your PYTHONPATH"
	sys.exit(-1)
# You can change the following things
# =============================================================================
%s
# =============================================================================
# Do not modify this code
if __name__ == "__main__":
	print "tahchee v." + version()
	site = Site(URL, locals=locals())
	if len(sys.argv)>1 and sys.argv[1].lower()=="remote": site.setMode("remote")
	SiteBuilder(site).build(filter(lambda x:x not in ('local','remote'),sys.argv[1:]))
"""

BUILD_PY_DEFAULTS = """\
URL       = "%s"
MAIN      = "index.html"
SHOW_MAIN = True
INDEXES   = ["index.*"]
IGNORES   = ["*.sw?", "*.bak", "*.pyc", ".cvs", ".CVS", ".svn", ".DS_Store"]
ACCEPTS   = []"""


BASE_TMPL ="""\
## This is how we create a function in Cheetah. Here, the $site object is 
## a reference to Tahchee Site instance representing the current site. This
## instance has a "link" method that allows to create a relative or absolute
## link (depending on the mode - e.g. local or remote) in which the site is
## built
#def link(destination)
$linking.link($page.path, $destination)#slurp
#end def
#def keywords
ENTER KEYWORDS HERE
#end def
#def head
#end def
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="fr">
<head>
  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type" />
  <title>$title</title>
  <meta name="keywords" content="$keywords" />
  <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
  <link rel="Shortcut Icon" href="$link('images/favicon.ico')" type="image/x-icon" />
  <link rel="Stylesheet" title="Normal" media="screen" type="text/css" href="$link('screen.css')" />
  <link rel="start" title="Home" href="index.html" />
  $head
</head>
<body>
$body
</body>
</html>
"""

PAGE_TMPL ="""\
## Here, we "extend" the base template, this is like an inhertiance between
## page templates. Templates are all located in the Templates module, so
## here, we simply say "this template extends the template Base.tmpl in the
## Templates directory"
#extends Templates.Base
#def header
ENTER HEADER HERE
#end def
#def content
ENTER CONTENT HERE
#end def
#def footer
ENTER FOOTER HERE
#end def
#def body
<div id="header">$header</div>
<div id="content">$content</div>
<div id="footer">$footer</div>
#end def
"""

INDEX_HTML = """\
#extends Templates.Page
#def title: Welcome to Tahchee
#def header: <a href="http://www.ivy.fr/tahchee">Tahchee</a> v.%s

#def content
<h1>Welcome to Tahchee</h1>

<p><a href="http://www.ivy.fr/tahchee">Tahchee</a>  is build system and an
set of extensions to the <a href="http://www.cheetahtemplate.org">Cheetah</a>
template system.
</p>

<p>This page was created by the default templates provided, and will help you
understand how to get started with Tahchee.</p>

<p>You can get more information by reading the <a
href="http://www.ivy.fr/tahchee/manual.html">Tahchee Manual</a>. </p>

#end def
#def footer
<a href="http://www.ivy.fr/tahchee">Tahchee</a> &copy; <a href="http://www.ivy.fr">Ivy</a>, 2004-2006-.
#end def
""" % (__version__)

SCREEN_CSS = """\
body{
	margin-left:10%;
    margin-right:10%;
    padding:20pt;
    padding-top:10pt;
    background:rgb(255,255,255);
    font: 9pt/13pt "Lucida Grande",Lucida,sans-serif;
    color:rgb(80,80,80);;
}

h1,
h2,
h3,
h4{
	font-family:"Trebuchet MS",sans-serif;
    color:rgb(22, 130, 178);
    font-weight:normal;
    padding-top:0.5em;
}

strong{
	color:rgb(103,183,0);
}

a,
a:active,
a:visited{
	color:rgb(22,130,178);
	text-decoration:none;
}
a:hover{
	text-decoration:underline;
}

a img{
	border:0;
}


#header, #footer{
	font-size:7pt;
	clear:both;
	width:100%;
	color:rgb(177,208,223);
}

#footer{
	padding-top: 30pt;
	text-align:right;
}
"""
#------------------------------------------------------------------------------
#
#  Help
#
#------------------------------------------------------------------------------

HELP = """\
Tahchee v.%s 

   allows to automatically build static websites from Cheetah templates. It
   features many useful function, such as relative or absolute linking, image
   generation, and automated build.

Usage:

   tahchee create URL [DIRECTORY]     (Creates a new website)
   tahchee update [DIRECTORY]         (Updates website tahchee files)
   tahchee plugins                    (Lists available plugins)
   tahchee help [COMMAND]             (Displays command help)
   tahchee version                    (Displays version info)

Links:

   <http://www.ivy.fr/tahchee>        Tahchee website
   <http://www.cheetahtemplate.org>   Cheetah website
""" % (__version__)

HELP_CREATE = """\
tahchee create URL [DIRECTORY]

   Creates a new Tahchee projet in the current directory or in the
   indicated directory.
   
   URL         the URL of your website (eg. http://www.mysite.org)
   DIRECTORY   the directory in which you want to create your project
   
   The directory will then hold a 'Makefile' file that you can simply
   call with the 'make' tool.will  It will also be filled with the
   following subdirectories:

   Templates/   where you store all your page templates
   Pages/       your site Cheetah pages, CSS files, images, etc.
   Site/Local/  the version of your site made for local testing
   Site/Remote/ the version of your site made for uploading to remote site
   Fonts/       where you put your .ttf files
   Plugins/     drop your Python modules in here
"""

HELP_UPDATE = """\
tahchee update [DIRECTORY]

   Updates your Tahchee project (`build.py` file and `Makefile`) so that it
   will work with the updated version of Tahchee.

   It is a good idea to run this command on your projects each time you
   update Tahchee.
"""

HELP_PLUGINS = """\
tahchee plugins

   Displays the list of the plugins that Tahchee found for your local project.
   This will look both for the default Tahchee plugins, and for the ones found
   in your project `Plugins` directory.
"""
#------------------------------------------------------------------------------
#
#  Main
#
#------------------------------------------------------------------------------

def run( args ):
	if not args:
		print HELP[:-1]
		sys.exit()

	# Checks the number of arguments
	if args[0] == "create" and len( args ) < 2 or len( args) > 3 \
	or args[0] == "update" and len( args ) > 2:
		print HELP[:-1]
		sys.exit()
	
	directory = os.getcwd()
	# The write function only creates a file if it does not exist
	def write( path, data ):
		if os.path.exists(path): return
		fd = open(path, "wb")
		fd.write(data)
		fd.close()

	# ========================================================================
	# UPDATE MODE
	# ========================================================================
	if args[0] == "create":
		# Gets the websiteurl
		websiteurl = args[1]
		# Gets the destination directory
		if len ( args ) == 3: directory = args[2]
		# Checks that the directory is empty or not exists
		if not os.path.exists(directory):
			if not os.path.exists(os.path.dirname(os.path.abspath(directory))):
				print "Parent directory does not exist. Please create it."
				sys.exit()
			else:
				os.mkdir( directory )
		write( directory + "/Makefile", MAKEFILE_TEMPLATE)
		write( directory + "/build.py", BUILD_PY_TEMPLATE  % (BUILD_PY_DEFAULTS
		% (websiteurl)))
		for subdir in "Pages Templates Site/Local Site/Remote".split():
			path = os.path.join(directory, subdir)
			if not os.path.exists(path): os.makedirs(path)
		write( directory + "/Templates/Base.tmpl", BASE_TMPL)
		write( directory + "/Templates/Page.tmpl", PAGE_TMPL)
		write( directory + "/Pages/index.html.tmpl", INDEX_HTML)
		write( directory + "/Pages/screen.css", SCREEN_CSS)
		print "Tahchee site '%s' project files created in %s" % (websiteurl, directory)
		print "  The site is filled with sample templates and pages"
		print "  You can now go there and type 'make info' to learn what you can do."
	
	# ========================================================================
	# UPDATE MODE
	# ========================================================================
	elif args[0] == "update":
		if len ( args ) == 2: directory = args[1]
		build_py = directory + "/build.py"
		user_configuration = None
		if not os.path.exists(build_py):
			print "Tahchee expected to find at least a 'build.py' in this directory"
		else:
			f = file(build_py, "r")
			for line in f:
				if line.strip().startswith("# =========="):
					if user_configuration == None:
						user_configuration = ""
					else:
						break
				elif user_configuration != None:
					user_configuration += line 
			if user_configuration: user_configuration = user_configuration[:-1]
			else: user_configuration = ""
			f.close()
		if not user_configuration:
			print "Your build.py was regenerated. The old version was moved to 'build.old'"
			user_configuration = BUILD_PY_DEFAULTS % ("http://www.mysite.org")
			shutil.copy(build_py, os.path.splitext(build_py)[0] + ".old")
		if os.path.exists(build_py): os.unlink(build_py)
		write(build_py , BUILD_PY_TEMPLATE  % (user_configuration))
		if not user_configuration:
			print "Please edit your new build.py configuration file."
		else:
			print "Your project was updated."
	# ========================================================================
	# UPDATE MODE
	# ========================================================================
	elif args[0] == "plugin" or args[0] == "plugins":
		data = []
		print "Available plugins:"
		for plugin in Plugins.list():
			data.append((plugin.name(), plugin.version() or __version__, plugin.summary()))
		for n, v, d in data:
			print " - %-15s %-6s %s" % (n, v, d)
	# ========================================================================
	# HELP MODE
	# ========================================================================
	elif args[0] in ("help" "--help"):
		if len(args) == 1:
			print HELP
		else:
			command = args[1].lower()
			if   command == "create": print HELP_CREATE
			elif command == "update": print HELP_UPDATE
			elif command == "plugin": print HELP_PLUGIN
			elif command == "version": print __version__
			elif command == "help": print HELP
			else: print "Unknown command: ", command
	elif args[0] in ("version" "--version"):
		print "tahchee " + __version__

if __name__ == "__main__":
	args = sys.argv[1:]
	run(args)

# EOF
