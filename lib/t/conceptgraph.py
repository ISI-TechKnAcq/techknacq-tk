# T: Concept Graph
# Jonathan Gordon

import networkx as nx

from t.corpus import GensimCorpus

# Parameters

WORDS_PER_CONCEPT = 100

###

# Considerations:
# - I should now be adding the links from concepts to documents and vice
#   versa, but these will then be mixed in with the concept-to-concept links
#   I'm going to add. I've specified the 'type' for the links I've added,
#   e.g., for document citations, but I want to be able to quickly find
#   the type of links I'm interested in. This is why I have 'docs' and
#   'concepts' sets to allow iterating over those, but what to do about
#   edges? I shouldn't duplicate this information.
# - Maybe it's sufficient to use the NX edges method, which can specify a
#   property of interest, though not filter on a value:
#      for (u,v,d) in FG.edges(data='weight'):

class ConceptGraph:
    def __init__(self):
        self.g = nx.DiGraph()


    def add_docs(self, corpus):
        """Add each document from the corpus as a node in the ConceptGraph
        and add edges for any citation information."""

        for doc in corpus.docs:
            self.g.add_node(doc.id, type='document', authors=doc.authors,
                            title=doc.title, book=doc.book, year=doc.year,
                            url=doc.url, abstract=doc.get_abstract())
            for ref in doc.references:
                self.g.add_edge(doc.id, ref, type='cite')


    def add_concepts(self, model):
        """Add each topic from the topic model as a node in the
        ConceptGraph."""

        for i in range(model.num_topics):
            concept_id = 'concept-' + str(i)
            self.g.add_node(concept_id, type='concept')
            self.g[concept_id]['words'] = []
            for weight, word in model.show_topic(i, WORDS_PER_CONCEPT):
                self.g[concept_id]['words'].append((word, weight))


    def docs(self):
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'document')


    def concepts(self):
        return (n for n in self.g if
                self.g.node[n].get('type', '') == 'concept')
