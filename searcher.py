import math
from collections import defaultdict


class SearchResults:
    def __init__(self, docids):
        self.docids, self.relevances = zip(*docids) if docids else ([], [])

    def get_page(self, page, page_size):
        start_num = (page - 1) * page_size
        return self.docids[start_num:start_num + page_size]

    def total_pages(self, page_size):
        return math.floor((len(self.docids) + page_size) / page_size)

    def total_doc_num(self):
        return len(self.docids)


class Searcher(object):
    def __init__(self, index_dir, IndexesImplementation):
        self.indexes = IndexesImplementation()
        self.indexes.load_from_disk(index_dir)

    # TODO 2
    # def _bm25(self, docid, query_terms_to_posting_lists_sizes):
    #     result = 0
    #     text = self.indexes.get_document_text(docid)
    #     text_len = len(text)
    #     for qt, nd_containing in query_terms_to_posting_lists_sizes.iteritems():
    #         term_frequency = float(len(filter(lambda t: qt == t, text))) / text_len
    #         inverted_document_frequency = math.log(
    #             (self.indexes.total_doc_count() - nd_containing + 0.5) / (nd_containing + 0.5))
    #         k1 = 1.5
    #         b = 0.75
    #         result += inverted_document_frequency * (term_frequency * (k1 + 1)) / (term_frequency + k1 * (
    #                 1 - b + b * query_terms_to_posting_lists_sizes[qt] / self.indexes.average_doclen()))
    #
    #     return result

    # TODO 2
    # def find_documents_and_rank_by_bm25(self, query_terms):
    #     docids = set()
    #     query_terms_to_posting_lists_sizes = dict()
    #     for query_term in query_terms:
    #         posting_list = self.indexes.get_documents(query_term)
    #         query_terms_to_posting_lists_sizes[query_term] = len(posting_list)
    #         for hit in posting_list:
    #             docids.add(hit.docid)
    #
    #     docids_and_relevance = set()
    #     for docid in docids:
    #         docids_and_relevance.add((docid, self._bm25(docid, query_terms_to_posting_lists_sizes)))
    #
    #     print(docids_and_relevance)
    #     return SearchResults(sorted(list(docids_and_relevance), key=lambda x: x[1], reverse=True))

    # OLD RANKING FUNCTIONS
    def rank_docids(self, docids):
        return sorted([(docid, self.indexes.get_document_score(docid)) for docid in docids], key=lambda x: x[1],
                      reverse=True)

    # find documents by terms
    def find_documents_and_rank_by_score_and(self, query_terms):
        query_term_count = defaultdict(set)
        for query_term in query_terms:
            for (pos, docid) in self.indexes.get_documents(query_term):
                query_term_count[docid].add(query_term)
        return SearchResults(self.rank_docids(
            [doc_id for doc_id, unique_hits in query_term_count.items() if len(unique_hits) == len(query_terms)]))

    def find_documents_and_rank_by_score_or(self, query_terms):
        docids = set()
        for query_term in query_terms:
            for (pos, docid) in self.indexes.get_documents(query_term):
                docids.add(docid)
        return SearchResults(self.rank_docids(docids))


def generate_snippet(query_terms, doc_text):
    query_terms_in_window = []
    best_window = []
    best_window_len = 100500
    terms_in_best_window = 0
    # iterate through all terms in doc
    for pos, term in enumerate(doc_text):
        # if given term in query
        if term in query_terms:
            # add it to window snippet
            query_terms_in_window.append((term, pos))
            # if the same term is appeared
            if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == term:
                query_terms_in_window.pop(0)
            # update position
            current_window_len = pos - query_terms_in_window[0][1] + 1
            terms_in_window = len(set(map(lambda x: x[0], query_terms_in_window)))
            # if the best window snippet was found
            if terms_in_window > terms_in_best_window or (
                    terms_in_window == terms_in_best_window and current_window_len < best_window_len):
                terms_in_best_window = terms_in_window
                best_window = query_terms_in_window[:]
                best_window_len = current_window_len
    # find best window
    doc_len = len(doc_text)
    snippet_start = max(best_window[0][1] - 15, 0)
    snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 15)
    # return best window snippet containing all terms from query
    return [(term.full_word, term in query_terms) for term in
            doc_text[snippet_start:snippet_end]]
