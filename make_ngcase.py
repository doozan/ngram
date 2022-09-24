#!/usr/bin/python3

import argparse
import smart_open
import sys
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("ngram2", help="File contaning single word ngram counts")
    parser.add_argument("--min", type=int, help="Minumum count")
    args = parser.parse_args()

    print("loading", args.ngram2, file=sys.stderr)

    data = defaultdict(list)
    with smart_open.open(args.ngram2, "rt") as infile:
        for line in infile:
            ngram, count, *_ = line.split("\t")
            if "_" in ngram:
                raise ValueError("ngram contains _, is it word_pos format?:", line)

            words = ngram.split()
            if not len(words) == 2:
                raise ValueError("ngram is not 2 words", ngram)
            word = words[1]

            lc = word.lower()
            data[lc].append((word, int(count)))

    for word, components in data.items():
        total = sum(x[1] for x in components)
        alts = defaultdict(int)
        for alt_case, count in components:
            if alt_case == word:
                continue
            alts[alt_case] += count

        for alt_case, count in alts.items():
            if args.min and count < args.min:
                continue
            if count*10 > total:
                #print(f"{alt_case}\t{count}\t{word}\t{total}\t{int(count/total*100)}%")
                print(f"{alt_case}\t{int(count/total*100)}")

if __name__ == "__main__":
    main()
