#tf-idf
#concept scores

from lib.submodular.corpus import Corpus
#We will use a library in Python called gensim.
import gensim
print(dir(gensim))

#Let's create some documents.
#raw_documents = ["I'm taking the show on the road.",
#                 "My socks are a force multiplier.",
#             "I am the barber who cuts everyone's hair who doesn't cut their own.",
#             "Legend has it that the mind is a mad monkey.",
#            "I make my own fun."]

corpus = Corpus()
id_documents, raw_documents = corpus.getRawDocs()
#id_documents = corpus.getIdDocs()
print(id_documents)
print("Number of documents:",len(raw_documents))

#We will use NLTK to tokenize.
#A document will now be a list of tokens.
from nltk.tokenize import word_tokenize
gen_docs = [[w.lower() for w in word_tokenize(text)]
            for text in raw_documents]
print(gen_docs)

#We will create a dictionary from a list of documents. A dictionary maps every word to a number.
dictionary = gensim.corpora.Dictionary(gen_docs)
# print(dictionary[5])
# print(dictionary.token2id['road'])
print("Number of words in dictionary:",len(dictionary))
# for i in range(len(dictionary)):
#     print(i, dictionary[i])

#Now we will create a corpus. A corpus is a list of bags of words. A bag-of-words representation for a document just lists the number of times each word occurs in the document.
corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
# print(corpus)

#Now we create a tf-idf model from the corpus. Note that num_nnz is the number of tokens.
tf_idf = gensim.models.TfidfModel(corpus)
# print(tf_idf)
# s = 0
# for i in corpus:
#     s += len(i)
# print(s)

#Now we will create a similarity measure object in tf-idf space.
#tf-idf stands for term frequency-inverse document frequency. Term frequency is how often the word shows up in the document and inverse document fequency scales the value by how rare the word is in the corpus.
sims = gensim.similarities.Similarity('../../tmp/',tf_idf[corpus],
                                      num_features=len(dictionary))
# print(sims)
# print(type(sims))

#Now create a query document and convert it to tf-idf.
query_doc = [w.lower() for w in word_tokenize("concept to text")]
# print(query_doc)
query_doc_bow = dictionary.doc2bow(query_doc)
# print(query_doc_bow)
query_doc_tf_idf = tf_idf[query_doc_bow]
# print(query_doc_tf_idf)

#We show an array of document similarities to query. We see that the second document is the most similar with the overlapping of socks and force.
# print(sims[query_doc_tf_idf])
for i in range(len(sims[query_doc_tf_idf])):
    print(str(sims[query_doc_tf_idf][i])+" - "+str(id_documents[i]))