#!/usr/bin/env python3

# TechKnAcq: Concept Graph
# Jonathan Gordon

#
# This script runs MALLET on a document corpus to generate the needed output files for constructing a
# Concept Graph.
#

import sys
import os
import tempfile
import glob
import random
import subprocess
import click
import re

from collections import defaultdict

from mallet import Mallet
from techknacq.corpus import Corpus
from techknacq.conceptgraph import ConceptGraph

# Parameters

MALLET_PATH = '/usr/local/bin/mallet'

LDA_TOPICS = 300
LDA_ITERATIONS = 200

@click.command()
@click.argument('corpusdir', type=click.Path(exists=True))
@click.argument('out-path', type=click.Path())
@click.argument('num-topics', default=LDA_TOPICS)
@click.argument('num-iterations', default=LDA_ITERATIONS)
def main(corpusdir, out_path, num_topics, num_iterations):

    rand_prefix = hex(random.randint(0, 0xffffff))[2:]
    prefix = os.path.join(out_path, rand_prefix)

    if os.path.exists(out_path) is False:
        os.makedirs(out_path)

    cg = ConceptGraph()

    corpus = Corpus(corpusdir)
    # corpus.fix_text()

    cg.add_docs(corpus)

    print('Generating topic model.')
    mallet_corpus = prefix + '/corpus'
    os.makedirs(mallet_corpus)
    corpus.export(mallet_corpus, abstract=False, form='text')
    model = Mallet(MALLET_PATH, mallet_corpus, prefix=prefix, num_topics=num_topics,
                   iters=num_iterations, bigrams=False)

    cg.add_concepts(model)

    cg.export(prefix + '/cg.json',
              provenance='none'+' '+str(0))
    print('Concept graph:', prefix + 'cg.json')

if __name__ == '__main__':
    main()
