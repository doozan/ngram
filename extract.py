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

def summarize(lines):
    for line in lines:
        total = 0
        min_found = not args.min_year
        items = line.split('\t')
        for year_item in items[1:]:

            if not min_found:
                if int(year_item[:4]) <= args.min_year:
                    continue
                min_found = True

            if args.max_year and int(year_item[:4]) > args.max_year:
                break

            year, sources, count = year_item.split(",")
            total += int(count)

        if total and total > args.min_count:
            yield(items[0], total)

def download(url, dest):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            print("downlading", url, file=sys.stderr)
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def get_target(lang, ngram, part, parts, min_year=None):
    if min_year:
        return f"{lang}/{ngram}-{part:05}-of-{parts:05}-{min_year}.txt"
    else:
        return f"{lang}/{ngram}-{part:05}-of-{parts:05}.txt"

def make_extract(lang, ngram, part, parts, min_year=None):
    path = f"{lang}/{ngram}-{part:05}-of-{parts:05}.gz"
    url = f"http://storage.googleapis.com/books/ngrams/books/20200217/{path}"
    target = get_target(lang, ngram, part, parts, min_year)

    # Don't create extract if it already exists
    if os.path.exists(target):
        return target

    # Use the cache as necessary
    if args.cachedir:
        cache = os.path.join(args.cachedir, path)
        if not os.path.exists(cache):
            download(url, cache)
        print(f"extracting {cache} to {target}", file=sys.stderr)
        gz = gzip.open(cache, "rt")

    # If no cache, stream directly from the source URL
    else:
        print(f"streaming {url} to {target}", file=sys.stderr)
        r = requests.get(url, stream=True)
        gz = io.TextIOWrapper(gzip.GzipFile(fileobj=r.raw))
        gz.seek(0)

    with open(target, "wt") as outfile:
        for value, count in summarize(gz):
            outfile.write(f"{value}\t{count}\n")

    gz.close()

    return target

def normalize_lemma(item, allow_pos=None, disallow_pos=None):
    ngrams = []
    for ngram in item.split(" "):
        word, _, pos = ngram.partition("_")
        if not word:
            return
        if pos and not (allow_pos and pos not in allow_pos) and not (disallow_pos and pos not in disallow_pos):
            return

        word = word.lower()
#        if pos:
#            ngrams.append(f"{word}_{pos}")
#        else:
#            ngrams.append(word)
        ngrams.append(word)
    return " ".join(ngrams)

def find_coords(part):
    target = make_extract(args.lang, args.ngram, part, args.parts, args.min_year)
    print(f"checking {target}, {len(all_lemmas)}", file=sys.stderr)

    all_coords = defaultdict(int)

    for ngram, count in read_extract(target):
        coords = []
        lemmas = ngram.split(" ")
        for lemma in lemmas:
            if not wordlist.has_entry(lemma) or \
                    lemma in ["el", "la", "las", "los", "un", "una", "y"]:
                coords = []
                break

            lemma_count = all_lemmas.get(lemma)
            if not lemma_count:
                coords = []
                break

            #print([lemma, lemma_count, count])
            if count*4 > lemma_count:
                coords.append((lemma, ngram, count))

        for lemma, ngram, count in coords:
            item = (lemma, ngram)
            if all_coords[item] < count:
                all_coords[item] = count

    for k, count in all_coords.items():
        lemma, ngram = k
        lemma_count = all_lemmas.get(lemma)
        print(f"{lemma}\t{ngram}\t{count}/{lemma_count}\t{int(count/lemma_count*100)}%")

all_lemmas = defaultdict(int)

def load_ngram1(part):
    make_extract("spa", 1, part, 3)

def load_lemmas():
    ngram = 1
    parts = 3

    for part in range(0, parts):
        target = make_extract("spa", 1, part, 3)
        for lemma, count in read_extract(target):
            all_lemmas[lemma] += int(count)

def read_extract(filename):
    print(f"reading {filename}", file=sys.stderr)
    with open(filename, "rt") as infile:
        for line in infile:
            ngram, _, count = line.partition("\t")
            lemma = normalize_lemma(ngram, disallow_pos=["."])
            if lemma:
                yield lemma, int(count)


parser = argparse.ArgumentParser(description="Summarize ngram usage")
parser.add_argument("--cachedir", help="read/write source files from/to cache directory")
parser.add_argument("--ngram", type=int, required=True)
parser.add_argument("--lang", required=True)
parser.add_argument("--parts", type=int, required=True)
parser.add_argument("--min-count", type=int)
parser.add_argument("--min-year", type=int)
parser.add_argument("--max-year", type=int)
parser.add_argument("--wordlist", required=True)
args = parser.parse_args()

wordlist = Wordlist.from_file(args.wordlist)

max_cpu = max(1, mp.cpu_count()-1)
pool = mp.Pool(max_cpu)
pool.map(load_ngram1, range(0,3))
pool.close()

load_lemmas()

pool = mp.Pool(max_cpu)
#find_coords(10)
pool.map(find_coords, range(0, args.parts))

pool.close()


