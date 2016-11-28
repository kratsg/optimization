# simple makefile to simplify repetitive build env management tasks under posix
PYTHON := $(shell which python)
all: install

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
