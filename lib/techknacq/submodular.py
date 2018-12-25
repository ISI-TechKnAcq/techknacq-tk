
import re, math
from collections import Counter
from lib.techknacq.conceptgraph import ConceptGraph
from lib.techknacq.readinglist import ReadingList
from lib.techknacq.constantvalues import ConstantValues
import click

def text_to_vector(text):
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
    



if __name__ == '__main__':
    text1 = 'This is a foo bar sentence .'
    text2 = 'This sentence is similar to a foo bar sentence .'

    vector1 = text_to_vector(text1)
    vector2 = text_to_vector(text2)

    cosine = get_cosine(vector1, vector2)

    print('Cosine:', cosine)
    main()