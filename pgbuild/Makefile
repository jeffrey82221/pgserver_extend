SHELL := /bin/bash
INSTALL_PREFIX := $(shell pwd)/../src/pgserver/pginstall/
BUILD := $(shell pwd)/pgbuild/

POSTGRES_VERSION := 18.6
PG_MAJOR := $(firstword $(subst ., ,$(POSTGRES_VERSION)))
IS_MUSL ?= $(shell if command -v ldd >/dev/null 2>&1 && ldd --version 2>&1 | grep -qi musl; then echo 1; else echo 0; fi)

# Windows: only postgres + pgvector.
#  - AGE's documented native build platforms are Linux and macOS.
#  - pgsql-http needs libcurl; pgvectorscale needs cargo-pgrx (not supported on Windows/musl).
# Elsewhere: pgvector, AGE and pgsql-http; plus the cargo-pgrx based pgvectorscale (not on musl)
# and pg_textsearch (PostgreSQL >= 17 only, skipped on older versions).
ifeq ($(OS),Windows_NT)
EXTENSIONS ?= pgvector
else
EXTENSIONS ?= pgvector age
ifneq ($(shell uname -s)-$(shell uname -m),Darwin-x86_64)
EXTENSIONS += pgsql_http
endif
ifneq ($(IS_MUSL),1)
EXTENSIONS += pgvectorscale
endif
ifeq ($(shell test $(PG_MAJOR) -ge 17 && echo yes),yes)
EXTENSIONS += pgtextsearch
else
$(info Skipping pgtextsearch: it requires PostgreSQL >= 17 (building $(PG_MAJOR)))
endif
endif

.PHONY: all
all: postgres $(EXTENSIONS)

### postgres
POSTGRES_URL := https://ftp.postgresql.org/pub/source/v$(POSTGRES_VERSION)/postgresql-$(POSTGRES_VERSION).tar.gz
POSTGRES_SRC := postgresql-$(POSTGRES_VERSION)
POSTGRES_BLD := $(POSTGRES_SRC)

$(POSTGRES_SRC).tar.gz:
	curl -L -O $(POSTGRES_URL)

## extract
$(POSTGRES_SRC)/configure: $(POSTGRES_SRC).tar.gz
	tar xzf $(POSTGRES_SRC).tar.gz
	touch $(POSTGRES_SRC)/configure

## configure
$(POSTGRES_BLD)/config.status: $(POSTGRES_SRC)/configure
	mkdir -p $(POSTGRES_BLD)
	cd $(POSTGRES_BLD) && ../$(POSTGRES_SRC)/configure --prefix=$(INSTALL_PREFIX) --without-readline --without-icu

## build
# https://stackoverflow.com/questions/68379786/
# for explanation of unsetting make env variables prior to calling postgres' own make
$(POSTGRES_BLD)/src/bin/initdb/initdb: $(POSTGRES_BLD)/config.status
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) -j

## install to INSTALL_PREFIX
$(INSTALL_PREFIX)/bin/postgres: $(POSTGRES_BLD)/config.status
	mkdir -p $(INSTALL_PREFIX)
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) install

.PHONY: postgres
postgres: $(INSTALL_PREFIX)/bin/postgres

### pgvector
PGVECTOR_TAG := v0.8.1
PGVECTOR_URL := https://github.com/pgvector/pgvector/archive/refs/tags/$(PGVECTOR_TAG).tar.gz
PGVECTOR_DIR := pgvector-$(PGVECTOR_TAG)

$(PGVECTOR_DIR).tar.gz:
	curl -L -o $(PGVECTOR_DIR).tar.gz $(PGVECTOR_URL)

$(PGVECTOR_DIR)/Makefile: $(PGVECTOR_DIR).tar.gz
	# tar extract into pgvector-$(PGVECTOR_TAG)
	mkdir -p $(PGVECTOR_DIR)
	tar xzf $(PGVECTOR_DIR).tar.gz -C $(PGVECTOR_DIR) --strip-components=1
	touch $(PGVECTOR_DIR)/Makefile

$(INSTALL_PREFIX)/lib/vector.so: $(PGVECTOR_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& export PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config \
		&& $(MAKE) -C $(PGVECTOR_DIR) -j \
		&& $(MAKE) -C $(PGVECTOR_DIR) install

.PHONY: pgvector
pgvector: postgres $(INSTALL_PREFIX)/lib/vector.so

### age
AGE_TAG := v1.7.0
AGE_URL := https://github.com/apache/age/archive/refs/tags/PG$(PG_MAJOR)/$(AGE_TAG)-rc0.tar.gz
AGE_DIR := age-$(AGE_TAG)
$(AGE_DIR).tar.gz:
	curl -L -o $(AGE_DIR).tar.gz $(AGE_URL)

$(AGE_DIR)/Makefile: $(AGE_DIR).tar.gz
	# tar extract into age-$(AGE_TAG)
	mkdir -p $(AGE_DIR)
	tar xzf $(AGE_DIR).tar.gz -C $(AGE_DIR) --strip-components=1
	touch $(AGE_DIR)/Makefile

$(INSTALL_PREFIX)/lib/age.so: $(AGE_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& export PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config \
		&& $(MAKE) -C $(AGE_DIR) -j \
		&& $(MAKE) -C $(AGE_DIR) install

.PHONY: age
age: postgres $(INSTALL_PREFIX)/lib/age.so

### pgsql-http (needs libcurl headers: libcurl-devel / libcurl4-openssl-dev; shipped with macOS)
PGSQL_HTTP_TAG := v1.7.0
PGSQL_HTTP_URL := https://github.com/pramsey/pgsql-http/archive/refs/tags/$(PGSQL_HTTP_TAG).tar.gz
PGSQL_HTTP_DIR := pgsql-http-$(PGSQL_HTTP_TAG)

$(PGSQL_HTTP_DIR).tar.gz:
	curl -L -o $(PGSQL_HTTP_DIR).tar.gz $(PGSQL_HTTP_URL)

$(PGSQL_HTTP_DIR)/Makefile: $(PGSQL_HTTP_DIR).tar.gz
	mkdir -p $(PGSQL_HTTP_DIR)
	tar xzf $(PGSQL_HTTP_DIR).tar.gz -C $(PGSQL_HTTP_DIR) --strip-components=1
	touch $(PGSQL_HTTP_DIR)/Makefile

$(INSTALL_PREFIX)/lib/http.so: $(PGSQL_HTTP_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& $(MAKE) -C $(PGSQL_HTTP_DIR) PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config -j \
		&& $(MAKE) -C $(PGSQL_HTTP_DIR) PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config install

.PHONY: pgsql_http
pgsql_http: postgres $(INSTALL_PREFIX)/lib/http.so

### pgvectorscale (rust, built with cargo-pgrx; needs rustc/cargo + clang)
PGVECTORSCALE_TAG := 0.9.0
PGVECTORSCALE_URL := https://github.com/timescale/pgvectorscale/archive/refs/tags/$(PGVECTORSCALE_TAG).tar.gz
PGVECTORSCALE_DIR := pgvectorscale-$(PGVECTORSCALE_TAG)
# must match the pgrx version pinned in pgvectorscale's Cargo.toml
PGRX_VERSION := 0.16.1

$(PGVECTORSCALE_DIR).tar.gz:
	curl -L -o $(PGVECTORSCALE_DIR).tar.gz $(PGVECTORSCALE_URL)

$(PGVECTORSCALE_DIR)/pgvectorscale/Cargo.toml: $(PGVECTORSCALE_DIR).tar.gz
	mkdir -p $(PGVECTORSCALE_DIR)
	tar xzf $(PGVECTORSCALE_DIR).tar.gz -C $(PGVECTORSCALE_DIR) --strip-components=1
	touch $(PGVECTORSCALE_DIR)/pgvectorscale/Cargo.toml

$(INSTALL_PREFIX)/lib/vectorscale.so: $(PGVECTORSCALE_DIR)/pgvectorscale/Cargo.toml $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& export PATH="$$HOME/.cargo/bin:$$PATH" \
		&& (cargo pgrx --version 2>/dev/null | grep -q "$(PGRX_VERSION)" || cargo install cargo-pgrx --version =$(PGRX_VERSION) --locked) \
		&& cd $(PGVECTORSCALE_DIR)/pgvectorscale \
		&& cargo pgrx init --pg$(PG_MAJOR) $(INSTALL_PREFIX)/bin/pg_config \
		&& cargo pgrx install --release --pg-config $(INSTALL_PREFIX)/bin/pg_config

.PHONY: pgvectorscale
pgvectorscale: pgvector postgres $(INSTALL_PREFIX)/lib/vectorscale.so

### pgtextsearch (timescale/pg_textsearch, plain PGXS C extension; PostgreSQL >= 17 only)
PGTEXTSEARCH_TAG := v1.0.0
PGTEXTSEARCH_URL := https://github.com/timescale/pg_textsearch/archive/refs/tags/$(PGTEXTSEARCH_TAG).tar.gz
PGTEXTSEARCH_DIR := pgtextsearch-$(PGTEXTSEARCH_TAG)

$(PGTEXTSEARCH_DIR).tar.gz:
	curl -L -o $(PGTEXTSEARCH_DIR).tar.gz $(PGTEXTSEARCH_URL)

$(PGTEXTSEARCH_DIR)/Makefile: $(PGTEXTSEARCH_DIR).tar.gz
	mkdir -p $(PGTEXTSEARCH_DIR)
	tar xzf $(PGTEXTSEARCH_DIR).tar.gz -C $(PGTEXTSEARCH_DIR) --strip-components=1
	touch $(PGTEXTSEARCH_DIR)/Makefile

$(INSTALL_PREFIX)/lib/pg_textsearch.so: $(PGTEXTSEARCH_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& $(MAKE) -C $(PGTEXTSEARCH_DIR) PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config -j \
		&& $(MAKE) -C $(PGTEXTSEARCH_DIR) PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config install

.PHONY: pgtextsearch
pgtextsearch: postgres $(INSTALL_PREFIX)/lib/pg_textsearch.so

### other
.PHONY: clean clean-all
clean:
	rm -rf $(INSTALL_PREFIX)
	rm -rf $(POSTGRES_SRC)
	rm -rf $(POSTGRES_BLD)
	rm -rf $(PGVECTOR_DIR)
	rm -rf $(AGE_DIR)
	rm -rf $(PGSQL_HTTP_DIR)
	rm -rf $(PGVECTORSCALE_DIR)
	rm -rf $(PGTEXTSEARCH_DIR)

clean-all: clean
	rm -rf *.tar.gz