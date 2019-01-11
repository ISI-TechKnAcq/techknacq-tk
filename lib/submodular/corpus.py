
import os, glob

class Corpus:
    def __init__(self, path="../../data/acl/"):
        print(path)
        for filename in glob.glob(os.path.join(path, '*.json')):
            with open(filename, 'r') as f:
                text = f.read()
                print(filename)
                print(len(text))


corpus = Corpus()