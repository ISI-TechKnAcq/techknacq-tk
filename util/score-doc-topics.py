#!/usr/bin/env python3

import os
from pathlib import Path
import click

from mallet import Mallet

MALLET_PATH = '../ext/mallet/bin/mallet'


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
            if len(corpus[doc]) == 0:
                continue
            scores[topic][doc] = 0.0
            for word in corpus[doc]:
                scores[topic][doc] += model.topics[topic].get(word, 0.0)
            scores[topic][doc] /= len(corpus[doc])
            if scores[topic][doc] > max_score:
                max_score = scores[topic][doc]
        if max_score == 0.0:
            continue
        for doc in corpus:
            scores[topic][doc] /= max_score

        for doc, weight in scores[topic].items():
            if weight != 0.0:
                fout.write('\t%s:%f' % (doc, weight))
        fout.write('\n')

    # Convert scores to topic_doc format.
    return [scores[i].items() for i in range(num_topics)]


@click.command()
@click.argument('text_corpus_dir', type=click.Path(exists=True))
@click.argument('topic_model_prefix')
def main(text_corpus_dir, topic_model_prefix):
    corpus = {}
    for doc in (str(f) for f in Path(text_corpus_dir).iterdir()
                if f.is_file()):
        doc_id = os.path.basename(doc).replace('.txt', '')
        if doc_id and doc_id != ' ':
            corpus[doc_id] = open(doc).read().split()

    print('Read corpus of size', len(corpus))

    model = Mallet(MALLET_PATH, prefix=topic_model_prefix)

    with open('alt-dt.txt', 'w') as fout:
        alt_dt(model, corpus, fout)


if __name__ == '__main__':
    main()
