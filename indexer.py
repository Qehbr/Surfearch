import argparse
import os.path
import json
from base64 import b64decode
import re


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
        current_id = self.doc_count
        # update forward index
        self.forward_index[current_id] = parsed_text
        # update inverted index
        for position, word in enumerate(parsed_text):
            if word not in self.inverted_index:
                self.inverted_index[word] = []
            self.inverted_index[word].append((position, current_id))

    def save_on_disk(self, index_dir):
        # create file names
        inverted_index_file_name = os.path.join(index_dir, "inverted_index")
        forward_index_file_name = os.path.join(index_dir, "forward_index")
        url_to_id_file_name = os.path.join(index_dir, "url_to_id")
        # open files
        inverted_index_file = open(inverted_index_file_name, "w")
        forward_index_file = open(forward_index_file_name, "w")
        url_to_id_file = open(url_to_id_file_name, "w")
        # save to disk in appropriate JSON files
        json.dump(self.inverted_index, inverted_index_file, indent=6)
        json.dump(self.forward_index, forward_index_file, indent=6)
        json.dump(self.url_to_id, url_to_id_file, indent=6)


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


def main():
    # get arguments
    parser = argparse.ArgumentParser(description="Index /r/{your subreddit}")
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
