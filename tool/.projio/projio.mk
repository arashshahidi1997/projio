# projio.mk — shared targets, managed by projio
# Include from your Makefile: -include .projio/projio.mk

PYTHON  ?= python
DATALAD ?= datalad
PROJIO  ?= $(PYTHON) -m projio
MSG     ?= Update

.PHONY: save push
.PHONY: projio-init projio-config-user projio-config-show projio-status projio-auth
.PHONY: projio-gh projio-gl projio-ria site-build site-serve mcp

# --- DataLad targets ---
save:
	$(DATALAD) save -m "$(MSG)"

push:
	$(DATALAD) push --to github

# --- Projio targets ---
projio-init:
	$(PROJIO) init .

projio-config-user:
	$(PROJIO) config init-user

projio-config-show:
	$(PROJIO) config -C . show

projio-status:
	$(PROJIO) status -C .

projio-auth:
	$(PROJIO) auth -C . doctor

projio-gh:
	$(PROJIO) sibling -C . github

projio-gl:
	$(PROJIO) sibling -C . gitlab

projio-ria:
	$(PROJIO) sibling -C . ria

site-build:
	$(PROJIO) site build -C .

site-serve:
	$(PROJIO) site serve -C .

mcp:
	$(PROJIO) mcp -C .
