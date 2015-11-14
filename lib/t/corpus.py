# T: Corpus
# Jonathan Gordon

from __future__ import unicode_literals

import os
import io
import json


class Corpus:
    def __init__(self):
        self.docs = set()

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
    def __init__(self):
        self.id = ''
        self.authors = []
        self.title = ''
        self.book = ''
        self.url = ''
        self.sections = []
        self.references = set()

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
        pass
