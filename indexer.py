import argparse
import os.path
import json
import pickle
from base64 import b64decode
from collections import defaultdict

from lang_proc import to_doc_terms


class Indexer(object):

    def __init__(self):
        self.inverted_index = defaultdict(list)
        self.forward_index = dict()
        self.url_to_id = dict()
        self.doc_count = 0

    def add_document(self, url, parsed_text):
        # give unique number to file
        self.doc_count += 1
        # check if document was already added
        assert url not in self.url_to_id
        # update url to id
        self.url_to_id[url.decode("utf-8")] = self.doc_count
        current_id = self.doc_count
        # update forward index
        self.forward_index[current_id] = parsed_text
        # update inverted index
        for position, term in enumerate(parsed_text):
            self.inverted_index[term].append((position, current_id))

    def save_on_disk(self, index_dir):

        def dump_pickle_to_file(source, file_name):
            file_path = os.path.join(index_dir, file_name)
            pickle.dump(source, open(file_path, "wb"))

        dump_pickle_to_file(self.inverted_index, "inverted_index")
        dump_pickle_to_file(self.forward_index, "forward_index")
        dump_pickle_to_file(self.url_to_id, "url_to_id")


class Searcher(object):
    def __init__(self, index_dir):
        self.inverted_index = dict()
        self.forward_index = dict()
        self.url_to_id = dict()

        def load_pickle_from_file(file_name):
            file_path = os.path.join(index_dir, file_name)
            dst = pickle.load(open(file_path, 'rb'))
            return dst

        self.inverted_index = load_pickle_from_file("inverted_index")
        self.forward_index = load_pickle_from_file("forward_index")
        self.url_to_id = load_pickle_from_file("url_to_id")

        # swap url and ids
        self.id_to_url = {value: key for (key, value) in self.url_to_id.items()}

    def generate_snippet(self, query_terms, docid):
        query_terms_in_window = []
        best_window = []
        best_window_len = 100500
        terms_in_best_window = 0
        # iterate through all terms in doc
        for pos, term in enumerate(self.forward_index[docid]):
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
        doc_len = len(self.forward_index[docid])
        snippet_start = max(best_window[0][1] - 15, 0)
        snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 15)
        # return best window snippet containing all terms from query
        return [(term.full_word, term in query_terms) for term in self.forward_index[docid][snippet_start:snippet_end]]

    # find documents by terms
    def find_documents_AND(self, query_terms):
        query_term_count = defaultdict(set)
        for query_term in query_terms:
            for (pos, docid) in self.inverted_index[query_term]:
                query_term_count[docid].add(query_term)
        return [docid for docid, unique_hits in query_term_count.items() if len(unique_hits) == len(query_terms)]

    def find_documents_OR(self, query_terms):
        docids = set()
        for query_term in query_terms:
            for (pos, docid) in self.inverted_index.get(query_term, []):
                docids.add(docid)
        return docids

    # get url by doc id
    def get_url(self, docid):
        return self.id_to_url[docid]

    # get document text
    def get_document_text(self, docid):
        return self.forward_index[docid]


def create_index_from_dir(crawled_data_dir, index_directory):
    indexer = Indexer()
    # loop through each file in crawled_data
    for filename in os.listdir(crawled_data_dir):
        # open and read file
        opened_file = open(os.path.join(crawled_data_dir, filename), encoding="utf8")
        raw_doc = opened_file.read()
        opened_file.close()
        # parse file
        parsed_doc = to_doc_terms(raw_doc)
        # add document to indexes
        indexer.add_document(b64decode(filename), parsed_doc)
    # save indexes on disk in JSON file
    indexer.save_on_disk(index_directory)


def main():
    # get arguments
    parser = argparse.ArgumentParser(description="Index /r/{your subreddit}")
    # parser.add_argument("crawled_data", required=True)
    # parser.add_argument("index_dir", required=True)
    parser.add_argument("crawled_data")
    parser.add_argument("index_dir")
    args = parser.parse_args()
    # check if indexes already created
    try:
        os.mkdir(args.index_dir)
    except FileExistsError:
        print("Folder is already created")
        exit()
    print("Crawled data: " + args.crawled_data)
    print("Index directory: " + args.index_dir)
    # create indexes
    create_index_from_dir(args.crawled_data, args.index_dir)
    print("Success!")


if __name__ == "__main__":
    main()
