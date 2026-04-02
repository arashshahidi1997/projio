# Flow: text_analysis
SHELL := /bin/bash

# Project root (relative to this Makefile)
PROJECT_ROOT ?= $(shell git -C $(dir $(abspath $(lastword $(MAKEFILE_LIST)))) rev-parse --show-toplevel)

.PHONY: help run dry-run nb-status nb-sync nb-lab nb-publish

help:
	@echo "Targets: run dry-run nb-status nb-sync nb-lab nb-publish"

run:
	snakemake --snakefile $(CURDIR)/Snakefile --directory $(PROJECT_ROOT) -j1

dry-run:
	snakemake --snakefile $(CURDIR)/Snakefile --directory $(PROJECT_ROOT) -j1 -n

nb-status:
	pipeio nb status

nb-sync:
	pipeio nb sync --direction py2nb

nb-lab:
	pipeio nb lab

nb-publish:
	pipeio nb sync --direction py2nb --force
	pipeio nb publish
