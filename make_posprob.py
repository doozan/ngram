#!/usr/bin/python3

import argparse
import contextlib
import multiprocessing
import re
import smart_open
import sys
from collections import defaultdict

@contextlib.contextmanager
def open(filename, *args, **nargs):
    """ like smart_open, but treat empty filenames or - as stdin/out """
    if not filename or filename == "-":
        mode = args[0] if args else nargs.get("mode")
        if mode and "w" in mode:
            yield sys.stdout
        else:
            yield sys.stdin
    else:
        yield smart_open.open(filename, *args, **nargs)



def process_yeardata(yeardata, min_year):
    total = 0
    year_found = False
    for year_item in yeardata.split('\t'):
        year = int(year_item[:4])

        if not year_found:
            if year <= min_year:
                continue
            year_found = True

        _, use_count, source_count = year_item.split(",")
        use_count = int(use_count)

        total += use_count

    return total

def iter_lines():
    count = 0
    with open("-") as infile:
        for line in infile:
            if not count % 10000:
                print(count, end = '\r', file=sys.stderr)
            count += 1

            yield line

args = None
def process(line):

    # ignore unhandled words
    if not re.match("^[_A-ZÁÉÍÑÓÚÜa-záéíñóúü.]+\t", line):
        return

    ngram_pos, yeardata = line.split("\t", 1)

    if "_" not in ngram_pos:
        return

    ngram, pos = ngram_pos.rsplit("_", 1)
    if pos not in ["NOUN", "PROPN", "VERB", "ADJ", "ADV", "PRON", "DET", "ADP", "CONJ", "PRT"]:
        return

    ngram = ngram.rstrip("_")
    if not ngram:
        return

    total = process_yeardata(yeardata, args.year)
    if not total:
        return

    return ngram, (pos, total)


def main():
    global args
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("--year", help="min year", type=int, required=True)
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_lines(), 10000)
    else:
        iter_items = map(process, iter_lines())

    data = defaultdict(list)
    for res in iter_items:
        if not res:
            continue
        key, value = res
        data[key].append(value)


    for form, pos_counts in data.items():
        totals = defaultdict(int)
        total = 0
        for pos, count in pos_counts:
            totals[pos] += count
            total += count

        parts = [f"{pos}:{count}" for pos, count in sorted(totals.items(), key=lambda x: (x[1]*-1, x[0]))]
        print(f"{form}\t{total}\t{'; '.join(parts)}")


if __name__ == "__main__":
    main()
