import math

# used for old ranking functions based on reddit score
# from collections import defaultdict

# class to store data about pages
class SerpPagination(object):
    def __init__(self, page, page_size, total_doc_num):
        self.page = page
        self.page_size = page_size
        self.pages = math.floor(total_doc_num / page_size) + 1

    # logic for pages visualization
    def iter_pages(self):
        if self.pages == 1:
            return [1]
        if self.page <= 6:
            left_part = range(1, self.page)
        else:
            left_part = [1, None] + list(range(self.page - 4, self.page))
        right_part = range(self.page, min(self.pages + 1, self.page + 5))
        result = list(left_part) + list(right_part)
        if result[-1] != self.page:
            result.append(None)
        return result


# class to store search results
class SearchResults:
    # store docids and its relevances according to bm25
    def __init__(self, docids):
        self.docids, self.relevances = zip(*docids) if docids else ([], [])

    # paging
    def get_page(self, page, page_size):
        start_num = (page - 1) * page_size
        return self.docids[start_num:start_num + page_size]

    def get_pagination(self, page, page_size):
        return SerpPagination(page, page_size, len(self.docids))

    def total_doc_num(self):
        return len(self.docids)


# Searcher
class Searcher(object):
    def __init__(self, index_dir, IndexesImplementation):
        self.indexes = IndexesImplementation()
        self.indexes.load_from_disk(index_dir)

    # bm 25 ranking for given doc and query terms
    def _bm25(self, docid, query_terms_to_posting_lists_sizes):
        # initial rank
        rank = 0
        # get text by docid
        text = self.indexes.get_document_text(docid)
        # get len of all text
        text_len = len(text)
        # * qt - query term
        # * nd_containing - how many docs containing given query term
        for qt, nd_containing in query_terms_to_posting_lists_sizes.items():
            # find how many times qt appeared in doc
            count_of_qt_in_doc = 0
            for term in text:
                if term == qt:
                    count_of_qt_in_doc += 1
            # compute term frequency in doc
            term_frequency = count_of_qt_in_doc / text_len
            # calculate IDF
            inverted_document_frequency = math.log(
                (self.indexes.total_doc_count() - nd_containing + 0.5) / (nd_containing + 0.5))
            # calculate rank with given k1 and b below:
            k1 = 1.5
            b = 0.75
            rank += inverted_document_frequency * (term_frequency * (k1 + 1)) / (term_frequency + k1 * (
                    1 - b + b * query_terms_to_posting_lists_sizes[qt] / self.indexes.average_doc_len()))
        return rank

    # bm25 for all docs
    def find_documents_and_rank_by_bm25(self, query_terms):
        docids = set()
        query_terms_to_posting_lists_sizes = dict()
        for query_term in query_terms:
            # documents containing query term
            posting_list = self.indexes.get_documents(query_term)
            # how many documents containing query term
            query_terms_to_posting_lists_sizes[query_term] = len(posting_list)
            # add docid to all docids
            for (pos, docid) in posting_list:
                docids.add(docid)
        # create docids and their relevance by bm25 algorithm
        docids_and_relevance = set()
        # update each doc
        for docid in docids:
            docids_and_relevance.add((docid, self._bm25(docid, query_terms_to_posting_lists_sizes)))
        # return search results based on their relevance
        return SearchResults(sorted(list(docids_and_relevance), key=lambda x: x[1], reverse=True))

    # OLD RANKING FUNCTIONS STILL WORKS BUT REDUNDANT
    # def rank_docids(self, docids):
    #     return sorted([(docid, self.indexes.get_document_score(docid)) for docid in docids], key=lambda x: x[1],
    #                   reverse=True)
    #
    # # find documents by terms
    # def find_documents_and_rank_by_score_and(self, query_terms):
    #     query_term_count = defaultdict(set)
    #     for query_term in query_terms:
    #         for (pos, docid) in self.indexes.get_documents(query_term):
    #             query_term_count[docid].add(query_term)
    #     return SearchResults(self.rank_docids(
    #         [doc_id for doc_id, unique_hits in query_term_count.items() if len(unique_hits) == len(query_terms)]))
    #
    # def find_documents_and_rank_by_score_or(self, query_terms):
    #     docids = set()
    #     for query_term in query_terms:
    #         for (pos, docid) in self.indexes.get_documents(query_term):
    #             docids.add(docid)
    #     return SearchResults(self.rank_docids(docids))


# generate snippet for given doc and query
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
    snippet_start = max(best_window[0][1] - 10, 0)
    snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 10)
    # return best window snippet containing all terms from query
    snippet = [(term.full_word, term in query_terms) for term in doc_text[snippet_start:snippet_end]]
    # if snippet is too long
    if len(snippet) > 50:
        # get excessive length of snippet
        excessive_len = len(snippet) - 50
        # cut it
        snippet = snippet[:int(len(snippet) / 2) - int(excessive_len / 2)] + [("...", False)] + snippet[int(
            len(snippet) / 2) + int(excessive_len / 2):]
    return snippet
