# T: Corpus
# Jonathan Gordon

import sys
import os
import io
import json
import datetime
import re
import multiprocessing as mp

from gensim import corpora, utils
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup
from pathlib import Path

from t.lx import SentTokenizer

class Corpus:
    def __init__(self):
        self.docs = set()

    def load(self, dirname, pool=None):
        if not pool:
            pool = mp.Pool(int(.5 * mp.cpu_count()))

        docnames = (str(f) for f in Path(dirname).iterdir() if f.is_file())
        for doc in pool.imap(Document, docnames):
            if doc:
                self.add(doc)

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
    def __init__(self, fname=None, format=None):
        if not format and 'json' in fname:
            format = 'json'
        if not format and 'xml' in fname:
            format = 'sd'

        j = {'info': {}}
        if fname and format == 'json':
            try:
                j = json.load(io.open(fname, 'r', encoding='utf8'))
            except Exception as e:
                print('Error reading JSON document:', fname, file=sys.stderr)
                print(e, file=sys.stderr)

        self.id = j['info'].get('id', '')
        self.authors = [x.strip() for x in j['info'].get('authors', [])]
        self.title = title_case(j['info'].get('title', ''))
        self.book = title_case(j['info'].get('book', ''))
        self.year = j['info'].get('year', '')
        self.url = j['info'].get('url', '')
        self.references = set(j.get('references', []))
        self.sections = j.get('sections', [])

        if fname and format == 'sd':
            self.read_sd(file)


    def read_sd(self, f, fref=None):
        """Read document contents from a ScienceDirect XML file."""

        xml = io.open(f, 'r', encoding='utf8').read()
        xml = re.sub("([</])(dc|prism|ce|sb|xocs):", r"\1", xml)
        soup = BeautifulSoup(xml, 'lxml')

        try:
            pii = re.sub('[()-]', '', soup.find('pii').string)
        except:
            print('No PII found for', f)
            return

        self.id = 'sd-' + pii
        self.authors = [x.string.strip() for x in soup('creator')]

        if not self.authors and soup.editor:
            self.authors = [x.get_text() + ' (ed.)' for x in
                            soup.editor('authors')]

        if soup.title:
            self.title = soup.title.string.strip()
        if soup.publicationname:
            self.book = soup.publicationname.string.strip()
        self.url = 'http://www.sciencedirect.com/science/article/pii/' + pii
        self.authors = [x.string.strip() for x in soup('creator')]
        if soup.coverdate:
            # Dates are in format YYYY-MM-DD
            self.year = int(re.sub('-.*', soup.coverdate.string))

        st = SentTokenizer()
        if soup.abstract:
            sec = {'heading': 'Abstract',
                   'text': st.tokenize(soup.find('abstract-sec').get_text())}
            self.sections.append(sec)

        for section in soup.find_all('section'):
            sec = {'text': []}
            heading = section.find('section-title')
            if heading and heading.string:
                sec['heading'] = heading.string.strip()
            for p in section.find_all(['para', 'simple-para']):
                sec['text'] += st.tokenize(p.get_text())
            self.sections.append(sec)

        if len(self.sections) <= 1:
            sec = {'text': []}
            for p in soup.find_all(['para', 'simple-para']):
                sec['text'] += st.tokenize(p.get_text())
            self.sections.append(sec)

        if soup.rawtext and len(self.sections) < 3:
            self.sections.append({'text': st.tokenize(soup.rawtext.get_text())})

        if len(self.text()) < 200:
            print(' ! Skip:', self.title, self.id + '. Missing text.')
            return

        if fref and os.path.exists(fref):
            reftext = io.open(fref, 'r', encoding='utf8').read()
            self.references = list(set([x.replace('PII:', 'sd-') for x in
                                        re.findall('PII:[^<]+', reftext)]))


    def get_abstract(self):
        """Return the (probable) abstract for the document."""

        if len(self.sections[0]['text']) > 2:
            return self.sections[0]['text'][:10]
        if len(self.sections) > 1:
            return self.sections[1]['text'][:10]
        return self.sections[0]['text'][:10]


    def json(self):
        """Return a JSON string representing the document."""

        doc = {
            'info': {
                'id': self.id,
                'authors': self.authors,
                'title': self.title,
                'year': self.year,
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
        t += '<infon key="year">' + escape(self.year) + '</infon>'
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

def title_case(s):
    for word in ['And', 'The', 'Of', 'From', 'To', 'In', 'For', 'A', 'An',
                 'On']:
        s = re.sub('([A-Za-z]) ' + word + ' ', r'\1 ' + word.lower() + ' ', s)
    return s
