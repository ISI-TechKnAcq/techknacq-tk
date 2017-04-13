#!/usr/bin/env python3

# Convert a topic model from alt-dt.txt format to Linhong's.

import sys
import fileinput
from collections import defaultdict

comp = defaultdict(dict)

for line in fileinput.input():
    fields = line.strip().split('\t')
    topicnum = fields[0]
    for (doc, pct) in [x.split(':') for x in fields[1:]]:
        comp[doc][topicnum] = float(pct)

for doc in comp:
    sys.stdout.write('/' + doc + '.txt\t')
    for topicnum in sorted(comp[doc], key=lambda x: comp[doc][x], reverse=True):
        sys.stdout.write('\ttopic' + topicnum + ':' + str(comp[doc][topicnum]))
    print()
