# T: Corpus
# Jonathan Gordon

from __future__ import unicode_literals

import os
import io
import json
import datetime

from xml.sax.saxutils import escape


class Corpus:
    def __init__(self):
        self.docs = set()

    def load(self, dirname):
        for docname in os.listdir(dirname):
            filepath = os.path.join(dirname, docname)
            if os.path.isdir(filepath):
                continue
            d = Document(file=filepath)
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


class Document:
    def __init__(self, file=None):
        if file:
            j = json.load(io.open(file, 'r', encoding='utf8'))
        else:
            j = {'info': {}}

        self.id = j['info'].get('id', '')
        self.authors = j['info'].get('authors', [])
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

        t = '''
<?xml? version="1.0" encoding="UTF-8"?>
<!DOCTYPE collection SYSTEM "BioC.dtd">
<collection>
<source>TechKnAcq</source>
<key>techknacq.key</key>
'''
        t += '<date>' + datetime.date.today().isoformat() + '</date>'
        t += '<document>'
        t += '<id>' + self.id + '</id>'
        t += '<passage><offset>0</offset>'
        t += '<infon key="authors">' + ', '.join(self.authors) + '</infon>'
        t += '<infon key="title">' + self.title + '</infon>'
        t += '<infon key="book">' + self.book + '</infon>'
        t += '<infon key="url">' + self.url + '</infon>'
        t += '<text>'
        for s in self.sections:
            if s.get('heading'):
                t += escape(s['heading']) + ' '
            t += escape(' '.join(s['text']))
            if s != self.sections[-1]:
                t += ' '
        t += '</text>'
        t += '</passage></document></collection>'
        return t


    def text(self):
        """Return a plain-text string representing the document."""
        t = self.title + '\n\n'
        for s in self.sections:
            if 'heading' in s and s['heading']:
                t += '\n\n' + s['heading'] + '\n\n'
            t += '\n'.join(s['text'])
        return t
