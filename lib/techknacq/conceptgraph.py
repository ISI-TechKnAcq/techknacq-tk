# TechKnAcq: Concept Graph
# Jonathan Gordon

import sys
import networkx as nx
import json
import uuid

# Parameters

WORDS_PER_CONCEPT = 100


class ConceptGraph:
    def __init__(self, fname=None):
        self.id = str(uuid.uuid4())
        self.provenance = 'TechKnAcq'
        self.type = '1.0'
        # We export lists of (concept) nodes and edges, but we internally
        # store everything as a NetworkX graph.
        self.g = nx.DiGraph()

        if fname:
            self.load(fname)


    def add_docs(self, corpus):
        """Add each document from the corpus as a node in the ConceptGraph
        and add edges for any citation information."""

        print('Adding documents to concept graph.')

        for doc in corpus:
            doc_length = len(doc.text().split())
            if doc_length < 300:
                continue
            self.g.add_node(doc.id, type='document', authors=doc.authors,
                            title=doc.title, book=doc.book, year=doc.year,
                            url=doc.url, abstract=doc.get_abstract(),
                            length=doc_length, roles=doc.roles)
            for ref in doc.references:
                self.g.add_edge(doc.id, ref, type='cite')


    def add_concepts(self, model):
        """Add each topic from the topic model as a node in the
        ConceptGraph."""

        print('Adding concepts to concept graph.')

        # Add a concept node for each topic in the model.
        for topic in range(len(model.topics)):
            concept_id = 'concept-' + str(topic)
            self.g.add_node(concept_id, type='concept', words=[], mentions=0,
                            name=model.names[topic], score=model.scores[topic])
            for word, weight in model.topic_pairs(topic):
                self.g.node[concept_id]['words'].append((word, weight))
                self.g.node[concept_id]['mentions'] += weight

        # Link the concept nodes to documents.
        for topic in range(len(model.topic_doc)):
            for base, percent in model.topic_doc[topic]:
                if percent == 0.0:
                    continue
                if base not in self.g:
                    continue
                self.g.add_edge('concept-' + str(topic), base,
                                type='topic', weight=percent)


    def add_dependencies(self, edges):
        print('Adding dependencies to concept graph.')
        for t1 in edges:
            for t2 in edges[t1]:
                if edges[t1][t2] <= 0.0:
                    continue
                self.g.add_edge('concept-' + t1, 'concept-' + t2,
                                type='dependency', weight=edges[t1][t2])


    def docs(self):
        """Return a list of all document IDs in the concept graph."""
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'document')

    #return docs that cover the the topic with the number of docs <= budget - submodular
    def topic_coverage_docs(self, topic_id, budget):
        #G = null
        edges = []



        return edges

    #return at least 25 most relevant docs and at most 200 most relevant docs with relevant weights > 0.6
    def topic_docs(self, topic_id, min_docs=25, max_docs=200, threshold=0.6):
        """Return a sorted list of (document_id, weight) pairs for the
        documents that are most relevant to the specified topic_id,
        including the top `min_docs` most relevant, and all others above
        `threshold`, up to `max_docs` many."""

        edges = []
        for (_, doc, weight) in sorted(self.g.edges([topic_id], data='weight'),
                                       key=lambda x: x[2], reverse=True):
            if self.g.node[doc].get('type', '') == 'document':
                if len(edges) < min_docs:
                    edges.append((doc, weight))
                elif weight >= threshold:
                    edges.append((doc, weight))
                if len(edges) >= max_docs:
                    break
        return edges


    def topic_deps(self, topic_id):
        """Return a sorted list of (topic_id, weight) pairs for the
        topics that are most relevant to the specified topic_id."""

        edges = []
        for (_, t2, weight) in self.g.edges([topic_id], data='weight'):
            if self.g.edge[topic_id][t2]['type'] == 'dependency':
                edges.append((t2, weight))

        return sorted(edges, key=lambda x: x[1], reverse=True)


    def doc_topic_strength(self, doc_id, topic_id):
        """Return the strength of association between a specified document
        and topic."""
        return self.g.edge[topic_id][doc_id]['weight']


    def doc_cites(self, doc_id):
        """Return a list of the document IDs for the documents
        that are cited by the specified document."""

        edges = []
        for (_, d2) in self.g.edges([doc_id]):
            if self.g.edge[doc_id][d2]['type'] == 'cite':
                edges.append(d2)
        return edges


    def name(self, c):
        return self.g.node[c]['name']


    def concepts(self):
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'concept')


    def load(self, fname):
        j = json.load(open(fname))

        try:
            self.id = j['id']
            self.provenance = j['provenance']
            self.type = j['type']

            for c in j['nodes']:
                self.g.add_node(c['id'], type='concept', words=[])
                self.g.node[c['id']]['name'] = c['name']
                self.g.node[c['id']]['mentions'] = c['mentionCount']
                for f in c['featureWeights']:
                    self.g.node[c['id']]['words'].append((f['feature'],
                                                          f['count']))
                self.g.node[c['id']]['words'].sort(key=lambda x:
                                                   (-1.0 * x[1], x[0]))
                for doc_edge in c['docWeights']:
                    self.g.add_edge(c['id'], doc_edge['document'],
                                    weight=doc_edge['weight'],
                                    type='composition')

            for d in j['corpus']['docs']:
                self.g.add_node(d['id'], type='document',
                                authors=[x['fullName'] for x in d['authors']],
                                title=d['title'], book=d['book'],
                                year=d['year'], url=d['url'],
                                abstract=d['abstractText'],
                                length=d.get('length', 0),
                                roles=d.get('roles', {}))
                for cited in d.get('cites', []):
                    self.g.add_edge(d['id'], cited, type='cite')

            for e in j['edges']:
                self.g.add_edge(e['source'], e['target'], type=e['type'],
                                weight=e['weight'])


        except Exception as e:
            sys.stderr.write('Error importing concept graph %s.\n' % (fname))
            print(e, file=sys.stderr)
            sys.exit(1)


    def export(self, file='concept-graph.json', concept_threshold=0.2,
               provenance=''):
        """Export the concept graph as a JSON file."""

        def bad_topic(c):
            if 'score' in self.g.node[c] and \
               self.g.node[c]['score'] < concept_threshold:
                sys.stderr.write('Skipping topic %s due to score.\n' %
                                 (self.g.node[c]['name']))
                return True
            if 'Miscellany' in self.g.node[c]['name'] or \
               self.g.node[c]['name'] == 'Bad':
                return True
            return False

        j = {'id': self.id,
             'provenance': ' '.join([self.provenance, provenance]).strip(),
             'type': self.type,
             'nodes': [],
             'edges': [],
             'corpus': {'id': str(uuid.uuid4()),
                        'name': '',
                        'description': '',
                        'docs': []}}

        # Add concept nodes and their (topic model) features.
        for c in self.concepts():
            if bad_topic(c):
                continue

            j_concept = {'id': c,
                         'name': self.g.node[c]['name'],
                         'mentionCount': self.g.node[c]['mentions'],
                         'featureWeights': [],
                         'docWeights': []}

            for (word, weight) in self.g.node[c].get('words', [])[:40]:
                if weight < 1:
                    continue
                j_concept['featureWeights'].append({'feature': word,
                                                    'count': int(weight)})

            for (doc, weight) in self.topic_docs(c):
                j_concept['docWeights'].append({'document': doc,
                                                'weight': weight})
            j['nodes'].append(j_concept)

        j['nodes'].sort(key=lambda x: x['id'])

        # Add document nodes and their features.
        for doc_id in self.docs():
            j_doc = {'id': doc_id,
                     'url': self.g.node[doc_id]['url'],
                     'title': self.g.node[doc_id]['title'],
                     'authors': [{'fullName': x}
                                 for x in self.g.node[doc_id]['authors']],
                     'book': self.g.node[doc_id]['book'],
                     'year': self.g.node[doc_id]['year'],
                     'abstractText': self.g.node[doc_id]['abstract'],
                     'cites': [],  # self.doc_cites(doc_id),
                     'length': self.g.node[doc_id].get('length', 0),
                     'roles': self.g.node[doc_id].get('roles', {})}
            j['corpus']['docs'].append(j_doc)

        j['corpus']['docs'].sort(key=lambda x: x['id'])

        for (t1, t2, data) in self.g.edges(data=True):
            if data.get('type', '') != 'dependency':
                continue
            if bad_topic(t1) or bad_topic(t2):
                continue
            j['edges'].append({'source': t1,
                               'target': t2,
                               'weight': data['weight'],
                               'type': 'dependency'})
        j['edges'].sort(key=lambda x: x['source'] + x['target'])

        json.dump(j, open(file, 'w', encoding='utf8'), indent=1,
                  sort_keys=True, ensure_ascii=False)
