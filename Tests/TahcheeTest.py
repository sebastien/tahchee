#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project   : Tahchee tests
# -----------------------------------------------------------------------------
# Author    : Sebastien Pierre
# Creation  : 20-Feb-2006
# Last mod  : 21-Feb-2006
# History   : 21-Feb-2006 - Enhanced when test case generate big output
#             20-Feb-2006 - First implementation
# -----------------------------------------------------------------------------

import os, re, time

TEST_FILE  = re.compile("^([A-Z][0-9]+)\-(\w+)\.py$")
TEST_FILES = {}

def do():
	# We populate the test files hash table
	this_dir = os.path.abspath(os.path.dirname(__file__))
	for path in os.listdir(this_dir):
		m = TEST_FILE.match(path)
		if not m: continue
		f = TEST_FILES.setdefault(m.group(1), [])
		f.append((m.group(2), os.path.join(this_dir, path)))

	# And now execute the tests
	groups = TEST_FILES.keys() ; groups.sort()
	for group in groups:
		for test, test_path in TEST_FILES[group]:
			print "%4s:%20s " % (group, test),
			potime = time.time()
			inp, out, err = os.popen3("python " + test_path)
			err  = err.read()
			res  = ""
			data = out.read()
			while data:
				if data: res += data
				data = out.read()
			if err.strip() == "" and res.split("\n")[-2].strip() == "OK":
				print "[OK]",
				print "in %.3f secs." % (time.time() - potime)
			else:
				print "[FAILED] after", time.time() - potime, "secs."
				print "%s\n " % (repr(err))

if __name__ == "__main__":
	do()

# EOF
