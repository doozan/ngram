#!/usr/bin/python3

import contextlib
import json
import sys
import smart_open

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


def summarize_line(line, min_year=0, max_year=0):
    year_found = not min_year
    items = line.split('\t')
    total = 0
    for year_item in items[1:]:

        if not year_found:
            if int(year_item[:4]) <= min_year:
                continue
            year_found = True

        if max_year and int(year_item[:4]) > max_year:
            break

        year, use_count, source_count = year_item.split(",")
        total += int(use_count)

    return items[0], total

def process(infilename, outfilename, min_total=0, min_year=0, limit=0):
    with open(outfilename, "wt") as outfile:
        with open(infilename, "rt") as fh:
            for count, line in enumerate(fh):
                if limit and count > limit:
                    break
                ngram, total = summarize_line(line, min_year)
                if total > min_total:
                    outfile.write(f"{ngram}\t{total}\n")

def lambda_handler(event, context):

    process(event["infile"], event["outfile"], event.get("min_total", 0), event.get("min_year", 0), event.get("limit", 0))

    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {event["infile"]} -> {event["outfile"]}')
    }

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("infile", help="read data from url")
    parser.add_argument("--outfile", "-o", help="read data from file")
    parser.add_argument("--min-year", type=int, help="Ignore usage before the specified year")
    parser.add_argument("--min-total", type=int, help="Only print entries with at least N uses", default=0)
    parser.add_argument("--limit", type=int, help="Limit processing to first N entries", default=0)
    args = parser.parse_args()

    lambda_handler(vars(args), None)
