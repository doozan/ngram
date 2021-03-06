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

year := 1950

spa-1-all := $(foreach var,$(shell seq -f "%05g" 0    2),spa/1-$(var)-of-00003-$(year).bz2)
spa-2-all := $(foreach var,$(shell seq -f "%05g" 0   72),spa/2-$(var)-of-00073-$(year).bz2)
spa-3-all := $(foreach var,$(shell seq -f "%05g" 0  687),spa/3-$(var)-of-00688-$(year).bz2)
spa-4-all := $(foreach var,$(shell seq -f "%05g" 0  570),spa/4-$(var)-of-00571-$(year).bz2)
spa-5-all := $(foreach var,$(shell seq -f "%05g" 0 1414),spa/5-$(var)-of-01415-$(year).bz2)

%-$(year).bz2:
>   @echo "Making $@..."

>   URL=http://storage.googleapis.com/books/ngrams/books/20200217/$*.gz
>   $(SUMMARIZE) $$URL --min-year $(year) -o $@

.SECONDEXPANSION:

spa-%: $$(spa-$$*-all)

spa/%-$(year).ngram: $$(spa-$$*-all)
>   @echo "Making $@..."

>   mkdir -p $(@D)
>   bzcat $^ | sort -k2,2nr -k1,1 > $@

# Build all .coord files at the same time
$(subst .bz2,.coord,$(spa-2-all)) &: spa/1-1950.ngram $(spa-2-all)
>   @echo "Making $@..."
>   $(MAKE_COORDS) --ngram1 $^

$(subst .bz2,.coord,$(spa-3-all)) &: spa/1-1950.ngram $(spa-3-all)
>   @echo "Making $@... $^"
>   $(MAKE_COORDS) --ngram1 $^

$(subst .bz2,.coord,$(spa-4-all)) &: spa/1-1950.ngram $(spa-4-all)
>   @echo "Making $@... $^"
>   $(MAKE_COORDS) --ngram1 $^

spa/%-$(year).coord: $$(subst .bz2,.coord,$$(spa-$$(*)-all))
>   @echo "Making $@..."

>   cat $^ | sort -u > $@

.PHONY: spa-1 spa-2 spa-3 spa-4 spa-5
