# Tahchee makefile template version 0.9
PYTHON  = /usr/bin/env python
LOCAL	= Site/Local
REMOTE	= Site/Remote

local:
	$(PYTHON) build.py local

remote:
	$(PYTHON) build.py remote

clean:
	find . -name "*~" -or -name "*.sw?" -or -name "*.pyc" -exec rm {} ';'
	find Templates -name "*py" -exec rm {} ';'
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
