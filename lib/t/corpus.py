# T: Corpus
# Jonathan Gordon

import sys
import os
import io
import json
import datetime

from gensim import corpora, utils

from xml.sax.saxutils import escape


class Corpus:
    def __init__(self):
        self.docs = set()

    def load(self, dirname):
        for docname in os.listdir(dirname):
            filepath = os.path.join(dirname, docname)
            if os.path.isdir(filepath):
                continue
            try:
                d = Document(file=filepath)
            except Exception as e:
                print('Error reading document:', filepath, file=sys.stderr)
                print(e, file=sys.stderr)
                continue
            self.add(d)

    def add(self, doc):
        self.docs.add(doc)

    def __ior__(self, other):
        self.docs |= other.docs
        return self

    def __iter__(self):
        for x in self.docs:
            yield x

    def export(self, outdir, format='json'):
        for d in self.docs:
            if format == 'json':
                with io.open(os.path.join(outdir, d.id + '.json'), 'w',
                             encoding='utf8') as out:
                    out.write(d.json() + '\n')
            elif format == 'bioc':
                with io.open(os.path.join(outdir, d.id + '.xml'), 'w',
                             encoding='utf8') as out:
                    out.write(d.bioc() + '\n')
            elif format == 'text':
                with io.open(os.path.join(outdir, d.id + '.txt'), 'w',
                             encoding='utf8') as out:
                    out.write(d.text() + '\n')


class TextCorpus(Corpus):
    """A corpus for use in gensim-based topic modeling."""

    def load(self, dirname):
        Corpus.load(self, dirname)
        self.dictionary = corpora.Dictionary(self.iter_docs())
        self.dictionary.filter_extremes()

    def iter_docs(self):
        for doc in self.docs:
            yield utils.simple_preprocess(doc.text())

    def __iter__(self):
        for tokens in self.iter_docs():
            yield self.dictionary.doc2bow(tokens)


class Document:
    def __init__(self, file=None):
        if file and '.json' in file:
            j = json.load(io.open(file, 'r', encoding='utf8'))
        else:
            j = {'info': {}}

        self.id = j['info'].get('id', '')
        self.authors = [x.strip() for x in j['info'].get('authors', [])]
        self.title = j['info'].get('title', '')
        self.book = j['info'].get('book', '')
        self.url = j['info'].get('url', '')
        self.references = set(j.get('references', []))
        self.sections = j.get('sections', [])


    def json(self):
        """Return a JSON string representing the document."""
        doc = {
            'info': {
                'id': self.id,
                'authors': self.authors,
                'title': self.title,
                'book': self.book,
                'url': self.url
            },
            'references': sorted(list(self.references)),
            'sections': self.sections
        }
        return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False)


    def bioc(self):
        """Return a BioC XML string representing the document."""

        t = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE collection SYSTEM "BioC.dtd">
<collection>
<source>TechKnAcq</source>
<key>techknacq.key</key>
'''
        t += '<date>' + datetime.date.today().isoformat() + '</date>'
        t += '<document>'
        t += '<id>' + escape(self.id) + '</id>'
        t += '<passage><offset>0</offset>'
        t += '<infon key="authors">'
        t += escape('; '.join(self.authors)) + '</infon>'
        t += '<infon key="title">' + escape(self.title) + '</infon>'
        t += '<infon key="book">' + escape(self.book) + '</infon>'
        t += '<infon key="url">' + escape(self.url) + '</infon>'
        t += '<text>'
        for s in self.sections:
            if s.get('heading'):
                t += escape(s['heading']) + ' '
            t += escape(' '.join(s['text']))
            if s != self.sections[-1]:
                t += ' '
        t += '</text>'
        t += '</passage></document></collection>'
        return filter_non_printable(t)


    def text(self):
        """Return a plain-text string representing the document."""
        t = self.title + '\n\n'
        for s in self.sections:
            if 'heading' in s and s['heading']:
                t += '\n\n' + s['heading'] + '\n\n'
            t += '\n'.join(s['text'])
        return filter_non_printable(t)


def filter_non_printable(s):
    return ''.join([c for c in s if ord(c) > 31 or ord(c) == 9 or c == '\n'])
