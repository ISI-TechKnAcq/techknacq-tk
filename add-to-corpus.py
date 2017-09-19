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

@click.command()
@click.argument('corpusdir', type=click.Path(exists=True))
@click.argument('out-path', type=click.Path())
def main(corpusdir, out_path):

    rand_prefix = hex(random.randint(0, 0xffffff))[2:]
    prefix = os.path.join(out_path, rand_prefix)

    if os.path.exists(out_path) is False:
        os.makedirs(out_path)

    corpus = Corpus(corpusdir)

    corpus.export(out_path)

if __name__ == '__main__':
    main()
