#!/usr/bin/python3

import argparse
import re
import sys

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

def main():
    global args
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("--year", help="min year", type=int, required=True)
    args = parser.parse_args()

    for idx, line in enumerate(sys.stdin):

        if not idx % 10000:
            print(idx, end = '\r', file=sys.stderr)

        # ignore unhandled words
        if not re.match("^[A-ZÁÉÍÑÓÚÜa-záéíñóúü.]+\t", line):
            continue

        ngram, yeardata = line.split("\t", 1)

        if not ngram.strip("."):
            continue

        total = process_yeardata(yeardata, args.year)
        if not total:
            continue

        print(f"{ngram}\t{total}")

if __name__ == "__main__":
    main()
