import argparse
import os.path
import json
from base64 import b64decode
import re
from collections import defaultdict


class Indexer(object):

    def __init__(self):
        self.inverted_index = dict()
        self.forward_index = dict()
        self.url_to_id = dict()
        self.doc_count = 0

    def add_document(self, url, parsed_text):
        # give unique number to file
        self.doc_count += 1
        # check if document was already added
        assert url not in self.url_to_id
        # update url to id
        # self.url_to_id[self.doc_count] = url.decode("utf-8")
        self.url_to_id[url.decode("utf-8")] = self.doc_count
        current_id = self.doc_count
        # update forward index
        self.forward_index[current_id] = parsed_text
        # update inverted index
        for position, word in enumerate(parsed_text):
            if word not in self.inverted_index:
                self.inverted_index[word] = []
            self.inverted_index[word].append((position, current_id))

    def save_on_disk(self, index_dir):

        def dump_json_to_file(source, file_name):
            file_path = os.path.join(index_dir, file_name)
            json.dump(source, open(file_path, "w"), indent=6)

        dump_json_to_file(self.inverted_index, "inverted_index")
        dump_json_to_file(self.forward_index, "forward_index")
        dump_json_to_file(self.url_to_id, "url_to_id")


def create_index_from_dir(crawled_data_dir, index_directory):
    indexer = Indexer()
    # loop through each file in crawled_data
    for filename in os.listdir(crawled_data_dir):
        # open and read file
        opened_file = open(os.path.join(crawled_data_dir, filename), encoding="utf8")
        read_file = opened_file.read()
        opened_file.close()
        # parse file
        parsed_doc = (re.split('; |, | |\n', read_file.lower()))
        for term in parsed_doc:
            if term == "":
                parsed_doc.remove("")
        # add document to indexes
        indexer.add_document(b64decode(filename), parsed_doc)
    # save indexes on disk in JSON file
    indexer.save_on_disk(index_directory)


class Searcher(object):
    def __init__(self, index_dir):
        self.inverted_index = dict()
        self.forward_index = dict()
        self.url_to_id = dict()

        # function to load file from json
        def load_json_from_file(file_name):
            file_path = os.path.join(index_dir, file_name)
            return json.load(open(file_path))

        # load indexes from json
        self.inverted_index = load_json_from_file("inverted_index")
        self.forward_index = load_json_from_file("forward_index")
        self.url_to_id = load_json_from_file("url_to_id")

        # swap url and ids
        self.id_to_url = {value: key for (key, value) in self.url_to_id.items()}

    def generate_snippet(self, query_words, docid):
        query_words_in_window = []
        best_window = []
        best_window_len = 100500
        # iterate through all words in doc
        for pos, word in enumerate(self.forward_index[str(docid)]):
            # if given word in query
            if word in query_words:
                # add it to window snippet
                query_words_in_window.append((word, pos))
                # if the same word is appeared
                if len(query_words_in_window) > 1 and query_words_in_window[0][0] == word:
                    query_words_in_window.pop(0)
                # update position
                current_window_len = pos - query_words_in_window[0][1] + 1
                # if the best window snippet was found
                if len(set(query_words_in_window)) == len(query_words) and current_window_len < best_window_len:
                    best_window = query_words_in_window[:]
                    best_len = current_window_len
        # return best window snippet containing all words from query
        return self.forward_index[str(docid)][best_window[0][1]:(best_window[len(best_window) - 1][1]) + 1]

    # find documents by words
    # def find_documents(self, query_words):
    #     return sum([self.inverted_index[query_word] for query_word in query_words], [])
    def find_documents_AND(self, query_words):
        query_word_count = defaultdict(set)
        for query_word in query_words:
            for (pos, docid) in self.inverted_index[query_word]:
                query_word_count[docid].add(query_word)
        return [docid for docid, unique_hits in query_word_count.items() if len(unique_hits) == len(query_words)]

    # get url by doc id
    def get_url(self, docid):
        return self.id_to_url[docid]

    # get document text
    def get_document_text(self, docid):
        return self.forward_index[str(docid)]


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
