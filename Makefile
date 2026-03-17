PYTHON ?= python
PUBLISH ?= /storage2/arash/infra/bin/publish_pypi.sh
DATALAD ?= /storage/share/python/environments/Anaconda3/envs/cogpy/bin/datalad
MSG ?= Update projio

RUNTIME_PATH := $(patsubst %/,%,$(dir $(DATALAD))):$(patsubst %/,%,$(dir $(PYTHON))):$(patsubst %/,%,$(dir $(PUBLISH)))
export PATH := $(RUNTIME_PATH):$(PATH)

.PHONY: help urls dev test docs docs-serve build check clean publish publish-test \
       save status pull-origin push-origin pull-gitlab push-gitlab

help:
	@printf '%s\n' \
		'make dev           # install projio + indexio editable with dev extras' \
		'make urls          # print repository and GitHub Pages URLs' \
		'make test          # run test suite' \
		'make docs          # build MkDocs site strictly' \
		'make docs-serve    # serve MkDocs locally' \
		'make build         # build wheel and sdist' \
		'make check         # run twine check on dist artifacts' \
		'make clean         # remove local build artifacts' \
		'make publish       # publish to PyPI via personal helper' \
		'make publish-test  # publish to TestPyPI via personal helper' \
		'' \
		'make save          # datalad save -r -m MSG (MSG var)' \
		'make status        # datalad status -r' \
		'make pull-origin   # datalad update -r --merge -s origin' \
		'make push-origin   # datalad push -r --to origin' \
		'make pull-gitlab   # datalad update -r --merge -s gitlab' \
		'make push-gitlab   # datalad push -r --to gitlab'

urls:
	@printf '%s\n' \
		'GitHub: https://github.com/arashshahidi1997/projio' \
		'Pages:  https://arashshahidi1997.github.io/projio/' \
		'PyPI:   https://pypi.org/project/projio/'

dev:
	$(PYTHON) -m pip install -e "packages/indexio[dev]"
	$(PYTHON) -m pip install -e ".[dev,indexio,biblio,notio]"

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests -q

docs:
	$(PYTHON) -m mkdocs build --strict

docs-serve:
	$(PYTHON) -m mkdocs serve

build:
	$(PYTHON) -m build

check:
	$(PYTHON) -m twine check dist/*

clean:
	rm -rf build dist site .pytest_cache .mypy_cache src/*.egg-info src/projio.egg-info

publish:
	$(PUBLISH) .

publish-test:
	$(PUBLISH) --test .

# ── DataLad subdataset management ──────────────────────────────────────
save:
	$(DATALAD) save -r -m "$(MSG)"

status:
	$(DATALAD) status -r

pull-origin:
	$(DATALAD) update -r --merge -s origin

push-origin:
	$(DATALAD) push -r --to origin

pull-gitlab:
	$(DATALAD) update -r --merge -s gitlab

push-gitlab:
	$(DATALAD) push -r --to gitlab

-include .projio/projio.mk
