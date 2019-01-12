
import os, glob
import json

class Corpus:
    def __init__(self, path="../../sample/"):
        print(path)
        for filename in glob.glob(os.path.join(path, '*.json')):
            with open(filename, 'r', encoding="utf-8") as fout:
                jsondata = json.load(fout)
                print(filename)
                print(jsondata['sections'][0])

corpus = Corpus()