#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Visualize a (JSON) concept graph file as a PDF
# Jonathan Gordon, 2015-06-22

import sys
import argparse
import json
from igraph import *

def main():
    parser = argparse.ArgumentParser(description='Visualize concept graph.')
    parser.add_argument('graph', help='JSON concept graph file')
    parser.add_argument('-o', '--output', nargs='?', default='graph.pdf',
        help='Output file name')
    parser.add_argument('-l', '--layout', nargs='?', default='drl',
        help='iGraph layout function (http://igraph.org/python/doc/tutorial/tutorial.html#layout-algorithms)')

    try:
        args = parser.parse_args()
    except IOError, msg:
        parser.error(str(msg))

    j = json.loads(open(args.graph).read())

    g = Graph()
    i = 0
    eCount = 0

    nodeCount = 0;
    for n in j['graph']['nodes']:
        if 'uuid' in n.keys():
            nodeCount = nodeCount+1

    g.add_vertices(nodeCount)
    nodeHash = {}

    i = 0
    for n in j['graph']['nodes']:
        if 'uuid' in n.keys():
            #g.vs[i]["label"] = n['name'].replace(' ', r'\n')
            nodeHash[ n['uuid'] ] = i
            i += 1;

    for e in j['graph']['edges']:
        c1 = nodeHash[ e['concept1'] ]
        c2 = nodeHash[ e['concept2'] ]
        g.add_edges([(c1, c2)])

    layout = g.layout(args.layout)
    plot(g, args.output, layout = layout)


if __name__ == '__main__':
    main()
