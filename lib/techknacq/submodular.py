
import re, math
from collections import Counter
from lib.techknacq.conceptgraph import ConceptGraph
from lib.techknacq.readinglist import ReadingList
from lib.techknacq.constantvalues import ConstantValues
import click

def text_to_vector(text):
    #print("text to vecctor: "+text)
    WORD = re.compile(r'\w+')
    words = WORD.findall(text)
    return Counter(words)

def get_cosine(vec1, vec2):
     intersection = set(vec1.keys()) & set(vec2.keys())
     numerator = sum([vec1[x] * vec2[x] for x in intersection])

     sum1 = sum([vec1[x]**2 for x in vec1.keys()])
     sum2 = sum([vec2[x]**2 for x in vec2.keys()])
     denominator = math.sqrt(sum1) * math.sqrt(sum2)

     if not denominator:
        return 0.0
     else:
        return float(numerator) / denominator

@click.command()
@click.argument('concept_graph', type=click.Path(exists=True))
@click.argument('query', nargs=-1)
def main(concept_graph, query):
    cg = ConceptGraph(click.format_filename(concept_graph))
    learner_model = {}
    for c in cg.concepts():
        learner_model[c] = ConstantValues.BEGINNER
    r = ReadingList(cg, query, learner_model)
    #print reading list
    #r.print()

    #summarise the reading list

    #convert r into list of papers
    r.convert2List()
    readinglist = r.getReadinglist()
    #before summarization
    print(len(readinglist))
    for doc in readinglist:
        print(doc)

    summarizedlist = greedyAlg(readinglist, ConstantValues.BUDGET)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc)


def greedyAlg(readinglist, budget):
    g=[]
    u = readinglist
    print("BUDGET: "+str(budget))
    while (len(u)>0 and len(g)<budget):
        dock = findArgmax(g, u, readinglist)
        print("dock: "+dock['title'])
        g.append(dock)
        #u.remove(dock)
        for i in range(len(u)):
            if u[i]==dock:
                u.pop(i)
                break
        print("len: "+str(len(g))+" "+str(len(u)))
    return g


def findArgmax(g, u, v):
    #bound = mmrCal(u)
    maxF = None
    argmax = None
    for doc in u:
        t=[]
        for x in g:
            t.append(x)
        t.append(doc)
        ft=mmrCal(t, v)
        #print("function mmr calculate: "+str(ft))
        if (maxF==None or maxF<ft):
            maxF=ft
            argmax=doc

    print("function mmr max: " + str(maxF)+" - "+str(argmax))
    return argmax

def mmrCal(s, v):
    fcut=0
    for doc1 in s:
        for doc2 in v:
            if (doc2 not in s):
                fcut+= cosineOf2Text(doc1['title'], doc2['title'])
    fpenalty = 0
    for doc1 in s:
        for doc2 in s:
            if (doc1 != doc2):
                fpenalty+= cosineOf2Text(doc1['title'], doc2['title'])
    return fcut-ConstantValues.PENALTY*fpenalty

def cosineOf2Text(text1, text2):
    vector1 = text_to_vector(text1)
    vector2 = text_to_vector(text2)

    return get_cosine(vector1, vector2)

if __name__ == '__main__':
    text1 = 'This is a foo bar sentence .'
    text2 = 'This sentence is similar to a foo bar sentence .'

    print('Cosine:', cosineOf2Text(text1, text2))
    main()