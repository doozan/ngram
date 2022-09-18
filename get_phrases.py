#!/usr/bin/python3

import argparse
import smart_open
import sys

from collections import defaultdict
from enwiktionary_wordlist.all_forms import AllForms

def case_matches(target, match):
    # Returns True if all capitalized words in target exactly match the correspanding match words
    # if a word in target is all lowercase, the case of match doesn't matter

    stripped_target = target.replace(",", "").replace("¿", "").replace("?", "")

    target_words = stripped_target.split()
    match_words = match.split()

    if stripped_target.lower() != match.lower():
        raise ValueError(target, stripped_target.lower(), match.lower())

    assert len(target_words) == len(match_words)

    for x in range(len(target_words)):
        if target_words[x] == target_words[x].lower():
            continue
        if target_words[x] == match_words[x]:
            continue
        return False

    return True


def get_segments(words, ngram_max=5):

    # Get offsets of all possible 5-word segments from a list of words
    # If words <= ngram_max, returns a list containing only one offset
    # returns [(0, 5), (1, 6), ...]

    segments = []
    if len(words) <= ngram_max:
        segments.append((0, len(words)))
    else:
        for x in range(len(words)-ngram_max+1):
            segments.append((x, x+ngram_max))

    return segments


def get_count_matches(search_phrase, search_targets, search_results):

    phrase_words = search_phrase.split()
    upper_words = search_phrase.upper().split()
    segments = get_segments(upper_words)

    max_count = None
    matches = []
    for start, end in segments:
        upper_segment = " ".join(upper_words[start:end])
        phrase_segment = " ".join(phrase_words[start:end])

        segment_count = 0
        for match in search_targets[upper_segment]:
            if case_matches(phrase_segment, match):
                match_count = search_results[match]
                matches.append((match, match_count))
                segment_count += match_count

        if max_count is None:
            max_count = segment_count
        elif max_count > segment_count:
            max_count = segment_count

    return max_count, matches


def iter_form_lemmas(allforms):

    for form, pos, lemma in allforms.all:
        if not lemma.count(" ") or lemma.count(" ") != form.count(" "):
            continue

        # skip drae forms with notes
        if "[" in lemma:
            continue

        # Remove characters that won't be in the ngram database
        stripped_form = form.replace(",", "").replace("¿", "").replace("?", "")
        if not stripped_form.strip():
            continue

        yield stripped_form, lemma


def get_search_targets(allforms):
    search_targets = {}

    for form, lemma in iter_form_lemmas(allforms):

        upper_ngram = form.upper()
        upper_words = upper_ngram.split()
        segments = get_segments(upper_words)

        for start, end in segments:
            upper_segment = " ".join(upper_words[start:end])
            search_targets[upper_segment] = []

    return search_targets

def iter_corpus_db(filename):
    from ngram.ngramdb import NgramDB
    ngramdb = NgramDB(filename)
    yield from ngramdb._cursor.execute("SELECT phrase, count FROM ngram;")

def iter_corpus_files(files):
    for filename in files:
        print("scanning", filename, file=sys.stderr)
        with smart_open.open(filename) as infile:
            for line in infile:
                yield line.split("\t")

def search_corpus(generator, search_targets):

    count_rows = 0
    count_matches = 0
    search_results = {}

    for ngram, count in generator:
        if not count_rows % 1000000:
            print(count_rows, end = '\r', file=sys.stderr)
        count_rows += 1

        upper_ngram = ngram.upper()
        if upper_ngram in search_targets:
            orig_form = ngram
            search_targets[upper_ngram].append(orig_form)
            search_results[orig_form] = int(count)
            count_matches += 1
#            if count_matches > 100:
#                break

    print("done, scanned", count_rows, count_matches, file=sys.stderr)
    return search_results


class Lemma():
    def __init__(self):
        self.ngrams = []
        self.count = 0

def get_lemma_counts(allforms, search_results, search_targets):

    lemma_counts = defaultdict(Lemma)

    for form, lemma in iter_form_lemmas(allforms):
        count, matches = get_count_matches(form, search_targets, search_results)
        if not count:
            continue

        lemma_counts[lemma].ngrams += matches
        lemma_counts[lemma].count += count

    return lemma_counts


def adjust_embedded(lemma_counts):

    embedded = defaultdict(list)

    for lemma in sorted(lemma_counts, key=lambda x: len(x.split())*-1):
        for bigger_lemma in embedded.get(lemma, []):
            bigger_count = lemma_counts[bigger_lemma].count
            lemma_counts[lemma].count -= bigger_count
            lemma_counts[lemma].ngrams.append((bigger_lemma, bigger_count*-1))
            if lemma_counts[lemma].count < 0:
                raise ValueError("less that zero", lemma, bigger_lemma)

        lemma_words = tuple(lemma.split())
        for size in [2,3,4,5]:
            for start, end in get_segments(lemma_words, size):
                lemma_segment = " ".join(lemma_words[start:end])
                embedded[lemma_segment].append(lemma)

def print_lemma_totals(lemma_counts):

    for lemma, lemma_count in sorted(lemma_counts.items(), key=lambda x: x[1].count*-1):

        ngram_list = []
        for ngram, ngram_count in lemma_count.ngrams:
            ngram_combo = f"{ngram}:{ngram_count}"
            if ngram_combo not in ngram_list:
                ngram_list.append(ngram_combo)

        ngram_str = "; ".join(ngram_list)
        print(f"{lemma}\t{lemma_count.count}\t{ngram_str}")


def main():
    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("--allforms", required=True)
    parser.add_argument("--ngramdb")
    parser.add_argument("--adjust-embedded", action='store_true')
    parser.add_argument("ngram", nargs="*")
    args = parser.parse_args()

    if args.ngramdb and args.ngram:
        raise ValueError("Use ngram DB or ngram files, not both")

    allforms = AllForms.from_file(args.allforms)

    # Since the ngram data contains a wide range of capitalizations, which may or may not be important to the phrases
    # ex "hasta la fetcha" should match any case variation but "Nuestro Señor" should not match lowercase variations
    search_targets = get_search_targets(allforms)

    generator = iter_corpus_files(args.ngram) if args.ngram else iter_corpus_db(args.ngramdb)
    search_results = search_corpus(generator, search_targets)

    lemma_counts = get_lemma_counts(allforms, search_results, search_targets)

    if args.adjust_embedded:
        adjust_embedded(lemma_counts)

    print_lemma_totals(lemma_counts)

if __name__ == "__main__":
    main()
