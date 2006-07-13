#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: tw=80 ts=4 sw=4 noet
# -----------------------------------------------------------------------------
# Project           :   Tahchee                      <http://www.ivy.fr/tachee>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                     <sebastien@ivy.fr>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation  : 29-Mar-2006
# Last mod  : 29-Mar-2006
# History   :
#             29-Mar-2006 - First implementation
# -----------------------------------------------------------------------------

import sys ; sys.path.insert(0, "Sources")
from tahchee import main
from distutils.core import setup

SUMMARY     = "A static website build system"
DESCRIPTION = """\
Tahchee is a tool for developers and Web designers that makes it possible to
easily build a static Web site using the Cheetah template system. It is used to
fill in the gap between bare template and macro processing system and dynamic
template-based Web sites. It acts both as a build system (à la "make") as well
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

    author      = "Sebastien Pierre", author_email = "sebastien@ivy.fr",
    summary     = SUMMARY,
    description = DESCRIPTION,
    license     = "Revised BSD License",
    keywords    = "web, template, build, cheetah",
    url         = "http://www.ivy.fr/tahchee",
    package_dir = { "": "Sources" },
    packages    = ["tahchee", "tahchee.plugins"],
    scripts     = ["Scripts/tahchee"]

)

# EOF
