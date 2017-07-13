#!/usr/bin/env python3

# TechKnAcq: Concept Graph
# Jonathan Gordon

import sys
import os
import tempfile
import glob
import random
import subprocess
import click
import json
import re
import tqdm
import math
import csv
from numpy import zeros
from itertools import combinations
import codecs

from collections import defaultdict

from mallet import Mallet
from techknacq.corpus import Corpus
from techknacq.conceptgraph import ConceptGraph
from collections import defaultdict


def read_composition(compfile):
    """Read the file giving the topic composition of each document, and
    generate a matrix of topic co-occurrence counts."""

    filecontents = compfile.readlines()
    num_topics = len(filecontents[0].split()) - 2

    topic_doc = []
    for i in range(num_topics):
        topic_doc.append([])

    co_occur = zeros((num_topics, num_topics), int)

    # We need a cut-off for a topic to count as non-trivially occurring
    # in a document, and this needs to vary depending on the number of
    # topics. Based on experiments with 20 and 200 topic models, I chose
    # the thresholds (20, 0.3) and (200, 0.1) and fit the line
    #    y = -1/900*x + 290/900
    # with a min of 0.01.
    thresh = max((290.0 - num_topics) / 900.0, 0.01)

    r = csv.reader(filecontents, delimiter='\t')
    for row in r:
        if row[0][0] == '#':
            continue
        m = re.search('([^/]+)\.(xml|txt)$', row[1])
        if not m:
            continue
        base = m.group(1)

        topics = row[2:]

        # Read into document topic breakdown information.
        for (topic_id, percent) in enumerate(topics):
            if float(percent) > thresh:
                topic_doc[topic_id].append((base, percent))

        # Read into co-occurrence matrix.
        filt_topics = [(a,b) for (a,b) in enumerate(topics) if float(b) > thresh]
        for topic_pair in combinations(filt_topics, 2):
            i1 = int(topic_pair[0][0])
            i2 = int(topic_pair[1][0])
            # Symmetric matrix.
            co_occur[i1][i2] += 1
            co_occur[i2][i1] += 1

    return (topic_doc, co_occur)

def read_weighted_keys(keyfile):
    r = csv.reader(keyfile, delimiter='\t')
    word_weights = []
    for row in r:
        topicnum = row[0]
        weighted_words = [(x, float(y)) for (x, y) in
                          zip(row[1::2], row[2::2])]
        word_weights.append(weighted_words)
    return word_weights

def read_keys(keyfile):
    names = []
    topics = []
    r = csv.reader(keyfile, delimiter='\t')
    for row in r:
        words = row[2].split()
        if len(words) > 5:
            names[int(row[0])] = ' '.join(words[:6])
        else:
            names[int(row[0])] = ' '.join(words)
        topics[int(row[0])] = row[2]
    return (names, topics)

def split_topic(topic_counts_path):
    topic_unigrams = defaultdict(set)
    topic_bigrams = defaultdict(set)
    topic_entities = defaultdict(set)

    for line in open(topic_counts_path):
        tokens = line.split()
        word = tokens[1]
        counts = tokens[2:]
        for c in counts:
            (topic, count) = c.split(':')
            if word.startswith('#') and word.endswith('#'):
                topic_entities[int(topic)].add((word, float(count)))
            elif word.count('_') >= 1:
                topic_bigrams[int(topic)].add((word, float(count)))
            else:
                topic_unigrams[int(topic)].add((word, float(count)))

    unigrams = []
    for topic in topic_unigrams.keys():
        unigrams.append( sorted(topic_unigrams[topic], key=lambda x: x[1],reverse=True)[:100])

    bigrams = []
    for topic in topic_bigrams.keys():
        bigrams.append( sorted(topic_bigrams[topic], key=lambda x: x[1],reverse=True)[:100])

    entities = []
    for topic in topic_bigrams.keys():
        entities.append( sorted(topic_entities[topic], key=lambda x: x[1],reverse=True)[:100])

    return (unigrams, bigrams, entities)


def topic_name_html(word_weights, global_min=None, global_max=None):
    def invert_hex(hex_number):
        inverse = hex(abs(int(hex_number, 16) - 255))[2:]
        # If the number is a single digit add a preceding zero
        if len(inverse) == 1:
            inverse = '0' + inverse
        return inverse

    def float_to_color(f):
        val = '%x' % int(f * 255)
        val = invert_hex(val)
        return '#%s%s%s' % (val, val, val)

    vals = [x[1] for x in word_weights]
    val_max = max(vals)
    val_min = math.sqrt(min(vals) / 2)
    val_diff = float(val_max - val_min)
    global_diff = float(global_max - global_min)

    ret = ''
    for (y, z) in sorted(word_weights, key=lambda x: x[1],
                         reverse=True):

        p = float(z - val_min) / val_diff

        if global_min and global_max:
            q = float(z - global_min) / global_diff
        else:
            q = p

        if y.startswith('#') and y.endswith('#'):
            y = y.replace('#', '')
            ret += '<a href="http://wikipedia.org/w/index.php?search=' + y.replace('_','+') + '">' +\
                   '<span style="color:%s" title="%s%% relevant">%s</span>' % (
                float_to_color(p), int(q * 100), y.replace('_', '&nbsp;')) + '</a>, '
        else:
            ret += '<span style="color:%s" title="%s%% relevant">%s</span>\n' % (
                float_to_color(p), int(q * 100), y.replace('_', '&nbsp;'))
    #ret = ret[:-2]
    return ret

def list_topic_components(keys_file, composition_file):
    g_unigram = ConceptGraph()
    g_unigram.read_keys(open(sys.argv[1], 'r'))
    g_unigram.read_weighted_keys(open(sys.argv[2], 'r'))

    g_bigram = ConceptGraph()
    g_bigram.read_keys(open(sys.argv[1], 'r'))
    g_bigram.read_weighted_keys(open(sys.argv[3], 'r'))

    g_entity = ConceptGraph()
    g_entity.read_keys(open(sys.argv[1], 'r'))
    g_entity.read_weighted_keys(open(sys.argv[4], 'r'))

    uniout = open('unigram-names.tsv', 'w')
    biout = open('bigram-names.tsv', 'w')
    entout = open('entity-names.tsv', 'w')

    for n in g_unigram.nodes:
        all_vals = [x[1] for x in g_unigram.word_weights[n]] + \
                   [x[1] for x in g_bigram.word_weights[n]] + \
                   [x[1] for x in g_entity.word_weights[n]]
        mi = min(all_vals)
        ma = max(all_vals)

        if g_unigram.word_weights[n] != []:
            print >> uniout, str(n) + '\t' + \
            topic_name_html(g_unigram.word_weights[n],
                            global_min=mi, global_max=ma)

        if g_bigram.word_weights[n] != []:
            print >> biout, str(n) + '\t' + \
            topic_name_html(g_bigram.word_weights[n],
                            global_min=mi, global_max=ma)

        if g_entity.word_weights[n] != []:
            print >> entout, str(n) + '\t' + \
            topic_name_html(g_entity.word_weights[n],
                            global_min=mi, global_max=ma)


def doc_name(did, doc_names):
    try:
        name = doc_names[did]['author'] + ': ' + '<a href="http://www.aclweb.org/anthology/' + did[0] + '/' + did[0:3] + '/' + did + '.pdf">' + doc_names[did]['title'] + '</a>'
        name = name.replace(' A ', ' a ')
        name = name.replace(' Of ', ' of ')
        name = name.replace(' As ', ' as ')
        name = name.replace(' The ', ' the ')
        name = name.replace(' To ', ' to ')
        name = name.replace(' And ', ' and ')
        name = name.replace(' For ', ' for ')
        name = name.replace(' In ', ' in ')
        name = name.replace(' With ', ' with ')
        name = name.replace(' By ', ' by ')
        name = name.replace(' On ', ' on ')
        name = name.replace(' - ', ' &ndash; ')
        name = name.replace(' -- ', ' &ndash; ')
        name = re.sub(', [^;,<>]+;', ', ', name)
        name = re.sub(', [^,:]+:', ':', name)
        return name
    except KeyError:
        return None

def read_documents(corpus_dir):
    first_lines = {}
    for root, dirs, files in os.walk(corpus_dir):
        for file in files:
            id = file.replace('.txt','')
            if os.path.isfile(root + '/' + file) and file[-4:] == '.txt':
                with codecs.open(root + '/' + file, 'r', 'utf-8') as f:
                    first_line = f.readline()
                    first_lines[id] = first_line
    return first_lines

def list_topic_docs(keys_file, composition_file, corpus_dir, n_docs_per_topic):

    docs_per_topic = []
    word_weights =  read_weighted_keys(open(keys_file, 'r'))
    (topic_doc, co_occur) = read_composition(open(composition_file, 'r'))

    first_lines_dict = read_documents(corpus_dir)

    for t in topic_doc:
        doc_list = []
        ordered_doc_refs = sorted(t,key=lambda x:(x[1]),reverse=True)

        for i in range(n_docs_per_topic):
            doc_ref = ordered_doc_refs[i][0]
            first_line = first_lines_dict.get(doc_ref, None)
            if(first_line is None):
                first_line = 'Error'
            doc_list.append(first_line + ' <em>[' + doc_ref + ']</em>')
        docs_per_topic.append(doc_list)

    return docs_per_topic

def make_eval_html_page(unigrams, bigrams, entities, docs):

    html_string = """
        <html>
        <head>
        <title>Topic Evaluation</title>
        <style type="text/css">
        body {
            margin: 2em auto;
            font-family: 'Univers LT Std', 'Helvetica', sans-serif;
            max-width: 900px;
            width: 90%;
        }

        article {
            border-top: 4px solid #888;
            padding-top: 3em;
            margin-top: 3em;
        }

        section {
            padding-bottom: 3em;
            border-bottom: 4px solid #888;
            margin-bottom: 4em;
        }

        section section {
            border: 0px;
            padding: 0px;
            margin: 0em 0em 3em 0em;
        }

        h1 { font-size: 18pt; }

        h2 { font-size: 14pt; }

        label { margin-right: 6px; }

        input { margin-left: 6px; }

        div.topic {
            padding: 1em;
        }

        p.rate { font-weight: bold; margin-left: 2em; }

        blockquote { margin-left: 40px; }

        a { text-decoration: none; font-style: italic; border-bottom: 1px dotted grey; }

        a:hover { color: blue !important; }
        a:hover span { color: blue !important; }

        </style>
        </head>
        <body>
        <h1>Topic Evaluation</h1>
        <article>
        <form id="eval_form" method="post" action="eval-post.php">
        <section>
        <h2>Instructions</h2>
        <p>You will be shown topics related to natural language processing
        and asked to judge them.</p>
        <p>Each topic is represented by a weighted collection of words, phrases,
        and entities, where the darker the color, the more important it is to
        the topic.</p>
        <p> Phrases may be missing common function words
        like &lsquo;of&rsquo;, making &lsquo;part of speech&rsquo; show up as
        &lsquo;part speech&rsquo;. Other phrases may be truncated or split, e.g.,
        &lsquo;automatic speech recognition&rsquo; will be displayed as
        &lsquo;automatic speech&rsquo; and &lsquo;speech recognition&rsquo;.</p>
        <p>You can click on the name of each entity to see its Wikipedia page. (You may need to choose the most relevant sense for ambiguous entities.</p>
        <p>For each
        topic you will also see a list of related papers, which you can click on to view
        in full.</p>
        <p>For each phrase associated with the topic you can hover your mouse to
        see how relevant it is to the topic. For each listed document, the
        percent of the document that is about the topic is displayed after the
        title.</p>
        <p>For each topic, you are asked how clear it is to you. A topic may be
        unclear because it is a mix of distinct ideas or because it is an area of
        research that is unfamiliar to you.</p>
        <p>Your Name: <input name="name" style="width: 300px" /></p>
        <p>Your Email: <input name="email" style="width: 300px" /></p>
        </section>
        """

    for topic in range(0, len(unigrams)):
        html_string += '<section>\n'
        html_string += '    <section>\n'
        html_string += '<h2>Topic ' + str(topic) + '</h2>'
        html_string += '<div class="topic">'

        '''
        html_string += '<p>Relevant entities:</p>'
        html_string += '<blockquote><p>', topic_rep[topic]['entity'], '</p></blockquote>'
        html_string += '<p>Relevant pairs of words:</p>'
        html_string += '<blockquote><p>', topic_rep[topic]['bigram'], '</p></blockquote>'
        '''

        html_string += '<p>Relevant words:</p>'
        html_string += topic_name_html(unigrams[topic],0,unigrams[topic][0][1])

        html_string += '<p>Relevant documents:</p><ul>'
        for doc_text in docs[topic]:
            html_string += '<li>'+doc_text+'</li>'
        html_string += '</ul>'

        html_string += '<p>How clear and coherent is the meaning of this topic?</p>'
        html_string += '<p class="rate">'
        for i, label in enumerate(['Very clear', 'Somewhat clear', 'Not very clear', 'Not clear at all'], 1):
            html_string += '<input type="radio" name="' + str(topic) + 'mean" id="' + str(topic) + 'mean-' + str(
                i) + '" value="' + str(i) + '" />'
            html_string += '<label for="' + str(topic) + 'mean-' + str(i) + '">' + label + '</label>'
        html_string += '</p>'

        html_string += '<p>Does this look like a combination of two or more distinct topics?</p>'
        html_string += '<p class="rate">'
        for i, label in enumerate(['No', 'Yes'], 1):
            html_string += '<input type="radio" name="' + str(topic) + 'comb" id="' + str(topic) + 'comb-' + str(
                i) + '" value="' + str(i) + '" />'
            html_string += '<label for="' + str(topic) + 'comb-' + str(i) + '">' + label + '</label>'
        html_string += '</p>'
        html_string += '<p>What short name would you give this topic?</p>'
        html_string += '<p class="rate">'
        html_string += '<input name="' + str(topic) + 'name" id="' + str(topic) + 'name" style="width: 400px" />'
        html_string += '</p>'
        html_string += '<p>Any comments?</p>'
        html_string += '<p class="rate">'
        html_string += '<textarea name="' + str(topic) + 'comment" id="' + str(
            topic) + 'comment" style="height: 100px; width: 600px"></textarea>'
        html_string += '</p>'
        html_string += '</section>'
        html_string += '</section>'

    html_string += """
        <section>
        <p><input id="submitButton" type="submit" name="Submit" value="Submit"
        /></p>
        </section>
        </form>
        </article>
        </body>
        </html>
    """

    return html_string

'''
in_dir,
docs_file='docs.tsv',
unigram_names_file='unigram-names.tsv',
bigram_names_file='bigram-names.tsv',
entity_names_file
'''

@click.command()
@click.argument('in_dir', type=click.Path(exists=True))
@click.argument('topic_counts_filename', type=click.STRING)
@click.argument('keys_filename', type=click.STRING)
@click.argument('composition_filename', type=click.STRING)
@click.argument('corpus_dir', type=click.STRING)
@click.argument('n_docs_per_topic', type=click.INT)
@click.argument('out_file', type=click.STRING)
def main(in_dir, topic_counts_filename, keys_filename, composition_filename, corpus_dir, n_docs_per_topic, out_file):

    '''
    json_str = ""
    progress = 0
    fileSize = os.path.getsize(cg_file)
    print('loading ' + cg_file)
    with open(cg_file, 'r') as inputFile:
        for line in inputFile:
            progress = progress + len(line)
            progressPercent = (1.0 * progress) / fileSize

            sys.stdout.write('\r')
            sys.stdout.write("[%-20s] %d%%" % ('='*(20*int(progressPercent)), (100 * progressPercent)))
            sys.stdout.flush()
            sys.stdout.write("")

            json_str += line

    cg = json.loads(json_str)
    '''

    (unigrams, bigrams, entities) = split_topic(in_dir+'/'+topic_counts_filename)
    docs_per_topic = list_topic_docs(in_dir+'/'+keys_filename, in_dir+'/'+composition_filename, corpus_dir, n_docs_per_topic)
    #list_topic_components(in_dir + '/' + keys_filename)
    html = make_eval_html_page(unigrams, bigrams, entities, docs_per_topic)
    
    output = open(out_file, 'w')
    output.write(html)
    output.close()

if __name__ == '__main__':
    main()
