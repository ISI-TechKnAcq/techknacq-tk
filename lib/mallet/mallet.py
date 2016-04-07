# Mallet
# Jonathan Gordon

import sys
import os
import tempfile
import random
import re
import subprocess
import multiprocessing as mp

from t.lx import StopLexicon

# Parameters

PROCESSES = int(.5 * mp.cpu_count())

OPTIMIZE_INTERVAL = 10

###

class Mallet:
    def __init__(self, path, corpus, num_topics=200, bigrams=False,
                 iters=1000):
        self.path = path

        rand_prefix = hex(random.randint(0, 0xffffff))[2:] + '-'
        self.prefix = os.path.join(tempfile.gettempdir(), rand_prefix)

        self.dtfile = self.prefix + 'composition.txt'
        self.wtfile = self.prefix + 'word-topic-counts.txt'
        self.omfile = self.prefix + 'model.mallet'
        self.tkfile = self.prefix + 'keys.txt'
        self.statefile = self.prefix + 'state.gz'

        self.topics = [[] for i in range(num_topics)]

        self.read(corpus, bigrams)
        self.train(num_topics, iters)
        self.load_wt()


    def read(self, corpus, bigrams):
        stop = StopLexicon()

        cmd = [self.path, 'import-dir',
               '--input', corpus,
               '--output', self.prefix + 'corpus.mallet',
               '--remove-stopwords',
               '--extra-stopwords', stop.file,
               '--token-regex', '"[\p{L}\p{M}]+"']

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
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        prog = re.compile(b'\<([^\)]+)\>')
        while p.poll() is None:
            line = p.stderr.readline()
            try:
                i = float(prog.match(line).groups()[0])
                progress = int(100. * i/iters)
                if progress % 10 == 0:
                    print('LDA progress: {0}%.'.format(progress))
            except AttributeError:
                pass

    def load_wt(self):
        for line in open(self.wtfile):
            tokens = line.strip().split()
            word = tokens[1]
            for c in tokens[2:]:
                topic, count = c.split(':')
                self.topics[int(topic)].append((word, float(count)))
