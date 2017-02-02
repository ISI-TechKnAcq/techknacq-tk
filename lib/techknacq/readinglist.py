# TechKnAcq: Reading List
# Jonathan Gordon

from collections import defaultdict
from nltk.stem.lancaster import LancasterStemmer

from techknacq.conceptgraph import ConceptGraph


# Parameters

THRESHOLD = .5
MAX_MATCHES = 6
MAX_DEPTH = 4

# User model constants
# The values are for interfacing with techknacq-server.

BEGINNER = 5
INTERMEDIATE = 4
ADVANCED = 3


class ReadingList:
    def __init__(self, cg, query, user_model=None, docs=True):
        self.cg = cg

        self.query = ' '.join(query).lower().split()

        self.user_model = user_model
        if self.user_model is None:
            self.user_model = {}
            for c in cg.concepts():
                self.user_model[c] = BEGINNER

        self.stemmer = LancasterStemmer()
        self.query_words = [(x, self.stemmer.stem(x))
                            for x in self.query]

        self.covered_concepts = set()
        self.covered_documents = set()
        self.covered_titles = set()
        self.relevance = {c: self.score_match(c) for c in cg.concepts()}
        self.rl = []

        self.docs = docs

        for c, score in sorted(self.relevance.items(), key=lambda x: x[1],
                               reverse=True)[:MAX_MATCHES]:
            entry = self.traverse(c, score)
            if entry:
                self.rl.append(entry)
                break


    def best_docs(self, c, roles=None):
        """Return an ordered list of the best documents for the topic
        given an ordered list of preferred pedagogical roles."""

        if roles is None:
            roles = ['reference', 'survey', 'tutorial', 'resource',
                     'empirical', 'manual']

        # 1. Find the 20 most relevant documents for the topic, and expand
        #    with any additional documents whose relevance is > 0.8.

        docs = self.cg.topic_docs(c)

        # 2. Stable sort documents by pedagogical role preference:
        #    ped_score = 1.0 * role1 + 0.85 * role2 + 0.7 * role3 +
        #                0.55 * role4 + 0.4 * role5 + 0.25 * role4

        def ped_role_score(doc, role_order):
            doc_roles = self.cg.g.node[doc]['roles']
            score = 0.0
            for i, role in enumerate(role_order):
                score += (1.0 - i*.15) * doc_roles.get(role, 0)
            return score

        docs.sort(key=lambda x: ped_role_score(x[0], roles), reverse=True)


        return docs


    def traverse(self, c, score, depth=1):
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
        # so we know which documents we want to include at this level.
        for dep, dep_weight in sorted(self.cg.topic_deps(c),
                                      key=lambda x: x[1],
                                      reverse=True)[:50]:
            dep_discount = 1
            if self.user_model[c] == INTERMEDIATE:
                dep_discount = 2
            elif self.user_model[c] == ADVANCED:
                dep_discount = 10
            dep_entry = self.traverse(dep, score * dep_weight/dep_discount +
                                      self.relevance[dep], depth+1)
            if dep_entry:
                entry['subconcepts'].append(dep_entry)
            if len(entry['subconcepts']) >= MAX_MATCHES:
                break

        if not self.docs:
            return entry

        #
        # Documents to print before any dependencies:
        #

        doc1_to_print = 4 - depth
        if entry['subconcepts']:
            doc1_to_print -= 1
        doc1_to_print = max(doc1_to_print, 1)

        if self.user_model[c] != ADVANCED or entry['subconcepts']:
            sorted_docs = self.best_docs(c, ['survey', 'reference',
                                             'tutorial', 'resource',
                                             'manual', 'empirical'])
            for doc_id, doc_weight in sorted_docs:
                if doc_id in self.covered_documents or \
                   self.cg.g.node[doc_id]['title'] in self.covered_titles:
                    continue

                entry['documents1'].append(self.doc_entry(doc_id, doc_weight))
                self.covered_documents.add(doc_id)
                self.covered_titles.add(self.cg.g.node[doc_id]['title'])
                if len(entry['documents1']) == doc1_to_print:
                    break

        #
        # Documents to print after any dependencies:
        #

        doc2_to_print = 4 - depth
        if self.user_model[c] == BEGINNER:
            doc2_to_print -= 1
        if entry['subconcepts'] or self.user_model[c] == ADVANCED:
            doc2_to_print = max(doc2_to_print, 1)
        else:
            doc2_to_print = max(doc2_to_print, 0)

        if entry['subconcepts'] or depth == 1 or \
           self.user_model[c] == ADVANCED:
            sorted_docs = self.best_docs(c, ['empirical', 'tutorial',
                                             'resource', 'manual', 'survey',
                                             'reference'])
            for doc_id, doc_weight in sorted_docs:
                if doc_id in self.covered_documents or \
                   self.cg.g.node[doc_id]['title'] in self.covered_titles:
                    continue

                entry['documents2'].append(self.doc_entry(doc_id, doc_weight))
                self.covered_documents.add(doc_id)
                self.covered_titles.add(self.cg.g.node[doc_id]['title'])
                if len(entry['documents2']) == doc2_to_print:
                    break

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

    def print(self, rl=None, depth=1, format='text'):
        if rl is None:
            rl = self.rl

        if format == 'html':
            print('<dl>')

        for entry in rl:
            if format == 'html':
                print('<dt>%s &ndash; %.4f</dt>' % (entry['name'],
                                                    entry['score']))
                print('<dd>')
            else:
                print()
                print('  '*depth + '%s -- %.4f' % (entry['name'],
                                                   entry['score']))

            if format == 'html':
                print('<ul>')
            for doc in entry['documents1']:
                self.print_doc(doc['id'], depth, format=format)
            if format == 'html':
                print('</ul>')

            self.print(entry['subconcepts'], depth + 1, format=format)
            if entry['subconcepts']:
                print()

            if format == 'html':
                print('<ul>')
            for doc in entry['documents2']:
                self.print_doc(doc['id'], depth, format=format)
            if format == 'html':
                print('</ul>')
                print('</dd>')

        if format == 'html':
            print('</dl>')


    def print_doc(self, doc_id, depth, format='text'):
        if format == 'html':
            print('<li>')

        if format == 'html':
            pass
        else:
            print('  '*depth + '-', end=' ')

        if len(self.cg.g.node[doc_id]['authors']) > 3:
            print(self.cg.g.node[doc_id]['authors'][0] + ' et al.:')
        elif self.cg.g.node[doc_id]['authors']:
            print('; '.join(self.cg.g.node[doc_id]['authors']) + ':')
        else:
            print('  '*depth + '- Unknown:')

        if format == 'html':
            print('<a href="' + self.cg.g.node[doc_id]['url'] + '">')

        if len(self.cg.g.node[doc_id]['title']) > 70 - 2 * depth:
            print('  '*depth + '  ' +
                  self.cg.g.node[doc_id]['title'][:70 - 2 * depth].strip() +
                  '...')
        else:
            print('  '*depth + '  ' + self.cg.g.node[doc_id]['title'])

        if format == 'html':
            print('</a>')

        if format == 'html':
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
            # If the ngram in the concept model is a subset of the query,
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
