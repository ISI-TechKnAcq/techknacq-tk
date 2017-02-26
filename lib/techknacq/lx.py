# TechKnAcq: Lx
# Jonathan Gordon

import sys
import os
import re
import nltk


# Path to data files.
try:
    MOD_PATH = os.path.dirname(os.path.realpath(__file__))
except AttributeError:
    sys.exit('__file__ is not defined; cannot find data.')
DATA_DIR = os.path.join(MOD_PATH, 'data')


class Lexicon:
    def __init__(self, listname):
        """Read a specified lexicon from disk."""
        self.words = set()
        self.file = listname

        with open(listname) as f:
            for word in f.readlines():
                self.words.add(word.strip())

    def __contains__(self, word):
        """Check if the given word is in the lexicon."""
        return word in self.words


class ScrabbleLexicon(Lexicon):
    def __init__(self):
        """Read a Scrabble dictionary from disk."""
        Lexicon.__init__(self, listname=os.path.join(DATA_DIR, 'scrabble.txt'))


class StopLexicon(Lexicon):
    def __init__(self):
        """Read a stoplist from disk."""
        Lexicon.__init__(self, listname=os.path.join(DATA_DIR, 'stop.txt'))


####


class SentTokenizer:
    abbrevs = ['dr', 'vs', 'mr', 'mrs', 'prof', 'e.g', 'i.e', 'viz', 'cf',
               'proc', 'b', 'dept', 'p', 'pp', 'ca', 'esp', 'eq', 'eqn',
               'fig', 'al', 'm.a', 'm.s', 'engl']

    def __init__(self):
        self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        self.tokenizer._params.abbrev_types.update(self.abbrevs)

    def tokenize(self, text):
        return self.tokenizer.tokenize(text, realign_boundaries=True)


####

# Based on the algorithm described in
#   A. Schwartz & M. Hearst, 2003: A Simple Algorithm for Identifying
#   Abbreviation Definitions in Biomedical Text.

def find_short_long_pairs(sent):
    def check_short(s):
        if len(s) < 2 or len(s) > 10:
            return False
        if len(s.split()) > 2:
            return False
        if not s[0].isalnum():
            return False
        return any(c.isupper() for c in s)

    def find_best_long(sh, lo):
        if len(lo) < len(sh):
            return
        sh_index = len(sh) - 1
        lo_index = len(lo) - 1
        while True:
            sh_char = sh[sh_index].lower()
            try:
                lo_char = lo[lo_index].lower()
            except IndexError:
                return
            if not sh_char.isalnum():
                sh_index -= 1
            if sh_index == 0:
                if sh_char == lo_char:
                    if lo_index <= 0 or not lo[lo_index-1].isalnum():
                        break
            elif sh_char == lo_char:
                sh_index -= 1
            lo_index -= 1
        if lo_index < 0:
            return

        lo = lo[lo_index:]
        words = lo.split()
        sh_chars = len(sh)
        if len(words) > min([sh_chars+5, sh_chars*2]):
            return
        if words[0] in ['in', 'of', 'from']:
            return
        if '(' in lo or ')' in lo:
            return
        return re.sub(' +', ' ', lo).strip()

    def extract_long(sh, sent):
        """Given a short form and the sentence it occurs in, find the
        long form."""
        before = re.sub(r' \(' + re.escape(s) + r'\).*', '', sent)
        before = re.sub('.*[,;]', '', before)

        lo = find_best_long(sh, before)
        if not lo:
            return

        tokens = re.split(r'[\t\n\r\f- ]', lo)
        long_size = len(tokens)
        short_size = len(sh)

        for c in sh:
            if not c.isalnum():
                short_size -= 1
            if len(lo) < len(sh) or sh in tokens or lo.endswith(sh) or \
               long_size > short_size*2 or long_size > short_size + 5 or \
               short_size > 10:
                return
        return lo

    ret = set()
    for sh in re.findall(r' \(([^()]+)\)', sent):
        if check_short(sh):
            lo = extract_long(sh, sent)
            if lo:
                ret.add((sh, lo))
    return ret
