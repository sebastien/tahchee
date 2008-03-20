#!/usr/bin/python
# Encoding: ISO-8859-1
# vim: tw=80 ts=4 sw=4 fenc=latin-1 noet
# -----------------------------------------------------------------------------
# Project           :   Tahchee                     <http://www.ivy.fr/tahchee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   20-Mar-2005
# Last mod.         :   08-May-2007
# -----------------------------------------------------------------------------

import sys ; sys.path.insert(0, "Sources")
from tahchee import main
from distutils.core import setup

SUMMARY     = "Automated static and dynamic web site creation tool"
DESCRIPTION = """\
Tahchee is a tool for developers and Web designers that makes it possible to
easily build a static Web site using the Cheetah template system. It is used to
fill in the gap between bare template and macro processing system and dynamic
template-based Web sites. It acts both as a build system (a la "make") as well
as an extension to the Cheetah template that makes it really easy to build small
to medium-sized sites. It is ideal for writing open source project or small
company Web sites.\
"""
# ------------------------------------------------------------------------------
#
# SETUP DECLARATION
#
# ------------------------------------------------------------------------------

setup(
    name        = "Tahchee",
    version     = main.__version__,
    author      = "Sebastien Pierre", author_email = "sebastien@type-z.org",
    description = SUMMARY, long_description = DESCRIPTION,
    license     = "Revised BSD License",
    keywords    = "web, Cheetah, automated, static, dynamic, build",
    url         = "http://www.ivy.fr/tahchee",
    download_url= "http://www.ivy.fr/tahchee/tahchee-%s.tar.gz" % (main.__version__) ,
    package_dir = { "": "Sources" },
    package_data= { "tahchee.plugins._kiwi": ["*.css"] },
    packages    = ["tahchee", "tahchee.plugins", "tahchee.plugins._kiwi"],
    scripts     = ["Scripts/tahchee"],
    classifiers = [
      "Development Status :: 4 - Beta",
      "Environment :: Web Environment",
      "Intended Audience :: Developers",
      "Intended Audience :: Information Technology",
      "License :: OSI Approved :: BSD License",
      "Natural Language :: English",
      "Topic :: Internet :: WWW/HTTP :: Site Management",
      "Topic :: Software Development :: Build Tools",
      "Topic :: Text Processing :: Markup",
      "Operating System :: POSIX",
      "Operating System :: Microsoft :: Windows",
      "Programming Language :: Python",
    ]
)

# EOF
