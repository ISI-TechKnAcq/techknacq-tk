# T: Corpus
# Jonathan Gordon

from __future__ import unicode_literals

import os
import io
import json


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

    def export(self, outdir, format='json'):
        for d in self.docs:
            if format == 'json':
                with io.open(os.path.join(outdir, d.id + '.json'), 'w',
                             encoding='utf8') as out:
                    out.write(d.json())
            elif format == 'bioc':
                with io.open(os.path.join(outdir, d.id + '.xml'), 'w',
                             encoding='utf8') as out:
                    out.write(d.bioc())
            elif format == 'text':
                with io.open(os.path.join(outdir, d.id + '.txt'), 'w',
                             encoding='utf8') as out:
                    out.write(d.text())


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
            'references': list(self.references),
            'sections': self.sections
        }
        return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False)

    def bioc(self):
        """Return a BioC XML string representing the document."""
        pass

    def text(self):
        """Return a plain-text string representing the document."""
        t = str()
        for s in self.sections:
            if 'heading' in s:
                t += '\n\n' + s['heading'] + '\n\n'
            t += '\n'.join(s['text'])
        return t
