# Mallet
# Jonathan Gordon

import sys
import os
import tempfile
import random
import re
import subprocess
import multiprocessing as mp

from numpy import zeros
from itertools import combinations

from t.lx import StopLexicon


# Parameters

#PROCESSES = int(.5 * mp.cpu_count())
PROCESSES = 1

OPTIMIZE_INTERVAL = 10

###

class Mallet:
    def __init__(self, path, corpus=None, num_topics=200, bigrams=False,
                 iters=1000, prefix=None):
        self.path = path

        if prefix:
            self.prefix = prefix
        else:
            rand_prefix = hex(random.randint(0, 0xffffff))[2:] + '-'
            self.prefix = os.path.join(tempfile.gettempdir(), rand_prefix)

        self.dtfile = self.prefix + 'composition.txt'
        self.wtfile = self.prefix + 'word-topic-counts.txt'
        self.omfile = self.prefix + 'model.mallet'
        self.tkfile = self.prefix + 'keys.txt'
        self.wtkfile = self.prefix + 'weighted-keys.txt'
        self.statefile = self.prefix + 'state.gz'
        self.cofile = self.prefix + 'co-occur.txt'

        if os.path.exists(self.tkfile):
            num_topics = len(open(self.tkfile).readlines())
            print('Found model with', num_topics, 'topics.')

        self.topics = [[] for i in range(num_topics)]

        if not os.path.exists(self.wtfile) or not os.path.exists(self.dtfile):
            self.read(corpus, bigrams)
            self.train(num_topics, iters)
        self.load_wt()
        self.load_dt()


    def read(self, corpus, bigrams):
        stop = StopLexicon()

        cmd = [self.path, 'import-dir',
               '--input', corpus,
               '--output', self.prefix + 'corpus.mallet',
               '--remove-stopwords',
               '--extra-stopwords', stop.file,
               '--token-regex', '[^\\s]+']

        if bigrams:
            cmd += ['--keep-sequence-bigrams', '--gram-sizes 2']
        else:
            cmd += ['--keep-sequence']

        if subprocess.call(cmd) != 0:
            sys.stderr.write('Mallet import-dir failed.\n')
            sys.exit(1)


    def train(self, num_topics, iters):
        cmd = [self.path, 'train-topics',
               '--input', self.prefix + 'corpus.mallet',
               '--num-topics', str(num_topics),
               '--num-iterations', str(iters),
               '--optimize-interval', str(OPTIMIZE_INTERVAL),
               '--num-threads', str(PROCESSES),
               '--output-doc-topics', self.dtfile,
               '--word-topic-counts-file', self.wtfile,
               '--output-model', self.omfile,
               '--output-topic-keys', self.tkfile,
               '--output-state', self.statefile]

        if subprocess.call(cmd) != 0:
            sys.stderr.write('Mallet train-topics failed.\n')
            sys.exit(1)


    def load_wt(self):
        print('Loading word-topic file.')
        for line in open(self.wtfile):
            tokens = line.strip().split()
            word = tokens[1]
            for c in tokens[2:]:
                topic, count = c.split(':')
                self.topics[int(topic)].append((word, float(count)))

        with open(self.wtkfile, 'w') as out:
            for topic in range(len(self.topics)):
                out.write('\t'.join([str(topic)] +
                                    [str(y) + '\t' + str(z) for (y, z) in
                                     sorted(self.topics[topic], key=lambda x:
                                            x[1], reverse=True)][:60]) + '\n')


    def load_dt(self):
        print('Loading document-topic composition file.')

        num_topics = len(self.topics)
        self.topic_doc = [[] for i in range(num_topics)]
        self.co_occur = zeros((num_topics, num_topics), int)

        # We need a cut-off for a topic to count as non-trivially occurring
        # in a document, and this needs to vary depending on the number of
        # topics. Based on experiments with 20 and 200 topic models, I chose
        # the thresholds (20, 0.3) and (200, 0.1) and fit the line
        #    y = -1/900*x + 290/900
        # with a min of 0.01. This is a preliminary measure and should be
        # adjusted for other corpora.
        thresh = max((290.0 - num_topics)/900.0, 0.01)

        for line in open(self.dtfile):
            row = line.split('\t')
            if row[0][0] == '#':
                continue
            if len(row) < 2:
                print('Error with composition row', row, file=sys.stderr)
                continue
            m = re.search('([^/]+)\.(xml|txt)$', row[1])
            if not m:
                continue
            base = m.group(1)

            topics = [(int(a), float(b)) for (a, b) in
                      zip(row[2::2], row[3::2])]

            # Read into document topic breakdown information.
            for topic_id, percent in topics:
                self.topic_doc[topic_id].append((base, percent))

            # Read into co-occurrence matrix.
            filt_topics = [(a, b) for (a, b) in topics if b > thresh]
            for topic_pair in combinations(filt_topics, 2):
                i1 = topic_pair[0][0]
                i2 = topic_pair[1][0]
                # Symmetric matrix.
                self.co_occur[i1][i2] += 1
                self.co_occur[i2][i1] += 1

        with open(self.cofile, 'w') as out:
            for row in self.co_occur:
                for c in row:
                    out.write('%s ' % (c))
                out.write('\n')
