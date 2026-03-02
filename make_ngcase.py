#!/usr/bin/python3

import argparse
import smart_open
import sys
from collections import defaultdict

def print_matches(matches, lower, total):
    for form, count in matches:
        if form == lower:
            continue
        if count*10 > total:
            #print(f"{alt_case}\t{count}\t{word}\t{total}\t{int(count/total*100)}%")
            print(f"{form}\t{int(count/total*100)}")

def main():
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("ngram", help="File contaning ngram counts")
    parser.add_argument("--min", type=int, help="Minumum count")
    args = parser.parse_args()

    print("loading", args.ngram, file=sys.stderr)

    data = defaultdict(list)
    with smart_open.open(args.ngram, "rt") as infile:
        current_match = None
        matches = []
        matched_mixed_case = True
        total = 0
        for line in infile:
            ngram, count, *_ = line.split("\t")
            count = int(count)

            if "_" in ngram:
                raise ValueError("ngram contains _, is it word_pos format?:", line)

            lower = ngram.lower()
            if current_match and current_match != lower:
                if matched_mixed_case and total >= args.min:
                    print_matches(matches, current_match, total)
                matches = []
                total = 0
                matched_mixed_case = False

            current_match = lower
            matches.append((ngram, count))
            total += count
            if not matched_mixed_case and ngram != lower:
                matched_mixed_case = True


if __name__ == "__main__":
    main()
