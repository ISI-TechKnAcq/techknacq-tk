#Author: Binh Kieu Th
#Target: submodular functions for generating reading lists
#mmr: Maximal Marginal Relevance
#crl: Concept Relevance
#qfr: Query-Focused Relevance
#upr: Update Relevance




from lib.submodular.constantvalues import ConstantValues
from lib.submodular.similarityscore import SimilarityScores

# from conceptgraph import ConceptGraph
# from readinglist import ReadingList
# from constantvalues import ConstantValues

class Submodular:

    def __init__(self, readinglist, Lambda, alg=ConstantValues.LAZY_GREEDY_ALG):
        self.readinglist = readinglist
        self.Lambda = Lambda
        self.alg = alg

    def getSubmodular(self):
        if self.alg==ConstantValues.LAZY_GREEDY_ALG:
            return self.lazyGreedyAlg(self.readinglist, self.Lambda)
        else:
            return None #other alg

    def lazyGreedyAlg(self, readinglist, Lambda):
        g=[]
        u=[]
        for doc in readinglist:
            u.append(doc)
        #print("BUDGET: "+str(budget))
        while len(u)>0 and len(g)<ConstantValues.BUDGET:
            dock, maxK = self.findArgmax(g, u, readinglist, Lambda)
            #print("dock: "+dock['title'])
            #if (maxK>0):
            g.append(dock)
            #u.remove(dock)
            for i in range(len(u)):
                if u[i]==dock:
                    #print("remove dock: "+str(dock))
                    u.pop(i)
                    break
            print("len: "+str(len(g))+" "+str(len(u)))
        return g


    def findArgmax(self, g, u, v, Lambda):
        #bound = mmrCal(g,v, Lambda)
        bound = self.mmrCal(g, v, Lambda)
        print("bound: "+str(bound))
        maxF = None
        argmax = None
        for doc in u:
            t=[]
            for x in g:
                t.append(x)
            t.append(doc)
            ft=self.mmrCal(t, v, Lambda)
            #ft=crlCal(t, v, Lambda)
            #print("function mmr calculate: "+str(ft))
            if (maxF==None or maxF<ft):
                maxF=ft
                argmax=doc

        print("find max: " + str(maxF))
        return argmax, maxF-bound

    #as paper
    def mmrCal(self, s,v, Lambda):
        if ConstantValues.SIMILARITY_MEASUE=='title':
            return self.mmrCal4Title(s, v, Lambda)
        elif ConstantValues.SIMILARITY_MEASUE=='abstract':
            return self.mmrCal4Abstract(s, v, Lambda)

    #concept reading list
    def crlCal(self, s,v, Lambda):
        if ConstantValues.SIMILARITY_MEASUE=='title':
            return self.crlCal4Title(s, v, Lambda)
        elif ConstantValues.SIMILARITY_MEASUE=='abstract':
            return self.crlCal4Abstract(s, v, Lambda)

    def crlCal4Title(self,s, v, Lambda):
        fcover = 0
        # print(str(len(s))+' - '+str(len(v)))
        for doc in s:
            fcover+=doc['score']
        fpenalty = 0
        for doc1 in s:
            for doc2 in s:
                if (doc1 != doc2):

                    fpenalty += SimilarityScores(doc1['title'], doc2['title']).getScore()
        return fcover - Lambda * fpenalty

    def crlCal4Abstract(self, s, v, Lambda):
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
                    fpenalty += SimilarityScores(abstract1, abstract2).getScore()
                    count+=1
        if count==0:
            count=1
        #return fcover - Lambda * (fpenalty/count)
        return fcover - Lambda * fpenalty

    def mmrCal4Abstract(self, s, v, Lambda):
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
                    fcover += SimilarityScores(abstract1, abstract2).getScore()
        fpenalty = 0.0
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
                    fpenalty += SimilarityScores(abstract1, abstract2).getScore()

        return fcover - Lambda * fpenalty

    def mmrCal4Title(self, s, v, Lambda):
        fcover=0
        #print(str(len(s))+' - '+str(len(v)))
        for doc1 in s:
            for doc2 in v:
                #print(str(doc2['title'])+ " "+str(doc2 in s))
                if (doc2 not in s):
                    fcover+= SimilarityScores(doc1['title'], doc2['title']).getScore()
        fpenalty = 0
        for doc1 in s:
            for doc2 in s:
                if (doc1 != doc2):
                    fpenalty+= SimilarityScores(doc1['title'], doc2['title']).getScore()
        return fcover - Lambda * fpenalty


