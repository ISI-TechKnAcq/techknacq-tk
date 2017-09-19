#!/usr/bin/env python3

# Topic Mapping Script
# Gully Burns

import math
import operator
import os
import pickle
import random
from datetime import datetime

import bokeh.plotting as bp
import click
import numpy as np
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, HoverTool, TapTool, OpenURL
from bokeh.models import PanTool, BoxZoomTool, WheelZoomTool, ResetTool
from numpy.linalg import norm
from sklearn.manifold import TSNE
from tqdm import tqdm

from mallet import Mallet
from techknacq.corpus import Corpus

#
# Provides HTML code for a single topic signature based on greyscale coding
# for each word
#
def topic_signature_html(m, t_tuple, n_words, colormap, global_min=None, global_max=None):
    t_id = t_tuple[0]
    t_percent = t_tuple[1]
    color = colormap[t_id]

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

    ret = '<emph><font color="' + color + '">&#x25A0; </font>#' + str(t_id) + ' (' + t_percent_2sf + '): </emph>'

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

def document_signature_html(corpus, doc_id, DT, m, doc_list, n_topics, n_words, colormap):
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
    html_signature += '</br>'.join([topic_signature_html(m, top_topics[i], n_words, colormap) for i in range(n_topics)])
    html_signature += '</p>'

    return html_signature
#
# SCRIPT TO RUN TOPIC MAPPING VISUALIZATION UNDER DIFFERENT METHODS
#
@click.command()
@click.argument('topicmodel_dir', type=click.STRING)
@click.argument('corpus_dir', type=click.Path(exists=True))
@click.argument('viz_dir', type=click.Path())
def main(topicmodel_dir, corpus_dir, viz_dir):

    MALLET_PATH = '/usr/local/bin/mallet'

    if os.path.exists(viz_dir) is False:
        os.makedirs(viz_dir)

    corpus = Corpus(corpus_dir)
    m = Mallet(MALLET_PATH, topicmodel_dir, prefix=topicmodel_dir)

    td = []
    doc_list = [d_tuple[0] for d_tuple in m.topic_doc[0]]

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

    tsne_lda_pkl_path = viz_dir + "/tsne_lda.pkl"

    if os.path.isfile(tsne_lda_pkl_path) is False:

        tsne_model = TSNE(n_components=2, verbose=1, random_state=0, angle=.99, init='pca')
        tsne_lda = tsne_model.fit_transform(DT)

        # save the t-SNE model
        tsne_lda_pkl_file = open(tsne_lda_pkl_path, 'wb')
        pickle.dump(tsne_lda, tsne_lda_pkl_file)
        tsne_lda_pkl_file.close()

    else:

        tsne_lda_pkl_file = open(tsne_lda_pkl_path, 'rb')
        tsne_lda = pickle.load(tsne_lda_pkl_file)
        tsne_lda_pkl_file.close()

    # Code to create the HTML display
    colors = []
    for i in range(200):
        r = lambda: random.randint(0,255)
        colors.append('#%02X%02X%02X' % (r(),r(),r()))

    colormap = np.array(colors)
    print(len(colormap))

    html_signatures = []
    for i in tqdm(range(n_docs)):
        html_signatures.append(document_signature_html(corpus, i, DT, m, doc_list, 5, 10, colormap))

    #display(HTML(html_signatures[0]))

    doc_count = DT.shape[0]
    doc_urls = [corpus[doc_list[i]].url for i in range(doc_count)]

    topic_keys = []
    for i in range(DT.shape[0]):
        topic_keys += DT[i].argmax(),

    markers = []
    for i in range(DT.shape[0]):
        if 'video' in doc_list[i]:
            markers.append('triangle')
        else:
            markers.append('circle')

    title = 'ERUDITE Visualization'
    num_example = len(DT)

    hover = HoverTool(tooltips="""
        <div>
            <span>
                @html_signatures{safe}
            </span>
        </div>
        """
        )

    pan = PanTool()
    boxzoom = BoxZoomTool()
    wheelzoom = WheelZoomTool()
    resetzoom = ResetTool()
    tap = TapTool(callback=OpenURL(url="@doc_urls"))

    cds = ColumnDataSource({
        "x": tsne_lda[:, 0],
        "y": tsne_lda[:, 1],
        "color": colormap[topic_keys][:num_example],
        "html_signatures": html_signatures,
        "doc_urls": doc_urls,
        "marker": markers
    })

    # plot_lda = bp.figure(plot_width=1400, plot_height=1100,
    #                     title=title,
    #                     tools="pan,wheel_zoom,box_zoom,reset,hover,previewsave",
    #                     x_axis_type=None, y_axis_type=None, min_border=1)

    plot_lda = bp.figure(plot_width=1400, plot_height=1100,
                         title=title,
                         tools=[pan, boxzoom, wheelzoom, resetzoom, hover, tap],
                         active_drag=pan,
                         active_scroll=wheelzoom,
                         x_axis_type=None, y_axis_type=None, min_border=1)

    # HACK TO GENERATE DIFFERENT PLOTS FOR CIRCLES AND TRIANGLES
    marker_types = ['circle', 'triangle']
    for mt in marker_types:
        x = []
        y = []
        color = []
        html_sig = []
        doc_url = []
        print(mt)
        for i in tqdm(range(DT.shape[0])):
            if markers[i] == mt:
                x.append(tsne_lda[i, 0])
                y.append(tsne_lda[i, 1])
                color.append(colormap[topic_keys][i])
                html_sig.append(html_signatures[i])
                doc_url.append(doc_urls[i])
        cds_temp = ColumnDataSource({
            "x": x,
            "y": y,
            "color": color,
            "html_signatures": html_sig,
            "doc_urls": doc_url
        })

        plot_lda.scatter('x', 'y', color='color', marker=mt, source=cds_temp)

    #plot_lda.scatter('x', 'y', color='color', source=cds)

    now = datetime.now().strftime("%d-%b-%Y-%H%M%S")

    output_file(viz_dir + '/scatterplot' + now + '.html', title=title, mode='cdn',
                root_dir=None)
    show(plot_lda)

if __name__ == '__main__':
    main()
