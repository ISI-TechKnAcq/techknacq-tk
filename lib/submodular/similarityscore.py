#Author: Binh Kieu Thanh
#Lib for similarity scores
#cosine similarity
#


import re, math
from collections import Counter
#from lib.submodular.constantvalues import ConstantValues

class SimilarityScores:

    def __init__(self, text1, text2, measure = 0):
        self.text1=text1
        self.text2=text2
        self.measure=measure

    def getScore(self):
        if self.measure==0:
            return self.cosineOf2Text(self.text1, self.text2)
        else:
            return 0.0

    def cosineOf2Text(self, text1, text2):
        vector1 = self.text_to_vector(text1)
        vector2 = self.text_to_vector(text2)

        return self.get_cosine(vector1, vector2)

    def text_to_vector(self, text):
        #print("text to vecctor: "+text)
        WORD = re.compile(r'\w+')
        words = WORD.findall(text)
        return Counter(words)

    def get_cosine(self, vec1, vec2):
         intersection = set(vec1.keys()) & set(vec2.keys())
         numerator = sum([vec1[x] * vec2[x] for x in intersection])

         sum1 = sum([vec1[x]**2 for x in vec1.keys()])
         sum2 = sum([vec2[x]**2 for x in vec2.keys()])
         denominator = math.sqrt(sum1) * math.sqrt(sum2)

         if not denominator:
            return 0.0
         else:
            return float(numerator) / denominator
