
import os, glob
import json

class Corpus:

    def __init__(self, path="../../sample/"):
        print(path)
        self.dictCorpus={}
        for filename in glob.glob(os.path.join(path, '*.json')):
            with open(filename, 'r', encoding="utf-8") as fout:
                doc=""
                jsondata = json.load(fout)
                docid = jsondata['info']['id']
                for jsonHeading in jsondata['sections']:
                    headings = jsonHeading['text']
                    for text in headings:
                        doc+=text+"\n"
                #print(doc)
                self.dictCorpus[docid]=doc
                #print(filename)
                #print(jsondata['sections'][0])

    def getRawDocs(self):
        docs=[]
        ids=[]
        if self.dictCorpus:
            for (id, doc) in self.dictCorpus.items():
                ids.append(id)
                docs.append(doc)
        return ids, docs

#corpus = Corpus()
#print(corpus.getRawDocs())