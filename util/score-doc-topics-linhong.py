#!/usr/bin/env python3

# See equations on https://github.com/ISI-TechknAcq/techknacq-main/wiki/Computing%20Relevance%20of%20Documents%20to%20Topics
# Jonathan Gordon, 2016-07-07

import sys
import os
import math

from pathlib import Path

from mallet import Mallet

MALLET_PATH = 'ext/mallet/bin/mallet'


def alt_dt(model, corpus, fout):
    """Produce an alternative document-topic matrix."""

    print('Computing alternative document-topic composition matrix.')
    num_topics = len(model.topics)
    scores = [{} for i in range(num_topics)]

    for topic in range(num_topics):
        fout.write('%d' % (topic))
        if topic % 50 == 0:
            print('Topic', topic)
        topic_sum = sum(model.topics[topic].values())
        topic_prob = model.params[topic]
        for doc in corpus:
            term1 = 0.0
            term2 = 0.0
            term3 = 0.0
            for word in corpus[doc]:
                try:
                    term1 += math.log(model.topics[topic].get(word, 0.0)/topic_sum)
                    term2 += math.log(topic_prob)
                except:
                    continue
            term3 = math.log(topic_prob)
            scores[topic][doc] = term1 + term2 - term3
            scores[topic][doc] = math.exp(scores[topic][doc])
        for doc, weight in scores[topic].items():
            if weight != 0.0:
                fout.write('\t%s:%f' % (doc, weight))
        fout.write('\n')

    # Convert scores to topic_doc format.
    return [scores[i].items() for i in range(num_topics)]


if __name__ == '__main__':
    model = Mallet(MALLET_PATH, prefix=sys.argv[2])

    corpus = {}
    for doc in (str(f) for f in Path(sys.argv[1]).iterdir() if f.is_file()):
        doc_id = os.path.basename(doc).replace('.txt', '')
        corpus[doc_id] = open(doc).read().split()

    print('Read corpus of size', len(corpus))

    model = Mallet(MALLET_PATH, prefix=sys.argv[2])

    with open('alt-dt.txt', 'w') as fout:
        alt_dt(model, corpus, fout)
