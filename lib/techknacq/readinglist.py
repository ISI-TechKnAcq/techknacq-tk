# TechKnAcq: Reading List
# Jonathan Gordon

import math

from collections import defaultdict
from nltk.tokenize import word_tokenize
from nltk.stem.lancaster import LancasterStemmer


# Parameters

THRESHOLD = .005
MAX_MATCHES = 6
MAX_DEPTH = 4
BASE_DOC_NUM = 8

# User model constants
# The values are for interfacing with techknacq-server.

BEGINNER = 5
INTERMEDIATE = 4
ADVANCED = 3

DEFAULT_DOC_PREFS = [
    'reference', 'survey', 'tutorial', 'resource', 'empirical', 'manual',
    'other'
]

INTRO_DOC_PREFS = [
    'survey', 'reference', 'tutorial', 'resource', 'manual', 'empirical',
    'other'
]

ADVANCED_DOC_PREFS = [
    'empirical', 'tutorial', 'resource', 'manual', 'survey', 'reference',
    'other'
]
#kieubinh analyzes code
class ReadingList:

    #input: concept graph (json format), query (string)
    #output: a list of ACL papers
    def __init__(self, cg, query, user_model=None, docs=True):
        self.cg = cg
        #tokenize of query by ' ' or '-' and lower this
        self.query = word_tokenize(' '.join(query).replace('-', ' ').lower())

        #default user model -> beginer
        self.user_model = user_model
        if self.user_model is None:
            self.user_model = {}
            for c in cg.concepts():
                self.user_model[c] = BEGINNER

        #stemmer query words
        self.stemmer = LancasterStemmer()
        self.query_words = [(x, self.stemmer.stem(x))
                            for x in self.query]

        self.covered_concepts = set()
        self.covered_documents = set()
        self.covered_titles = set()
        #score match?
        self.relevance = {c: self.score_match(c) for c in cg.concepts()}
        self.rl = []

        self.docs = docs

        for c, score in sorted(self.relevance.items(), key=lambda x: x[1],
                               reverse=True)[:MAX_MATCHES]:
            #each concept -> depth-first traveral to find
            print("matched concept "+c+" with score "+str(score))
            entry = self.traverse(c, score)
            if entry:
                self.rl.append(entry)
                break


    def best_docs(self, c, roles=None):
        """Return an ordered list of the best documents for the topic
        given an ordered list of preferred pedagogical roles."""

        if roles is None:
            roles = DEFAULT_DOC_PREFS

        # 1. Find the most relevant documents for the topic.

        docs = self.cg.topic_docs(c)

        print("most relevant documents for the topic "+c+" -> size of docs "+str(len(docs)))

        # 2. Stable sort documents by pedagogical role preference:
        #    ped_score = 1.0 * role1 + 0.85 * role2 + 0.7 * role3 +
        #                0.55 * role4 + 0.4 * role5 + 0.25 * role4

        def ped_role_score(doc, role_order):
            doc_roles = self.cg.g.node[doc]['roles']
            score = 0.0
            for i, role in enumerate(role_order):
                score += (1.0 - i*.15) * doc_roles.get(role, 0)
            if self.cg.g.node[doc].get('length', 0) == 0:
                return score
            return score * math.log(self.cg.g.node[doc]['length'])

        docs.sort(key=lambda x: ped_role_score(x[0], roles), reverse=True)

        return docs


    def traverse(self, c, score, depth=1, match_num=1):
        if score < THRESHOLD or c in self.covered_concepts:
            return

        if depth == MAX_DEPTH:
            return

        self.covered_concepts.add(c)

        entry = {'id': c,
                 'name': self.cg.name(c),
                 'score': score,
                 'documents1': [],
                 'subconcepts': [],
                 'documents2': []}

        # First compute any dependencies we'll include in the reading list
        # so we know which -- and how many -- documents we want to include
        # at this level.
        for dep, dep_weight in sorted(self.cg.topic_deps(c),
                                      key=lambda x: x[1], reverse=True)[:50]:
            dep_discount = 1
            if self.user_model[c] == INTERMEDIATE:
                dep_discount = 2
            elif self.user_model[c] == ADVANCED:
                dep_discount = 10
            dep_entry = self.traverse(dep, score * dep_weight/dep_discount +
                                      self.relevance[dep], depth + 1)
            if dep_entry:
                entry['subconcepts'].append(dep_entry)
            if len(entry['subconcepts']) >= MAX_MATCHES:
                break

        if not self.docs:
            return entry

        includes_dep = 1 if entry['subconcepts'] else 0

        num_docs = max(BASE_DOC_NUM - 2*depth - includes_dep, 1)

        if self.user_model[c] == BEGINNER:
            num_intro_docs = round(.75 * num_docs)
            num_advanced_docs = round(.25 * num_docs)
        elif self.user_model[c] == INTERMEDIATE:
            num_intro_docs = round(.5 * num_docs)
            num_advanced_docs = round(.5 * num_docs)
        elif self.user_model[c] == ADVANCED:
            num_intro_docs = round(.25 * num_docs)
            num_advanced_docs = round(.75 * num_docs)

        intro_docs = self.best_docs(c, INTRO_DOC_PREFS)
        advanced_docs = self.best_docs(c, ADVANCED_DOC_PREFS)


        #
        # Documents to print before any dependencies:
        #

        for doc_id, doc_weight in intro_docs:
            if num_intro_docs == 0:
                break
            if doc_id in self.covered_documents or \
               self.cg.g.node[doc_id]['title'] in self.covered_titles:
                continue
            entry['documents1'].append(self.doc_entry(doc_id, doc_weight))
            self.covered_documents.add(doc_id)
            self.covered_titles.add(self.cg.g.node[doc_id]['title'])
            num_intro_docs -= 1
            break


        #
        # Documents to print after any dependencies:
        #

        for doc_id, doc_weight in intro_docs:
            if num_intro_docs == 0:
                break
            if doc_id in self.covered_documents or \
               self.cg.g.node[doc_id]['title'] in self.covered_titles:
                continue
            entry['documents2'].append(self.doc_entry(doc_id, doc_weight))
            self.covered_documents.add(doc_id)
            self.covered_titles.add(self.cg.g.node[doc_id]['title'])
            num_intro_docs -= 1

        for doc_id, doc_weight in advanced_docs:
            if num_advanced_docs == 0:
                break
            if doc_id in self.covered_documents or \
               self.cg.g.node[doc_id]['title'] in self.covered_titles:
                continue
            entry['documents2'].append(self.doc_entry(doc_id, doc_weight))
            self.covered_documents.add(doc_id)
            self.covered_titles.add(self.cg.g.node[doc_id]['title'])
            num_advanced_docs -= 1

        return entry


    def doc_entry(self, doc_id, doc_weight):
        """Return the reading list entry for the specified document, which
        was selected with the specified weight."""
        return {'id': doc_id,
                'score': doc_weight,
                'type': 'unknown',
                'title': self.cg.g.node[doc_id]['title'],
                'authors': self.cg.g.node[doc_id]['authors'],
                'book': self.cg.g.node[doc_id]['book'],
                'year': self.cg.g.node[doc_id]['year'],
                'url': self.cg.g.node[doc_id]['url'],
                'abstract': self.cg.g.node[doc_id]['abstract']}

    def all_concepts(self, l=None):
        if l is None:
            l = self.rl
        for concept in l:
            yield concept
            yield from self.all_concepts(concept['subconcepts'])

    def print(self, rl=None, depth=1, form='text'):
        if rl is None:
            rl = self.rl

        if form == 'html':
            print('<dl>')

        for entry in rl:
            if form == 'html':
                print('<dt>%s &ndash; %.4f</dt>' % (entry['name'],
                                                    entry['score']))
                print('<dd>')
            elif form == 'text':
                print()
                print('  '*depth + '%s -- %.4f' % (entry['name'],
                                                   entry['score']))

            if form == 'html':
                print('<ul>')
            for doc in entry['documents1']:
                self.print_doc(doc['id'], depth, form=form)
            if form == 'html':
                print('</ul>')

            self.print(entry['subconcepts'], depth + 1, form=form)
            if entry['subconcepts'] and form == 'text':
                print()

            if form == 'html':
                print('<ul>')
            for doc in entry['documents2']:
                self.print_doc(doc['id'], depth, form=form)
            if form == 'html':
                print('</ul>')
                print('</dd>')

        if form == 'html':
            print('</dl>')


    def print_doc(self, doc_id, depth, form='text'):
        if form == 'html':
            print('<li>')

        if form == 'html':
            pass
        elif form == 'text':
            print('  '*depth + '-', end=' ')

        authors = ''
        if len(self.cg.g.node[doc_id]['authors']) > 3:
            authors = self.cg.g.node[doc_id]['authors'][0] + ' et al.'
        elif self.cg.g.node[doc_id]['authors']:
            authors = '; '.join(self.cg.g.node[doc_id]['authors'])
        else:
            authors = 'Unknown'

        title = ''
        if form == 'html':
            title = '<a href="' + self.cg.g.node[doc_id]['url'] + '">'

        if len(self.cg.g.node[doc_id]['title']) > 70 - 2 * depth:
            title += '  '*depth + '  ' + \
                  self.cg.g.node[doc_id]['title'][:70 - 2 * depth].strip() + \
                  '...'
        else:
            title += '  '*depth + '  ' + self.cg.g.node[doc_id]['title']

        if form == 'html':
            title += '</a>'

        if form == 'tsv':
            print(doc_id + '\t' + title + '\t' + authors + '\t' +
                  str(self.cg.g.node[doc_id]['year']) + '\t' +
                  self.cg.g.node[doc_id]['book'] + '\t' +
                  self.cg.g.node[doc_id]['url'])
        else:
            print(authors + ':')
            print(title)

        if form == 'html':
            print('</li>')


    def score_match(self, c):
        """Score the relevance of a concept to a query based on lexical
        overlap."""

        concept_words = [([(x, self.stemmer.stem(x)) for x in
                           ngram.split('_')],
                          ngram_count/self.cg.g.node[c]['mentions'])
                         for ngram, ngram_count in self.cg.g.node[c]['words']]

        matches = defaultdict(float)
        bonus = 0.0

        for ngram, weight in concept_words:
            for query_word, query_lemma in self.query_words:
                if query_word in [x[0] for x in ngram]:
                    matches[query_word] += weight
                elif set([query_word, query_lemma]) & set(ngram[0] + ngram[1]):
                    matches[query_word] += 0.75 * weight
            # If the n-gram in the concept model is a subset of the query,
            # e.g., 'hidden markov' in 'hidden markov model', apply a bonus.
            if ' '.join([x[0] for x in ngram]) in \
               ' '.join([x[0] for x in self.query_words]):
                bonus += weight

        # If the query is part of the name a human annotator gave to the
        # topic, give it a bonus.
        if ' '.join([x[0] for x in self.query_words]) in \
           self.cg.g.node[c].get('name', '').lower():
            bonus += .75
        else:
            lemma_overlap = \
                set([x[1] for x in self.query_words]) & \
                set([self.stemmer.stem(x) for x in
                     self.cg.g.node[c].get('name', '').lower().split()])
            # Partial credit
            bonus += .5 * len(lemma_overlap)

        return sum(matches.values()) * len(matches)/len(self.query_words) + \
               bonus
