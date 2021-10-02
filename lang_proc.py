from nltk.stem.porter import PorterStemmer
from nltk.tokenize import sent_tokenize, TreebankWordTokenizer
import itertools
import string
from nltk.corpus import stopwords

_stop_words = stopwords.words('english')


class Term(object):
    def __init__(self, full_word):
        self.full_word = full_word
        self.stem = PorterStemmer().stem(full_word).lower()

    def __eq__(self, other):
        return self.stem == other.stem

    def __hash__(self):
        return hash(self.stem)

    def __repr__(self):
        return "Term {}({})".format(self.stem, self.full_word)

    def __str__(self):
        return repr(self)

    def is_punctuation(self):
        return self.stem in string.punctuation

    def is_stop_word(self):
        return self.full_word in _stop_words


def stem_and_tokenize_text(raw_query):
    sents = sent_tokenize(raw_query)
    tokens = list(itertools.chain(*[TreebankWordTokenizer().tokenize(sent) for sent in sents]))
    terms = [Term(token) for token in tokens]
    correct_terms = []
    for term in terms:
        if not term.is_punctuation():
            correct_terms.append(term)
    return correct_terms
    # return filter(lambda term: not term.is_punctuation(), terms)


def to_query_terms(raw_query):
    return stem_and_tokenize_text(raw_query)


def to_doc_terms(raw_doc):
    return stem_and_tokenize_text(raw_doc)
