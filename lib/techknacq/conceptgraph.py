# TechKnAcq: Concept Graph
# Jonathan Gordon

import sys
import networkx as nx
import json
import uuid

# Parameters

WORDS_PER_CONCEPT = 100

###

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

        for doc in corpus:
            if len(doc.text().split()) < 300:
                continue
            self.g.add_node(doc.id, type='document', authors=doc.authors,
                            title=doc.title, book=doc.book, year=doc.year,
                            url=doc.url, abstract=doc.get_abstract(),
                            roles=doc.roles)
            for ref in doc.references:
                self.g.add_edge(doc.id, ref, type='cite')


    def add_concepts(self, model):
        """Add each topic from the topic model as a node in the
        ConceptGraph."""

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
                if not base in self.g:
                    continue
                self.g.add_edge('concept-' + str(topic), base,
                                type='topic', weight=percent)


    def add_dependencies(self, edges):
        for t1 in edges:
            for t2 in edges[t1]:
                self.g.add_edge('concept-' + t1, 'concept-' + t2,
                                type='dependency', weight=edges[t1][t2])


    def docs(self):
        """Return a list of all document IDs in the concept graph."""
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'document')


    def topic_docs(self, topic_id, min=20, max=400, threshold=0.8):
        """Return a sorted list of (document_id, weight) pairs for the
        documents that are most relevant to the specified topic_id,
        including the top `min` most relevant, and all others above
        `threshold`, up to `max` many."""

        edges = []
        for (_, doc, weight) in sorted(self.g.edges([topic_id], data='weight'),
                                       key=lambda x: x[2], reverse=True):
            if self.g.node[doc].get('type', '') == 'document':
                if len(edges) < min:
                    edges.append((doc, weight))
                elif weight >= threshold:
                    edges.append((doc, weight))
        return edges[:max]


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
                self.g.node[c['id']]['words'].sort(key=lambda x: x[1],
                                                   reverse=True)
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


    def export(self, file='concept-graph.json', concept_threshhold=0.2):
        """Export the concept graph as a JSON file."""

        def bad_topic(c):
            if self.g.node[c]['score'] < concept_threshhold:
                sys.stderr.write('Skipping topic %s due to score.\n' %
                                 (self.g.node[c]['name']))
                return True
            if 'Miscellany' in self.g.node[c]['name'] or \
              self.g.node[c]['name'] == 'Bad':
                #sys.stderr.write('Skipping topic %s due to name.\n' %
                #                 (self.g.node[c]['name']))
                return True
            return False

        j = {'id': self.id,
             'provenance': self.provenance,
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

        # Add document nodes and their features.
        for doc_id in self.docs():
            j_doc = {'id': doc_id,
                     'url': self.g.node[doc_id]['url'],
                     'title': self.g.node[doc_id]['title'],
                     'authors': [{#'id': x.lower().replace(' ', '_'),
                                  'fullName': x}
                                 for x in self.g.node[doc_id]['authors']],
                     'book': self.g.node[doc_id]['book'],
                     'year': self.g.node[doc_id]['year'],
                     'abstractText': self.g.node[doc_id]['abstract'],
                     'cites': [], #self.doc_cites(doc_id),
                     'roles': self.g.node[doc_id].get('roles', {})}
            j['corpus']['docs'].append(j_doc)

        for (t1, t2, data) in self.g.edges(data=True):
            if data.get('type', '') != 'dependency':
                continue
            if bad_topic(t1) or bad_topic(t2):
                continue
            j['edges'].append({'source': t1,
                               'target': t2,
                               'weight': data['weight'],
                               'type': 'dependency'})

        json.dump(j, open(file, 'w', encoding='utf8'), indent=1,
                  sort_keys=True, ensure_ascii=False)
