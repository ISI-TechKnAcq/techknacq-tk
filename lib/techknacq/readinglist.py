# TechKnAcq: Reading List
# Jonathan Gordon

from nltk.stem import WordNetLemmatizer

from techknacq.conceptgraph import ConceptGraph


# Parameters

THRESHOLD = 0.002
MAX_MATCHES = 5
MAX_DEPTH = 5

# User model constants
# The values are for interfacing with techknacq-server.

BEGINNER = 5
INTERMEDIATE = 4
ADVANCED = 3


class ReadingList:
    def __init__(self, cg, query, user_model=None, docs=True):
        self.cg = cg

        self.query = set(query)

        self.user_model = user_model
        if self.user_model is None:
            self.user_model = {}
            for c in cg.concepts():
                self.user_model[c] = BEGINNER

        self.lemmatizer = WordNetLemmatizer()
        self.query_lemmas = set([self.lemmatizer.lemmatize(x)
                                 for x in self.query])

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
                                      key=lambda x:
                                      score*x[1] + self.relevance[x[0]],
                                      reverse=True)[:MAX_MATCHES]:
            dep_discount = 1
            if self.user_model[c] == INTERMEDIATE:
                dep_discount = 2
            elif self.user_model[c] == ADVANCED:
                dep_discount = 10
            dep_entry = self.traverse(dep, score*dep_weight/dep_discount +
                                      self.relevance[dep], depth+1)
            if dep_entry:
                entry['subconcepts'].append(dep_entry)

        if not self.docs:
            return entry

        #
        # Documents to print before any dependencies:
        #

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
                break

        #
        # Documents to print after any dependencies:
        #

        doc2_count = 0
        if entry['subconcepts'] or self.user_model[c] == ADVANCED:
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
                doc2_count += 1
                if self.user_model[c] != ADVANCED or doc2_count == 2:
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

        if len(self.cg.g.node[doc_id]['title']) > 70:
            print('  '*depth + '  ' + self.cg.g.node[doc_id]['title'][:70] +
                  '...')
        else:
            print('  '*depth + '  ' + self.cg.g.node[doc_id]['title'])

        if format == 'html':
            print('</a>')

        if format == 'html':
            print('</li>')


    def score_match(self, c, fuzzy=False):
        """Score the relevance of a concept to a query based on lexical
        overlap. If `fuzzy` is False, use strict matching rather than
        lemmatizing."""

        mentions = self.cg.g.node[c]['mentions']
        score = 0.0
        for word, weight in self.cg.g.node[c]['words']:
            # Each match is scored as the % of distinct words the query
            # and the feature share * weight of the feature in the topic, e.g.,
            # - Query: 'knowledge'
            #   Topic feature: ('knowledge_base', 323)
            #   Return: (1/2) * (323 / topic_mentions)
            # - Query: 'knowledge base generation'
            #   Topic feature: ('data base', 323)
            #   Return: (1/4) * (323 / topic_mentions)
            words = set(word.split('_'))
            all_words = self.query | words
            common = self.query & words
            score += (len(common)/len(all_words)) * (weight/mentions)
            if fuzzy:
                words_lemmas = set([self.lemmatizer.lemmatize(x)
                                    for x in words])
                all_words = self.query_lemmas | words_lemmas
                common = self.query_lemmas & words_lemmas
                score += .75 * (len(common)/len(all_words)) * (weight/mentions)
        return score
