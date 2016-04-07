# T: Lx
# Jonathan Gordon

import sys
import os
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
