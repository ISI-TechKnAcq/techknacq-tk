#!/usr/bin/env python3

import sys
from pathlib import Path

from mallet import Mallet

MALLET_PATH = 'ext/mallet/bin/mallet'


def alt_dt(model, corpus, fout):
    """Produce an alternative document-topic matrix giving the importance of
    a document to the topic rather than vice versa, which we compute by
    summing (and then normalizing) the weight of each document word in the
    topic."""

    print('Computing alternative document-topic composition matrix.')
    num_topics = len(model.topics)
    scores = [{} for i in range(num_topics)]

    for topic in range(num_topics):
        fout.write('%d' % (topic))
        if topic % 50 == 0:
            print('Topic', topic)
        max_score = 0.0
        for doc in corpus:
            scores[topic][doc] = 0.0
            for word in corpus[doc]:
                scores[topic][doc] += model.topics[topic].get(word, 0.0)
            if scores[topic][doc] > max_score:
                max_score = scores[topic][doc]
        if max_score == 0.0:
            continue
        for doc in corpus:
            scores[topic][doc] /= max_score

        for doc, weight in scores[topic].items():
            fout.write('\t%s:%f' % (doc, weight))
        fout.write('\n')

    # Convert scores to topic_doc format.
    return [scores[i].items() for i in range(num_topics)]


if __name__ == '__main__':
    model = Mallet(MALLET_PATH, prefix=sys.argv[2])

    corpus = {}
    for doc in (str(f) for f in Path(sys.argv[1]).iterdir() if f.is_file()):
        corpus[doc] = open(doc).read().split()

    model = Mallet(MALLET_PATH, prefix=sys.argv[2])

    with open('alt-dt.txt', 'w') as fout:
        alt_dt(model, corpus, fout)
