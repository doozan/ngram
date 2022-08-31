#!/usr/bin/python3

import argparse
from collections import defaultdict
from enwiktionary_wordlist.all_forms import AllForms
import smart_open
import multiprocessing as mp
import sys
import pathlib

def get_preferred_case(ngram1, form):
    if len(form) == 1 and form.isalpha():
        return form.lower()
    return ngram1.get(form,(None,))[0]

def get_usage_count(ngram1, form):
    return ngram1.get(form.lower(),(None,0))[1]

def get_form(ngram1, ngram):
    word, _, pos = ngram.partition("_")
    if pos:
        return
    return get_preferred_case(ngram1, word.lower())

def load_ngram1(filename):

    """ returns a dict { 'lowercase_form': ['PreferredCase', count] } """
    print("loading", filename, file=sys.stderr)

    data = {}
    with open(filename, "rt") as infile:
        for line in infile:
            ngram, count, *args = line.split("\t")
            if "_" in ngram:
                raise ValueError("ngram contains _, is it word_pos format?:", line)
            word = ngram
#            word, _, pos = ngram.rpartition("_")
#            if not word or not word.isalpha():
#                continue

            lc = word.lower()
            if lc not in data:
                data[lc] = [word, int(count)]
            else:
#                print(word, data[lc], count)
                data[lc][1] += int(count)

    print("loaded", filename, len(data.keys()), file=sys.stderr)
    return data


def process_file(ngram1, filename):

    print("processing", filename, file=sys.stderr)
    all_coords = defaultdict(int)
    with smart_open.open(filename, "rt") as infile:
        for line in infile:
            ngram, count, *_ = line.split("\t")
            ngram_count = int(count)

            coords = []
            ngrams = ngram.split(" ")
            clean_ngrams = []
            for ngram_form in ngrams:
                form = get_form(ngram1, ngram_form)
                if not form:
                    coords = []
                    break
                clean_ngrams.append(form)

                form_count = get_usage_count(ngram1, form)
                if ngram_count*20 >= form_count:
                    coords.append(form)

            if not coords:
                continue

            clean_ngram = " ".join(clean_ngrams)
            for form in coords:
                item = (form, clean_ngram)
                if all_coords[item] < ngram_count:
                    all_coords[item] = ngram_count

    #outfilename = pathlib.Path(filename).with_suffix('.coord')
    #with open(outfilename, "wt") as outfile:
    for k, ngram_count in all_coords.items():
        form, ngram = k
        form_count = get_usage_count(ngram1, form)

        print(f"{form}\t{ngram}\t{form_count}\t{ngram_count}")
    print("processed", len(all_coords.keys()), file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("--ngram1", help="File contaning single word ngram counts")
    parser.add_argument("ngrams", help="File containing ngramN to search for collocations")
    args = parser.parse_args()

    ngram1 = load_ngram1(args.ngram1)

    process_file(ngram1, args.ngrams)

if __name__ == "__main__":
    main()
