# T: Concept Graph
# Jonathan Gordon

import networkx as nx
import json
import uuid

# Parameters

WORDS_PER_CONCEPT = 100

###

class ConceptGraph:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.provenance = 'TechKnAcq'
        self.type = '1.0'
        # We export lists of (concept) nodes and edges, but we internally
        # store everything as a NetworkX graph.
        self.g = nx.DiGraph()


    def add_docs(self, corpus):
        """Add each document from the corpus as a node in the ConceptGraph
        and add edges for any citation information."""

        for doc in corpus:
            self.g.add_node(doc.id, type='document', authors=doc.authors,
                            title=doc.title, book=doc.book, year=doc.year,
                            url=doc.url, abstract=doc.get_abstract())
            for ref in doc.references:
                self.g.add_edge(doc.id, ref, type='cite')


    def add_concepts(self, model):
        """Add each topic from the topic model as a node in the
        ConceptGraph."""

        # Add a concept node for each topic in the model.
        for i, topic in enumerate(model.topics):
            concept_id = 'concept-' + str(i)
            self.g.add_node(concept_id, type='concept')
            self.g.node[concept_id]['words'] = []
            for word, weight in sorted(topic, key=lambda x: x[1], reverse=True):
                self.g.node[concept_id]['words'].append((word, weight))

        # Link the concept nodes to documents.
        for topic_id in range(len(model.topic_doc)):
            for base, percent in model.topic_doc[topic_id]:
                if percent == 0.0:
                    continue
                self.g.add_edge('concept-' + str(topic_id), base, type='topic',
                                weight=percent)


    def add_dependencies(self, edges):
        for t1 in edges:
            for (t2, weight) in edges[t1]:
                self.g.add_edge(t1, t2, type='dependency', weight=weight)


    def docs(self):
        """Return a list of all document IDs in the concept graph."""
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'document')


    def topic_docs(self, topic_id):
        """Return a sorted list of (document_id, weight) pairs for the
        documents that are most relevant to the specified topic_id."""

        edges = []
        for (topic, doc, weight) in self.g.edges([topic_id], data='weight'):
            if self.g.node[doc].get('type', '') != 'document':
                continue
            edges.append((doc, weight))
        return sorted(edges, key=lambda x: x[1], reverse=True)


    def concepts(self):
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'concept')


    def export(self, file='concept-graph.json'):
        """Export the concept graph as a JSON file."""

        j = {'id': self.id,
             'provenance': self.provenance,
             'type': self.type,
             'nodes': [],
             'edges': [],
             'corpus': {'id': str(uuid.uuid4()),
                        'name': '', # XXX
                        'description': '',
                        'docs': []}}

        # Add concept nodes and their (topic model) features.
        for c in self.concepts():
            j_concept = {'id': c,
                         'name': '',
                         'mentionCount': 0,
                         'featureWeights': [],
                         'docWeights': []}

            for (word, weight) in self.g[c].get('words', []):
                j_concept['featureWeights'].append({'feature': word,
                                                    'count': int(weight)})
                j_concept['mentionCount'] += weight

            for (doc, weight) in self.topic_docs(c):
                j_concept['docWeights'].append({'document': doc,
                                                'weight': weight})
            j['nodes'].append(j_concept)

        for doc_id in self.docs():
            j_doc = {'id': doc_id,
                     'url': self.g.node[doc_id]['url'],
                     'title': self.g.node[doc_id]['title'],
                     'authors': [],
                     'book': self.g.node[doc_id]['book'],
                     'year': self.g.node[doc_id]['year'],
                     'abstractText': self.g.node[doc_id]['abstract']}
            j['corpus']['docs'].append(j_doc)
        # XXX: Add Doc['authors']

        for (t1, t2, data) in self.g.edges(data=True):
            if data.get('type', '') != 'dependency':
                continue
            j['edges'].append({'source': t1,
                               'target': t2,
                               'weight': data['weight'],
                               'type': 'dependency'})

        json.dump(j, open(file, 'w'), indent=2)
