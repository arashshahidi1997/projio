# projio.mk — shared targets, managed by projio
# Include from your Makefile: -include .projio/projio.mk

PYTHON  ?= python
DATALAD ?= /storage/share/python/environments/Anaconda3/envs/labpy/bin/datalad
MKDOCS  ?= /storage/share/python/environments/Anaconda3/envs/labpy/bin/python -m mkdocs
PROJIO  ?= /storage/share/python/environments/Anaconda3/envs/rag/bin/python -m projio
NOTIO   ?= /storage/share/python/environments/Anaconda3/envs/rag/bin/python -m notio
PANDOC  ?= /storage/share/python/environments/Anaconda3/envs/labpy/bin/pandoc
PUBLISH ?= /storage2/arash/infra/bin/publish_pypi.sh
MSG     ?= Update

PANDOC_FILTER ?= .projio/filters/include.lua

.PHONY: save push url
.PHONY: projio-init projio-config-user projio-config-show projio-status projio-auth
.PHONY: projio-gh projio-gl projio-ria site-build site-serve site-stop site-list site-detect mcp mcp-config

# --- DataLad targets ---
save:
	$(DATALAD) save -m "$(MSG)"

push:
	$(DATALAD) push --to github

url:
	$(PROJIO) url -C .

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

site-stop:
	$(PROJIO) site stop -C . --all

site-list:
	$(PROJIO) site list -C .

site-detect:
	$(PROJIO) site detect -C .

mcp:
	$(PROJIO) mcp -C .

mcp-config:
	$(PROJIO) mcp-config -C . --yes

# --- Render variables (from .projio/render.yml) ---
PANDOC_BIB       ?= bib/main.bib
PANDOC_CSL       ?= 
PDF_ENGINE_ARGS  ?= --pdf-engine=xelatex
PANDOC_CITE_ARGS  = $(if $(PANDOC_BIB),--citeproc --bibliography=$(PANDOC_BIB)) $(if $(PANDOC_CSL),--csl=$(PANDOC_CSL))
PANDOC_COMMON_ARGS = --lua-filter=$(PANDOC_FILTER) $(PANDOC_CITE_ARGS)


# --- Manuscript targets (manuscripto) ---
.PHONY: manuscript-demo-assemble manuscript-demo-pdf manuscript-demo-latex manuscript-demo-validate

manuscript-demo-assemble: docs/manuscript/demo/manuscript.yml
	@echo ">> Assembling manuscript: demo"
	@$(NOTIO) --root . manuscript assemble demo

manuscript-demo-pdf: docs/manuscript/demo/manuscript.yml $(PANDOC_FILTER)
	@echo ">> Building manuscript PDF: demo"
	@$(NOTIO) --root . manuscript assemble demo
	@mkdir -p _build/pdf
	@$(PANDOC) docs/manuscript/demo/_build/assembled.md $(PANDOC_COMMON_ARGS) $(PDF_ENGINE_ARGS) -o _build/pdf/demo.pdf

manuscript-demo-latex: docs/manuscript/demo/manuscript.yml $(PANDOC_FILTER)
	@echo ">> Building manuscript LaTeX: demo"
	@$(NOTIO) --root . manuscript assemble demo
	@mkdir -p _build/latex
	@$(PANDOC) docs/manuscript/demo/_build/assembled.md $(PANDOC_COMMON_ARGS) -t latex -o _build/latex/demo.tex

manuscript-demo-validate: docs/manuscript/demo/manuscript.yml
	@$(NOTIO) --root . manuscript validate demo

# --- Master document targets (Lua transclusion) ---
.PHONY: plan-pdf plan-latex plan-md

plan-pdf: docs/plan/master.md $(PANDOC_FILTER)
	@echo ">> Building plan PDF"
	@mkdir -p _build/pdf
	@$(PANDOC) docs/plan/master.md $(PANDOC_COMMON_ARGS) $(PDF_ENGINE_ARGS) -o _build/pdf/plan-master.pdf

plan-latex: docs/plan/master.md $(PANDOC_FILTER)
	@echo ">> Building plan LaTeX"
	@mkdir -p _build/latex
	@$(PANDOC) docs/plan/master.md $(PANDOC_COMMON_ARGS) -t latex -o _build/latex/plan-master.tex

plan-md: docs/plan/master.md $(PANDOC_FILTER)
	@echo ">> Building plan resolved Markdown"
	@mkdir -p _build/md
	@$(PANDOC) docs/plan/master.md --lua-filter=$(PANDOC_FILTER) -t gfm --wrap=none -o _build/md/plan-master.md
