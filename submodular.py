
import re, math
from collections import Counter
from lib.techknacq.conceptgraph import ConceptGraph
from lib.techknacq.readinglist import ReadingList
from lib.techknacq.constantvalues import ConstantValues
import click
# from conceptgraph import ConceptGraph
# from readinglist import ReadingList
# from constantvalues import ConstantValues

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
    print("Before Submodular: ")
    print(len(readinglist))
    for doc in readinglist:
        print(doc['id']+" - "+str(doc))
    #Lambda = 0 -> no penalty
    print("Lambda = 0 -> No penalty")
    Lambda = 0.0
    summarizedlist = greedyAlg(readinglist, Lambda)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc['id'])

    #Lambda = 0.5 -> less penalty
    print("Lambda = 0.5 -> less penalty")
    Lambda = 0.5
    summarizedlist = greedyAlg(readinglist, Lambda)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc['id'])
    #Lambda = 1.0 -> same degree penalty
    print("Lambda = 1.0 -> same degree penalty")
    Lambda = 1.0
    summarizedlist = greedyAlg(readinglist, Lambda)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc['id'])
    #Lambda = 2.0 -> double degree penalty
    print("Lambda = 2.0 -> double degree penalty")
    Lambda = 2.0
    summarizedlist = greedyAlg(readinglist, Lambda)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc['id'])
    #Lambda = 3.0 -> as paper
    print("#Lambda = 3.0 -> as the paper chosen")
    Lambda = 3.0
    summarizedlist = greedyAlg(readinglist, Lambda)
    print(len(summarizedlist))
    for doc in summarizedlist:
        print(doc['id'])

def greedyAlg(readinglist, Lambda):
    g=[]
    u=[]
    for doc in readinglist:
        u.append(doc)
    #print("BUDGET: "+str(budget))
    while (len(u)>0):
        dock, maxK = findArgmax(g, u, readinglist, Lambda)
        #print("dock: "+dock['title'])
        if (maxK>0):
            g.append(dock)
        #u.remove(dock)
        for i in range(len(u)):
            if u[i]==dock:
                #print("remove dock: "+str(dock))
                u.pop(i)
                break
        print("len: "+str(len(g))+" "+str(len(u)))
    return g


def findArgmax(g, u, v, Lambda):
    #bound = mmrCal(g,v, Lambda)
    bound = crlCal(g, v, Lambda)
    print("bound: "+str(bound))
    maxF = None
    argmax = None
    for doc in u:
        t=[]
        for x in g:
            t.append(x)
        t.append(doc)
        #ft=mmrCal(t, v, Lambda)
        ft=crlCal(t, v, Lambda)
        #print("function mmr calculate: "+str(ft))
        if (maxF==None or maxF<ft):
            maxF=ft
            argmax=doc

    print("find mmr max: " + str(maxF))
    return argmax, maxF-bound

#as paper
def mmrCal(s,v, Lambda):
    if ConstantValues.SIMILARITY_MEASUE=='title':
        return mmrCal4Title(s, v, Lambda)
    elif ConstantValues.SIMILARITY_MEASUE=='abstract':
        return mmrCal4Abstract(s, v, Lambda)

#concept reading list
def crlCal(s,v, Lambda):
    if ConstantValues.SIMILARITY_MEASUE=='title':
        return crlCal4Title(s, v, Lambda)
    elif ConstantValues.SIMILARITY_MEASUE=='abstract':
        return crlCal4Abstract(s, v, Lambda)

def crlCal4Abstract(s, v, Lambda):
    fcover = 0
    # print(str(len(s))+' - '+str(len(v)))
    for doc in s:
        fcover+=doc['score']
    fpenalty = 0
    for doc1 in s:
        for doc2 in s:
            if (doc1 != doc2):
                fpenalty += cosineOf2Text(doc1['title'], doc2['title'])
    return fcover - Lambda * fpenalty

def crlCal4Title(s, v, Lambda):
    fcover = 0.0
    # print(str(len(s))+' - '+str(len(v)))
    for doc in s:
        fcover+=doc['score']
    fpenalty = 0.0
    count=0
    for doc1 in s:
        for doc2 in s:
            if (doc1 != doc2):
                abstract1 = ""
                abstract2 = ""
                for sentence in doc1['abstract']:
                    abstract1 += sentence
                for sentence in doc2['abstract']:
                    abstract2 += sentence
                fpenalty += cosineOf2Text(abstract1, abstract2)
                count+=1
    if count==0:
        count=1
    return fcover - Lambda * (fpenalty/count)

def mmrCal4Abstract(s, v, Lambda):
    fcover = 0.0
    # print(str(len(s))+' - '+str(len(v)))
    for doc1 in s:
        for doc2 in v:
            # print(str(doc2['title'])+ " "+str(doc2 in s))
            if (doc2 not in s):
                abstract1=""
                abstract2=""
                for sentence in doc1['abstract']:
                    abstract1+=sentence
                for sentence in doc2['abstract']:
                    abstract2+=sentence
                #print("abstract1 : \n" + abstract1 + " \n abstract2: \n " + abstract2)
                fcover += cosineOf2Text(abstract1, abstract2)
    fpenalty = 0.0
    count=0
    for doc1 in s:
        for doc2 in s:
            if (doc1 != doc2):
                abstract1 = ""
                abstract2 = ""
                for sentence in doc1['abstract']:
                    abstract1 += sentence
                for sentence in doc2['abstract']:
                    abstract2 += sentence
                #print("abstract1 : \n" + abstract1 + " \n abstract2: \n " + abstract2)
                fpenalty += cosineOf2Text(abstract1, abstract2)
                count+=1
    if count==0:
        count=1
    return fcover - Lambda * (fpenalty/count)

def mmrCal4Title(s, v, Lambda):
    fcover=0
    #print(str(len(s))+' - '+str(len(v)))
    for doc1 in s:
        for doc2 in v:
            #print(str(doc2['title'])+ " "+str(doc2 in s))
            if (doc2 not in s):
                fcover+= cosineOf2Text(doc1['title'], doc2['title'])
    fpenalty = 0
    for doc1 in s:
        for doc2 in s:
            if (doc1 != doc2):
                fpenalty+= cosineOf2Text(doc1['title'], doc2['title'])
    return fcover - Lambda * fpenalty

def cosineOf2Text(text1, text2):
    vector1 = text_to_vector(text1)
    vector2 = text_to_vector(text2)

    return get_cosine(vector1, vector2)

if __name__ == '__main__':

    main()