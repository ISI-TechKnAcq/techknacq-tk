# T: Lx
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
               'fig', 'al']

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

    def find_best_long(s, l):
        if len(l) < len(s):
            return
        s_index = len(s) - 1
        l_index = len(l) - 1
        while True:
            s_char = s[s_index].lower()
            try:
                l_char = l[l_index].lower()
            except:
                return
            if not s_char.isalnum():
                s_index -= 1
            if s_index == 0:
                if s_char == l_char:
                    if l_index <= 0 or not l[l_index-1].isalnum():
                        break
            elif s_char == l_char:
                s_index -= 1
            l_index -= 1
        if l_index < 0:
            return

        l = l[l_index:]
        words = l.split()
        s_chars = len(s)
        if len(words) > min([s_chars+5, s_chars*2]):
            return
        if words[0] in ['in', 'of', 'from']:
            return
        if '(' in l or ')' in l:
            return
        return re.sub(' +', ' ', l).strip()

    def extract_long(s, sent):
        """Given a short form and the sentence it occurs in, find the
        long form."""
        before = re.sub(' \(' + re.escape(s) + '\).*', '', sent)
        before = re.sub('.*[,;]', '', before)

        l = find_best_long(s, before)
        if not l:
            return

        tokens = re.split(r'[\t\n\r\f- ]', l)
        long_size = len(tokens)
        short_size = len(s)

        for c in s:
            if not c.isalnum():
                short_size -= 1
            if (len(l) < len(s) or
                s in tokens or
                l.endswith(s) or
                long_size > short_size*2 or
                long_size > short_size + 5 or
                short_size > 10):
                return
        return l

    ret = set()
    for s in re.findall(' \(([^()]+)\)', sent):
        if check_short(s):
            l = extract_long(s, sent)
            if l:
                ret.add((s, l))
    return ret
