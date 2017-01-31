# simple makefile to simplify repetitive build env management tasks under posix
PYTHON := $(shell which python)
GIT := $(shell which git)
VERSION := $(shell $(PYTHON) -c "from root_optimize import __version__; print __version__")

register:
	@$(PYTHON) setup.py register

sdist: clean
	@$(PYTHON) setup.py sdist

upload: clean
	@$(PYTHON) setup.py sdist upload

clean:
	@$(PYTHON) setup.py clean
	rm -rf build

install: clean
	@$(PYTHON) setup.py install

test: install
	@$(PYTHON) setup.py test

tag:
ifeq ($(shell $(GIT) tag -l ${VERSION}),)
	$(GIT) tag -a ${VERSION} -m "${VERSION}"
else
	$(error "Already tagged version ${VERSION}")
endif
