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
MAKE_COORDS := ./make_coords.py
MAKE_NGCASE := ./make_ngcase.py

spa-1-all := $(foreach var,$(shell seq -f "%05g" 0    2),spa/1-$(var)-of-00003.bz2)
spa-2-all := $(foreach var,$(shell seq -f "%05g" 2   21),spa/2-$(var)-of-00073.bz2) $(foreach var,$(shell seq -f "%05g" 26   72),spa/2-$(var)-of-00073.bz2)
spa-3-all := $(foreach var,$(shell seq -f "%05g" 45 129),spa/3-$(var)-of-00688.bz2) $(foreach var,$(shell seq -f "%05g" 239  687),spa/3-$(var)-of-00688.bz2)
spa-4-all := $(foreach var,$(shell seq -f "%05g" 33  79),spa/4-$(var)-of-00571.bz2) $(foreach var,$(shell seq -f "%05g" 262  570),spa/4-$(var)-of-00571.bz2)
spa-5-all := $(foreach var,$(shell seq -f "%05g" 77 161),spa/5-$(var)-of-01415.bz2) $(foreach var,$(shell seq -f "%05g" 771 1414),spa/5-$(var)-of-01415.bz2)

%-filtered.bz2:
>   @echo "Making $@..."
>   URL=http://storage.googleapis.com/books/ngrams/books/20200217/$*.gz
>   curl --retry 5 -s $$URL | gunzip | ( grep -P "^[ A-ZÁÉÍÑÓÚÜa-záéíñóúü.]+\t" || [[ $$? == 1 ]] ) | bzip2  > $@

%-full.bz2:
>   @echo "Making $@..."
>   URL=http://storage.googleapis.com/books/ngrams/books/20200217/$*.gz
>   curl --retry 5 -s $$URL | gunzip | bzip2  > $@

YEAR := 1950
#YEAR := 2012
spa/%-filtered-$(YEAR).bz2: spa/%-filtered.bz2
>   @echo "Making $@..."
>   $(SUMMARIZE) $< --min-YEAR $(YEAR) -o $@
#>   $(SUMMARIZE) $< --min-YEAR $(YEAR) -o $@ --normalize

spa/%-full-$(YEAR).bz2: spa/%-full.bz2
>   @echo "Making $@..."
#>   $(SUMMARIZE) $< --min-YEAR $(YEAR) -o $@ --normalize
>   $(SUMMARIZE) $< --min-YEAR $(YEAR) -o $@

.SECONDEXPANSION:

spa/1-full-$(YEAR).ngram: $$(subst .bz2,-full-$(YEAR).bz2,$$(spa-1-all))
>   @echo "Making $@..."
>   bzcat $^ | sort -k2,2nr -k1,1 > $@

spa/%-filtered-$(YEAR).ngram: $$(subst .bz2,-filtered-$(YEAR).bz2,$$(spa-$$(*)-all))
>   @echo "Making $@..."
>   mkdir -p $(@D)
>   bzcat $^ | grep -P "^[ A-ZÁÉÍÑÓÚÜa-záéíñóúü.]+\t" | grep -v -E "(^|\s)\.+\s" > $@
>   sort -k2,2nr -k1,1 -o $@ $@

spa/%.ngram.bz2: spa/%.ngram
>   @echo "Making $@..."
>   bzip2 -f $<

spa/%-filtered-$(YEAR).coord: spa/1-filtered-$(YEAR).ngram spa/%-filtered-$(YEAR).ngram.bz2
>   @echo "Making $@..."
>   $(MAKE_COORDS) --ngram1 $^ > $@

spa/ngram-$(YEAR).db: $(patsubst %,spa/%-filtered-$(YEAR).ngram.bz2,2 3 4 5)
>   @echo "Making $@..."
>   cat <<EOF > load.sql
>   PRAGMA journal_mode = OFF;
>   PRAGMA synchronous = 0;
>   PRAGMA cache_size = 1000000;
>   PRAGMA locking_mode = EXCLUSIVE;
>   PRAGMA temp_store = MEMORY;
>   CREATE TABLE ngram(phrase text PRIMARY KEY NOT NULL, count INT NOT NULL);
>   .mode csv
>   .separator "\t"
>   .timer on
>   .import /dev/stdin ngram
>   EOF
>
>   $(RM) $@
>   bzcat $^ | sqlite3 --init load.sql $@

spa/es-1-$(YEAR).ngcase: spa/2-filtered-$(YEAR).ngram.bz2
>   @echo "Making $@..."

>   $(MAKE_NGCASE) $^ --min 1000 > $@

all_ngrams: spa/1-full-$(YEAR).ngram spa/1-filtered-$(YEAR).ngram $(patsubst %, spa/%-filtered-$(YEAR).ngram.bz2,2 3 4 5)
all_coords: $(patsubst %, spa/%-filtered-$(YEAR).coord,2 3 4 5)
all: all_ngrams all_coords

.PHONY: all all_ngrams all_coords
