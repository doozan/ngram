#!/usr/bin/python3

from collections import defaultdict
import smart_open
import sys

_unaccent_tab = str.maketrans("áéíñóúüÁÉÍÑÓÚÜ", "aeinouuAEINOUU")
def strip_accent(text):
    return text.translate(_unaccent_tab)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("file", nargs='*')
    parser.add_argument("--merge-dups", action='store_true')
    #parser.add_argument("--decade", help="min decade", type=int, required=True)
    args = parser.parse_args()

    assert not (args.file and args.merge_dups)

    if args.file:
        process(args.file)

    if args.merge_dups:
        merge_dups()

import contextlib

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



def merge_dups():
    ''' assumes the input has been sorted and than dups will be together '''
    prev_ngram = None
    post_1950 = 0
    post_2010 = 0
    with open("-") as infile:
        for line in infile:
            ngram, v_post_1950, v_post_2010 = line.rstrip().split("\t")
            if ngram != prev_ngram:
                if prev_ngram is not None:
                    print(f"{prev_ngram}\t{post_1950}\t{post_2010}")
                prev_ngram = ngram
                post_1950 = 0
                post_2010 = 0

            post_1950 += int(v_post_1950)
            post_2010 += int(v_post_2010)

        print(f"{prev_ngram}\t{post_1950}\t{post_2010}")

def process(filenames):

    #assert args.decade in [1950, 1960, 1970, 1980, 1990, 2000, 2010]

    # The original ngram files are sorted with captitals before lowercase
    # and accents after lowercase, which makes buffering difficult
    # As a workarond, buffer and flush regularly to minimize memory use
    # and reduce number of duplicate lines, but accept that some lines
    # will be duplicated and will require a second pass to merge

    data = defaultdict(lambda: [0, 0])
    def flush_data():
        for ngram, counts in data.items():
            post_1950, post_2010 = counts
            print(f"{ngram}\t{post_1950}\t{post_2010}")
        data.clear()

    ngram = ""
    for filename in filenames:
        print(f"processing {filename} {ngram}", file=sys.stderr)
        with smart_open.open(filename) as infile:
            #header = next(infile)

            #assert header.startswith("form\t1950s")
            #assert header.strip().endswith("\t2010s")

            #headers = header.strip().split("\t")
            #offset_idx = None
            #for idx, key in enumerate(headers):
            #    if key == f"{args.decade}s":
            #        offset_idx = idx-1

            #assert offset_idx is not None

            for idx, line in enumerate(infile):

                # skip headers
                #if line == header:
                #    continue

                if not idx % 10000:
                    print(idx, end = '\r', file=sys.stderr)

                ngram, *decade_counts = line.split("\t")
                lower = ngram.lower()

                #total = sum(map(int, decade_counts[offset_idx:]))
                post_1950 = sum(map(int, decade_counts))
                post_2010 = int(decade_counts[-1])

                if not post_1950:
                    continue

                data[lower][0] += post_1950
                data[lower][1] += post_2010
            flush_data()


if __name__ == "__main__":
    main()
