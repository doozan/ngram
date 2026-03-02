SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --keep-going

# don't delete any intermediary files
.SECONDARY:

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

SUMMARIZE := ./summarize.py
MAKE_NGRAM1 := ./make_ngram1.py
MAKE_NGPHRASES := ./make_ngphrases.py
MAKE_POSPROB := ./make_posprob.py

spa-1-all := $(foreach var,$(shell seq -f "%05g" 0    2),spa/1-$(var)-of-00003.bz2)
spa-2-all := $(foreach var,$(shell seq -f "%05g" 2   21),spa/2-$(var)-of-00073.bz2) $(foreach var,$(shell seq -f "%05g" 26   72),spa/2-$(var)-of-00073.bz2)
spa-3-all := $(foreach var,$(shell seq -f "%05g" 45 129),spa/3-$(var)-of-00688.bz2) $(foreach var,$(shell seq -f "%05g" 239  687),spa/3-$(var)-of-00688.bz2)
spa-4-all := $(foreach var,$(shell seq -f "%05g" 33  79),spa/4-$(var)-of-00571.bz2) $(foreach var,$(shell seq -f "%05g" 262  570),spa/4-$(var)-of-00571.bz2)
spa-5-all := $(foreach var,$(shell seq -f "%05g" 77 161),spa/5-$(var)-of-01415.bz2) $(foreach var,$(shell seq -f "%05g" 771 1414),spa/5-$(var)-of-01415.bz2)

%-full.bz2:
>   @echo "Making $@..."
>   URL=http://storage.googleapis.com/books/ngrams/books/20200217/$*.gz
>   curl --retry 5 -s $$URL | gunzip | bzip2  > $@

%-summary.bz2:
>   URL=http://storage.googleapis.com/books/ngrams/books/20200217/$*.gz
>   curl --retry 5 -s $$URL \
>      | gunzip \
>      | grep -P "^[ A-ZÁÉÍÑÓÚÜa-záéíñóúü.]+\t" \
>      | grep -v -E "(^|\s)\." \
>      | $(SUMMARIZE) \
>      | LC_ALL=C sort -t $$'\t' -k1,1 -k2,2nr \
>      | bzip2 \
>      > $@

.SECONDEXPANSION:

%-all: $$(subst .bz2,-summary.bz2,$$(spa-$$(*)-all))
>   @echo "Making $@..."
>   touch $@

es-%.posprob-full: $$(subst .bz2,-full.bz2,$$(spa-1-all))
>   @echo "Making $@..."
>   bzcat $^ \
>       | $(MAKE_POSPROB) --year $* \
>       | LC_ALL=C sort -k2,2nr -k1,1 \
>       > $@

es-%.ngram1: $$(subst .bz2,-full.bz2,$$(spa-1-all))
>   @echo "Making $@..."
>   bzcat $^ \
>       | $(MAKE_NGRAM1) --year $* \
>       | LC_ALL=C sort -k2,2nr -k1,1 \
>       > $@

es-combined.ngram%.bz2: $$(subst .bz2,-summary.bz2,$$(spa-$$(*)-all))
>   @echo "Making $@..."
>   $(MAKE_NGPHRASES) $^ \
>       | LC_ALL=C sort -t $$'\t' -k 1 \
>       | $(MAKE_NGPHRASES) --merge-dups \
>       | bzip2 \
>       > $@

es-combined.db: $(patsubst %, es-combined.ngram%.bz2,2 3 4 5)
>   @echo "Making $@..."
>   cat <<EOF > prep.sql
>   PRAGMA journal_mode = OFF;
>   PRAGMA synchronous = 0;
>   PRAGMA cache_size = 10000;
>   PRAGMA locking_mode = EXCLUSIVE;
>   PRAGMA temp_store = FILE;
>   PRAGMA mmap_size = 30000000000;
>   PRAGMA page_size = 4096;
>   CREATE TABLE IF NOT EXISTS ngram(phrase text PRIMARY KEY NOT NULL, post_1950 INT NOT NULL, post_2010 INT NOT NULL);
>   .mode csv
>   .separator "\t"
>   .timer on
>   .import /dev/stdin ngram
>   EOF
>
>   for file in $^; do \
>       echo "loading $$file..."; \
>       bzcat $$file | sqlite3 --init prep.sql $@; \
>   done

all: es-combined.db es-1950.posprob-full es-1950.ngram1 es-2010.ngram1
