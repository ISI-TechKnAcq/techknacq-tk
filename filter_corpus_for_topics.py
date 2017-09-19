#!/usr/bin/env python3

# Topic Filtering Script
# Gully Burns

import os
import click
import operator
from numpy.linalg import norm
import numpy as np
import math

from mallet import Mallet
from techknacq.corpus import Corpus
from techknacq.conceptgraph import ConceptGraph

from tqdm import tqdm

def topic_signature_html(m, t_tuple, n_words, global_min=None, global_max=None):
    t_id = t_tuple[0]
    t_percent = t_tuple[1]

    def invert_hex(hex_number):
        inverse = hex(abs(int(hex_number, 16) - 255))[2:]
        # If the number is a single digit add a preceding zero
        if len(inverse) == 1:
            inverse = '0' + inverse
        return inverse

    def float_to_greyscale(f):
        val = '%x' % int(f * 255)
        val = invert_hex(val)
        return '#%s%s%s' % (val, val, val)

    word_weights = sorted(
        m.topics[t_id].items(), key=operator.itemgetter(1), reverse=True
    )[:n_words]

    vals = [x[1] for x in word_weights]
    val_max = max(vals)
    val_min = math.sqrt(min(vals) / 2)
    val_diff = float(val_max - val_min)
    if global_min and global_max:
        global_diff = float(global_max - global_min)

    t_percent_2sf = '%s' % float('%.2g' % t_percent)

    ret = '<emph><font>&#x25A0; </font>#' + str(t_id) + ' (' + t_percent_2sf + '): </emph>'

    for (y, z) in sorted(word_weights, key=lambda x: x[1],
                         reverse=True):

        p = float(z - val_min) / val_diff

        if global_min and global_max:
            q = float(z - global_min) / global_diff
        else:
            q = p

        ret += '<span style="color:%s" title="%s%% relevant">%s</span>\n' % (
            float_to_greyscale(p), int(q * 100), y.replace('_', '&nbsp;'))

    return ret

def document_signature_html(corpus, doc_id, DT, m, doc_list, n_topics, n_words):
    doc_count = DT.shape[0]
    top_topics = sorted(
        enumerate(DT[doc_id]), reverse=True, key=operator.itemgetter(1)
    )[:n_topics]

    doc = corpus[doc_list[doc_id]]
    html_signature = '<p><b>' + doc.title + '</b></br>'
    html_signature += '<i>' + ', '.join(doc.authors) + '</i>'
    # if(doc.url):
    #    html_signature += ' [<a href="'+doc.url+'">Link</a>]'
    html_signature += '</br>'
    html_signature += '</br>'.join([topic_signature_html(m, top_topics[i], n_words) for i in range(n_topics)])
    html_signature += '</p>'

    return html_signature

@click.command()
@click.argument('topicmodel_dir', type=click.STRING)
@click.argument('corpus_dir', type=click.Path(exists=True))
@click.argument('file_of_topics_to_remove', type=click.Path(exists=True))
@click.argument('n_topics_to_remove', type=click.INT)
@click.argument('cleaned_corpus', type=click.Path(exists=False))
def main(topicmodel_dir, corpus_dir, file_of_topics_to_remove, n_topics_to_remove, cleaned_corpus):

    MALLET_PATH = '/usr/local/bin/mallet'

    cg = ConceptGraph()
    corpus = Corpus(corpus_dir)
    cg.add_docs(corpus)
    m = Mallet(MALLET_PATH, topicmodel_dir, prefix=topicmodel_dir)

    td = []
    doc_list = [d_tuple[0] for d_tuple in m.topic_doc[0]]

    if os.path.exists(cleaned_corpus) is False:
        os.mkdir(cleaned_corpus)

    with open(file_of_topics_to_remove) as f:
        topics_to_remove = [int(l.strip()) for l in f.readlines()]

    for (t, d_in_t_list) in enumerate(m.topic_doc):
        topic_counts = []
        topic_weights = []
        for (d, d_tuple) in enumerate(d_in_t_list):
            topic_counts.append(d_tuple[1])
        td.append(topic_counts)

    TD_raw = np.asarray(td)
    DT_raw = TD_raw.transpose()

    n_docs = DT_raw.shape[0]
    n_topics = DT_raw.shape[1]

    L1_norm = norm(DT_raw, axis=1, ord=1)
    DT = DT_raw / L1_norm.reshape(n_docs, 1)

    doc_count = DT.shape[0]
    doc_urls = [corpus[doc_list[i]].url for i in range(doc_count)]

    docs_to_remove = []
    removed_docs_file = open(cleaned_corpus + "/00_removed.html", 'w')
    kept_docs_file = open(cleaned_corpus + "/01_kept.html", 'w')
    for i in tqdm(range(n_docs)):

        doc = corpus[doc_list[i]]
        top_topic_tuples = sorted(
            enumerate(DT[i]), reverse=True, key=operator.itemgetter(1)
        )[:n_topics_to_remove]
        top_topics = [tup[0] for tup in top_topic_tuples]

        keep_this_doc = True
        for j in top_topics:
            if j in topics_to_remove:
                docs_to_remove.append(i)
                removed_docs_file.write("<hr><h3>"+doc.id+"</h3>")
                removed_docs_file.write(document_signature_html(corpus, i, DT, m, doc_list, 5, 10))
                keep_this_doc = False
                break

        if keep_this_doc:
            json_text = doc.json()
            kept_docs_file.write("<hr><h3>" + doc.id + "</h3>")
            kept_docs_file.write(document_signature_html(corpus, i, DT, m, doc_list, 5, 10))
            with open(cleaned_corpus + "/" + doc.id + '.json', 'w') as f:
                f.write(json_text)

    removed_docs_file.close()
    kept_docs_file.close()

if __name__ == '__main__':
    main()
