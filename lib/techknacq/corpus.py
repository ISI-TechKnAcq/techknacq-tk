# TechKnAcq: Corpus
# Jonathan Gordon

import sys
import os
import io
import json
import datetime
import re
import multiprocessing as mp
import enchant
import ftfy

from pathlib import Path
from bs4 import BeautifulSoup
from xml.sax.saxutils import escape
from unidecode import unidecode
from nltk import bigrams

from lib.techknacq.lx import SentTokenizer, StopLexicon, find_short_long_pairs

class Corpus:
    def __init__(self, path=None, pool=None):
        self.docs = {}

        if path and os.path.isfile(path):
            # Read a BioC corpus file.
            j = json.load(open(path))
            for d in j['documents']:
                doc = Document()
                doc.read_bioc_json(d)
                self.add(doc)
        elif path:
            if not pool:
                pool = mp.Pool(int(.5 * mp.cpu_count()))

            docnames = (str(f) for f in Path(path).iterdir() if f.is_file())
            for doc in pool.imap(Document, docnames):
                if doc:
                    self.add(doc)
            print('Read %d documents.' % len(self.docs))

        if os.path.exists('data/pedagogical-roles.txt'):
            print('Loading pedagogical roles.')
            self.read_roles('data/pedagogical-roles.txt')

    def clear(self):
        self.docs = {}

    def add(self, doc):
        assert(type(doc) == Document)
        doc.corpus = self
        self.docs[doc.id] = doc

    def __ior__(self, other):
        for doc in other:
            self.add(doc)
        return self

    def __iter__(self):
        for doc_id in self.docs:
            yield self.docs[doc_id]

    def __getitem__(self, key):
        return self.docs[key]

    def __setitem__(self, key, item):
        self.docs[key] = item

    def __contains__(self, key):
        return key in self.docs

    def fix_text(self):
        for doc in self:
            doc.dehyphenate()
            #doc.expand_short_forms()

    def export(self, dest, abstract=False, form='json'):
        if form not in ['json', 'bioc', 'text', 'bigrams']:
            print('Unrecognized form for export', form, file=sys.stderr)
            sys.exit(1)

        if form == 'bigrams':
            stop = StopLexicon()

        for d in self:
            if form == 'json':
                with io.open(os.path.join(dest, d.id + '.json'), 'w',
                             encoding='utf-8') as out:
                    out.write(d.json(abstract) + '\n')
            elif form == 'bioc':
                with io.open(os.path.join(dest, d.id + '.xml'), 'w',
                             encoding='utf-8') as out:
                    out.write(d.bioc(abstract) + '\n')
            elif form == 'text':
                with io.open(os.path.join(dest, d.id + '.txt'), 'w',
                             encoding='utf-8') as out:
                    out.write(d.text(abstract) + '\n')
            elif form == 'bigrams':
                with io.open(os.path.join(dest, d.id + '.txt'), 'w',
                             encoding='utf-8') as out:
                    out.write(d.bigrams(abstract, stop) + '\n')


    def read_roles(self, fname):
        role_annotations = {}
        for line in open(fname):
            if line.startswith('doc_id'):
                continue
            vals = line.strip().split('\t')
            doc_id = vals[0]
            role_annotations[doc_id.lower()] = \
              {'survey': float(vals[1]),
               'tutorial': float(vals[2]),
               'resource': float(vals[3]),
               'reference': float(vals[4]),
               'empirical': float(vals[5]),
               'manual': float(vals[6]),
               'other': float(vals[7])}
        for doc in self:
            prior = None
            if doc.id.startswith('wiki-'):
                prior = {'survey': 0.2,
                         'tutorial': 0.0,
                         'resource': 0.0,
                         'reference': 0.8,
                         'empirical': 0.0,
                         'manual': 0.0,
                         'other': 0.0}
            elif doc.id.startswith('web-') or 'Tutorials' in doc.book:
                prior = {'survey': 0.1,
                         'tutorial': 0.6,
                         'resource': 0.0,
                         'reference': 0.0,
                         'empirical': 0.0,
                         'manual': 0.2,
                         'other': 0.1}
            elif doc.id.startswith('acl-'):
                prior = {'survey': 0.0,
                         'tutorial': 0.0,
                         'resource': 0.1,
                         'reference': 0.0,
                         'empirical': 0.8,
                         'manual': 0.0,
                         'other': 0.1}
            elif doc.id.startswith('sd-'):
                prior = {'survey': 0.1,
                         'tutorial': 0.1,
                         'resource': 0.0,
                         'reference': 0.7,
                         'empirical': 0.0,
                         'manual': 0.0,
                         'other': 0.1}

            short_id = re.sub('^(acl|wiki|sd|web)-', '', doc.id.lower())
            annotation = role_annotations.get(short_id)

            if prior and annotation:
                doc.roles = {}
                for role in prior:
                    doc.roles[role] = (prior[role] + annotation[role]) / 2.0
            elif annotation:
                doc.roles = annotation
            elif prior:
                doc.roles = prior
            else:
                doc.roles = {'survey': 0.0,
                             'tutorial': 0.0,
                             'resource': 0.0,
                             'reference': 0.0,
                             'empirical': 0.0,
                             'manual': 0.0,
                             'other': 0.0}


class Document:
    def __init__(self, fname=None, form=None):
        if fname and not form:
            if 'json' in fname:
                form = 'json'
            elif 'xml' in fname:
                form = 'sd'
            elif 'txt' in fname:
                form = 'text'

        j = {'info': {}}
        if fname and form == 'json':
            try:
                j = json.load(io.open(fname, 'r', encoding='utf-8'))
            except Exception as e:
                print('Error reading JSON document:', fname, file=sys.stderr)
                print(e, file=sys.stderr)
                sys.exit(1)

        if 'id' in j['info']:
            self.id = j['info']['id']
        else:
            basename = os.path.basename(fname)
            basename = re.sub('\.(json|xml|txt)$', '', basename)
            self.id = basename
        self.authors = [x.strip() for x in j['info'].get('authors', [])]
        self.title = title_case(j['info'].get('title', ''))
        self.book = title_case(j['info'].get('book', ''))
        self.year = j['info'].get('year', '')
        self.url = j['info'].get('url', '')
        self.references = set(j.get('references', []))
        self.sections = j.get('sections', [])
        self.roles = {}
        self.corpus = None

        if fname and form == 'text':
            st = SentTokenizer()
            self.sections = [{'text': st.tokenize(open(fname).read())}]
        elif fname and form == 'sd':
            self.read_sd(fname)


    def read_bioc_json(self, j):
        """Read a document from a JSON-formatted BioC representation.
        Currently this is specific to the PubMed corpus it was used on."""

        self.id = 'pmc-' + j['id']
        self.url = j['infons']['xref']

        st = SentTokenizer()
        for i, passage in enumerate(j['passages']):
            if i == 0:
                lines = passage['text'].splitlines()[:3]
                # Guess that the author is the second line and the book
                # title and year are the third line.
                self.authors = lines[1].split(', ')
                self.book = re.sub(r' \(.+', '', lines[2])
                m = re.match(r'.*\(([0-9]+)\)', lines[2])
                if m:
                    self.year = int(m.group(1))
            for annotation in passage['annotations']:
                if annotation['infons']['value'] == 'article-title':
                    a = annotation['locations'][0]['offset']
                    b = a + annotation['locations'][0]['length']
                    self.title = passage['text'][a:b-1]
                elif annotation['infons']['value'] == 'abstract':
                    a = annotation['locations'][0]['offset'] - 1
                    b = a + annotation['locations'][0]['length']
                    sec = {}
                    sec['heading'] = 'Abstract'
                    sec['text'] = st.tokenize(passage['text'][a:b])
                    if sec['text'][0] != 'null':
                        self.sections.append(sec)
                else:
                    sys.sterr.write('Unexpected infon value %s.\n' %
                                    (anntoation['infons']['value']))


    def read_sd(self, f, fref=None):
        """Read document contents from a ScienceDirect XML file."""

        def get_para_sents(p):
            if p.find('list'):
                # Really this needs to be split into the paragraph text
                # before and after the list, but BeautifulSoup is a pain, and
                # this is good enough.
                l = p.find('list').replace_with(' ... ')
                sents = [re.sub(r'\s+', ' ', x) for x in
                         st.tokenize(p.get_text())]
                for para in l.find_all(['para', 'simple_para']):
                    sents.extend([re.sub(r'\s+', ' ', x) for x in
                                  st.tokenize(para.get_text())])
                return sents
            return [re.sub(r'\s+', ' ', x) for x in
                    st.tokenize(p.get_text())]

        if '-ref.xml' in f:
            return

        xml = io.open(f, 'r', encoding='utf-8').read()
        xml = ftfy.fix_text(xml, uncurl_quotes=False,
                            fix_entities=False)
        xml = strtr(xml, {'e´': 'é', 'e`': 'è'})
        xml = re.sub("([</])(dc|prism|ce|sb|xocs):", r"\1", xml)
        soup = BeautifulSoup(xml, 'lxml')

        try:
            pii = re.sub('[()-.]', '', soup.find('pii').string)
        except:
            print('No PII found for', f)
            return

        self.id = 'sd-' + pii.lower()
        self.authors = []
        try:
            for author in soup('creator'):
                x = author.string.strip()
                name = re.sub('^.*, ', '', x) + ' ' + re.sub(',.*$', '', x)
                self.authors.append(name)
        except:
            pass

        if not self.authors and soup.editor:
            self.authors = [x.get_text() + ' (ed.)' for x in
                            soup.editor('authors')]

        if soup.title:
            self.title = soup.title.string.strip()
        if soup.publicationname:
            self.book = soup.publicationname.string.strip()
        self.url = 'http://www.sciencedirect.com/science/article/pii/' + pii
        if soup.coverdate:
            # Dates are in format YYYY-MM-DD
            self.year = int(re.sub('-.*', '', soup.coverdate.string))

        st = SentTokenizer()
        if soup.abstract:
            sec = {'heading': 'Abstract',
                   'text': st.tokenize(soup.find('abstract-sec').get_text())}
            self.sections.append(sec)

        sec_id = ''
        sec = {'text': []}
        sec_last = {'text': []}
        for p in soup.find_all(['para', 'simple-para']):
            if p.find_parents('outline'):
                continue
            elif p.find('list') and p.find('list').find('section-title'):
                continue
            elif p.find_parents('para'):
                continue
            elif p.find_parents('floats'):
                # Lest these show up at the start and be treated as an
                # abstract.
                sec_last['text'] += get_para_sents(p)
                continue
            if p.parent.name in ['section', 'biography']:
                p_sec_id = p.parent.get('id', '')
                if p_sec_id != sec_id:
                    if sec['text']:
                        self.sections.append(sec)
                    sec = {'text': []}
                    sec_id = p_sec_id
                    heading = p.parent.find('section-title')
                    if heading and heading.string:
                        sec['heading'] = heading.string.strip()
                    elif p.parent.name == 'biography':
                        sec['heading'] = 'Biography'
            sec['text'] += get_para_sents(p)
        if sec['text']:
            self.sections.append(sec)
        if sec_last['text']:
            self.sections.append(sec_last)

        if soup.rawtext and len(self.sections) < 3:
            self.sections.append({'text': st.tokenize(soup.rawtext.get_text())})

        if len(self.text()) < 200:
            print(' ! Skip:', self.title, self.id + '. Missing text.')
            return

        if not fref:
            fref = f.replace('-full.xml', '-ref.xml')

        if os.path.exists(fref):
            reftext = io.open(fref, 'r', encoding='utf-8').read()
            self.references = set([x.replace('PII:', 'sd-').lower() for x in
                                   re.findall('PII:[^<]+', reftext)])


    def dehyphenate(self):
        """Fix words that were split with hyphens."""

        def dehyphenate_sent(s):
            words = s.split()
            out = []
            skip = False
            for w1, w2 in bigrams(words):
                if skip:
                    skip = False
                elif w1[-1] == '-':
                    if d.check(w1[:-1] + w2):
                        out.append(w1[:-1] + w2)
                        skip = True
                    elif w1[0].isalpha() and w2 != 'and':
                        out.append(w1 + w2)
                        skip = True
                    else:
                        out.append(w1)
                else:
                    out.append(w1)
            if not skip:
                out.append(words[-1])
            return ' '.join(out)

        # Learn the document-specific vocabulary:
        d = enchant.Dict('en')
        for word in re.split('\W+', self.text()):
            if word and word[-1] != '-':
                d.add_to_session(word)

        for sect in self.sections:
            if 'heading' in sect:
                sect['heading'] = dehyphenate_sent(sect['heading'])
            for i in range(len(sect['text'])):
                sect['text'][i] = dehyphenate_sent(sect['text'][i])


    def expand_short_forms(self):
        """Expand short forms (acronyms or abbreviations) in the document's
        text to the long forms found in the document."""

        def make_entity(x):
            return '#' + x.replace(' ', '_') + '#'

        # Find substitutions
        subs = {}
        for sent in self.text().splitlines():
            for s, l in find_short_long_pairs(sent.strip()):
                if s not in subs or len(l) < len(subs[s]):
                    subs[s] = l

        if len(subs) == 0:
            return

        # Substitute in text.
        rem_pat = re.compile(r'\((' + '|'.join([re.escape(x) for x in
                                                subs.keys()]) + r')\)')
        sub_pat = re.compile(r'\b(' + '|'.join([re.escape(x) for x in
                                                subs.keys()]) + r')\b')
        lon_pat = re.compile(r'\b(' + '|'.join([re.escape(x) for x in
                                                subs.values()]) + r')\b')
        for sect in self.sections:
            if 'heading' in sect:
                h = rem_pat.sub('', sect['heading'])
                h = lon_pat.sub(lambda x: make_entity(x.group()), h)
                h = sub_pat.sub(lambda x: make_entity(subs.get(x.group(),
                                                               x.group())), h)
                sect['heading'] = re.sub('\s+', ' ', h)
            for i in range(len(sect['text'])):
                s = rem_pat.sub('', sect['text'][i])
                s = lon_pat.sub(lambda x: make_entity(x.group()), s)
                s = sub_pat.sub(lambda x: make_entity(subs.get(x.group(),
                                                               x.group())), s)
                sect['text'][i] = re.sub(r'\s+', ' ', s)


    def get_abstract(self):
        """Return the (probable) abstract for the document."""

        if self.sections[0].get('heading', '') == 'Abstract':
            return self.sections[0]['text'][:10]
        if len(self.sections) > 1 and \
           self.sections[1].get('heading', '') == 'Abstract':
            return self.sections[1]['text'][:10]

        if len(self.sections[0]['text']) > 2:
            return self.sections[0]['text'][:10]
        if len(self.sections) > 1 and len(self.sections[1]['text']) > 2:
            return self.sections[1]['text'][:10]
        return self.sections[0]['text'][:10]


    def json(self, abstract=False):
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
            'references': sorted(list(self.references))
        }
        if abstract:
            doc['sections'] = [self.sections[0]]
        else:
            doc['sections'] = self.sections

        return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False)


    def bioc(self, abstract=False):
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
        t += '<infon key="year">' + escape(str(self.year)) + '</infon>'
        t += '<infon key="book">' + escape(self.book) + '</infon>'
        t += '<infon key="url">' + escape(self.url) + '</infon>'
        t += '<text>'
        for s in self.sections:
            if s.get('heading'):
                t += escape(s['heading']) + ' '
            t += escape(' '.join(s['text']))
            if s != self.sections[-1]:
                t += ' '
            if abstract:
                break
        t += '</text>'
        t += '</passage></document></collection>'
        return filter_non_printable(t)


    def text(self, abstract=False):
        """Return a plain-text string representing the document."""
        out = self.title + '.\n'
        out += self.title + '.\n'

        for author in self.authors:
            if author == 'Wikipedia':
                continue
            out += author + '.\n'

        out += self.book + '\n' + str(self.year) + '\n\n'

        if abstract:
            out += '\n'.join(self.get_abstract())
        else:
            for sect in self.sections:
                if 'heading' in sect and sect['heading']:
                    out += '\n\n' + sect['heading'] + '\n\n'
                out += '\n'.join(sect['text']) + '\n'

        for ref_id in sorted(list(self.references)):
            if not ref_id in self.corpus:
                continue
            out += '\n'
            for author in self.corpus[ref_id].authors:
                if author == 'Wikipedia':
                    continue
                out += author + '.\n'
            out += self.corpus[ref_id].title + '.\n'
        return filter_non_printable(unidecode(out))


    def bigrams(self, abstract=False, stop=StopLexicon()):
        def good_word(w):
            if '_' in w and not '#' in w:
                return False
            return any(c.isalpha() for c in w)

        def bigrams_from_sent(s):
            s = unidecode(s)
            ret = ''
            words = []
            for x in re.split(r'[^a-zA-Z0-9_#-]+', s):
                if len(x) > 0 and not x in stop and not x.lower() in stop \
                   and re.search('[a-zA-Z0-9]', x):
                    words.append(x)
            for w1, w2 in bigrams(words):
                if good_word(w1) and good_word(w2):
                    ret += w1.lower() + '_' + w2.lower() + '\n'
                if w1[0] == '#' and w1[-1] == '#' and good_word(w1):
                    ret += w1 + '\n'
            if words and words[-1][0] == '#' and words[-1][-1] == '#' and \
               good_word(words[-1]):
                ret += words[-1] + '\n'
            return ret

        out = bigrams_from_sent(self.title)
        out += bigrams_from_sent(self.title)

        for author in self.authors:
            if author == 'Wikipedia':
                continue
            out += bigrams_from_sent(author)

        out += bigrams_from_sent(self.book)

        if abstract:
            for sent in self.get_abstract():
                out += bigrams_from_sent(sent)
        else:
            for sect in self.sections:
                if 'heading' in sect and sect['heading']:
                    out += bigrams_from_sent(sect['heading'])
                for sent in sect['text']:
                    out += bigrams_from_sent(sent)

        for ref_id in sorted(list(self.references)):
            if not ref_id in self.corpus:
                continue
            for author in self.corpus[ref_id].authors:
                if author == 'Wikipedia':
                    continue
                out += bigrams_from_sent(author)
            out += bigrams_from_sent(self.corpus[ref_id].title)

        return out


def filter_non_printable(s):
    return ''.join([c for c in s if ord(c) > 31 or ord(c) == 9 or c == '\n'])

def title_case(s):
    for word in ['And', 'The', 'Of', 'From', 'To', 'In', 'For', 'A', 'An',
                 'On', 'Is', 'As', 'At']:
        s = re.sub('([A-Za-z]) ' + word + ' ', r'\1 ' + word.lower() + ' ', s)
    return s

def strtr(text, dic):
    """Replace the keys of dic with values of dic in text."""
    pat = '(%s)' % '|'.join(map(re.escape, dic.keys()))
    return re.sub(pat, lambda m:dic[m.group()], text)
