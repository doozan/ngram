#!/usr/bin/python3

import argparse
import gzip
import requests
import multiprocessing as mp
import io
import os
import sys
from collections import defaultdict
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms

parser = argparse.ArgumentParser(description="Summarize ngram usage")
parser.add_argument("file", nargs='+')
parser.add_argument("--strip-pos", help="remove _POS tags")
parser.add_argument("--allow-unknown", help="Include words that don't exist in allforms", action='store_true')
parser.add_argument("--allforms", help="Use the given allforms for resolving word case and restricting POS")
parser.add_argument("--pos", help="Only list forms that match the given POS (may be specified multiple times)", action='append')
parser.add_argument("--min-len", help="Only list forms that with at least N characters", type=int)
#parser.add_argument("--ignore-pos", help="remove _POS tags")
args = parser.parse_args()

allforms = AllForms.from_file(args.allforms) if args.allforms else None

def get_form(ngram, allow_pos=None, disallow_pos=None):
    """ Note: allow_pos matches POS forms from allforms (n, v, adj, etc) but
    disallow_pos matches POS forms from NGRAMs (VERB, NOUN, ., etc) """
    word, _, pos = ngram.rpartition("_")
    if not word:
        word = pos
        pos = ""

    if not word.isalpha() or (args.min_len and len(word) < args.min_len):
        return

    if pos:
        if disallow_pos and pos in disallow_pos:
            return
        if pos not in ["NOUN", "VERB", "ADJ", "ADV", "PRON", "DET", "ADP", "CONJ", "PRT"]:
            return

    known = True
    if allforms:
        known = allforms.get_lemmas(word, allow_pos)
        if not known:
            lc = word.lower()
            known = allforms.get_lemmas(lc)
            if known:
                word = lc

    return word, pos, known

def read_summary(filename):
    print(f"reading {filename}", file=sys.stderr)

    if filename == "-":
        infile = sys.stdin
    else:
        infile = open(filename, "rt")

    for line in infile:
        ngram, _, count = line.partition("\t")
        res = get_form(ngram, allow_pos=args.pos, disallow_pos=["."])
        if not res:
            continue
        form, pos, known = res
        if not known and not args.allow_unknown:
            continue
        if form:
            yield form, pos, int(count), known

    if filename != "-":
        infile.close()

def print_formdata(form, formdata, is_known):
    poscount = []
    total = 0
    for pos, count in sorted(formdata.items(), key=lambda x: x[1], reverse=True):
        total += count
        if pos:
            poscount.append(f"{pos}:{count}")

    poscounts = "\t" + '; '.join(poscount) if poscount else ""
    unknown = "\tUNKNOWN" if not is_known else ""
    if unknown and poscounts == "":
        poscounts = "\t"

    print(f"{form}\t{total}{poscounts}{unknown}")

data = []
for filename in args.file:
    data += list(read_summary(filename))

prev_form = None
prev_known = False
formdata = defaultdict(int)
for form, pos, count, known in sorted(data):
    if form != prev_form:
        if prev_form:
            print_formdata(prev_form, formdata, prev_known)
        formdata = defaultdict(int)
        prev_form = form
        prev_known = known
    formdata[pos] += count

if prev_form:
    print_formdata(prev_form, formdata, prev_known)
