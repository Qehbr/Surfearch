import argparse
import json
import os.path

from joblib.numpy_pickle_utils import xrange
from progressbar import ProgressBar, Percentage, Bar, RotatingMarker
from lang_proc import to_doc_terms
import shelve
from document import Document


class ShelveIndexes(object):
    def __init__(self):
        self.inverted_index = None
        self.forward_index = None
        self.url_to_id = None
        self.doc_count = 0
        self.block_count = 0
        self.index_dir = ""  # TODO
        self._doc_count = 0
        self._avgdl = 0

    def total_doc_count(self):
        return self._doc_count

    def average_doc_len(self):
        return self._avgdl

    def save_on_disk(self):
        self.inverted_index.close()
        self.forward_index.close()
        self.url_to_id.close()
        self._merge_blocks()  # TODO

    def load_from_disk(self, index_dir):
        self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"))
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"))
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"))

        self._doc_count = 0
        total_word_count = 0
        for (docid, text) in self.forward_index.items():
            self._doc_count += 1
            total_word_count += len(text.text)
        self._avgdl = total_word_count / self._doc_count
        print("LOADED!")

    def start_indexing(self, index_dir):
        # TODO self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"), "n", writeback=True)
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"), "n", writeback=True)
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"), "n", writeback=True)
        self.index_dir = index_dir  # TODO

    # TODO
    def sync(self):
        self.inverted_index.sync()
        self.forward_index.sync()
        self.url_to_id.sync()

    # TODO
    def _merge_blocks(self):
        print("Merging blocks!")
        blocks = [shelve.open(os.path.join(self.index_dir, "inverted_index_block{}".format(i))) for i in
                  xrange(self.block_count)]
        keys = set()
        for block in blocks:
            keys |= set(block.keys())
        print("Total word count", len(keys))
        merged_index = shelve.open(os.path.join(self.index_dir, "inverted_index"), "n")
        key_ind = 0
        for key in keys:
            key_ind += 1
            print("MERGING", key_ind, key)
            merged_index[key] = sum([block.get(key, []) for block in blocks], [])
        merged_index.close()

    # TODO
    def _create_new_ii_block(self):
        print("Created a new block!")
        if self.inverted_index:
            self.inverted_index.close()
        self.inverted_index = shelve.open(
            os.path.join(self.index_dir, "inverted_index_block{}".format(self.block_count)), "n", writeback=True)
        self.block_count += 1

    def add_document(self, doc):
        if self.doc_count % 200 == 0:
            self._create_new_ii_block()  # TODO
        self.doc_count += 1
        assert doc.url not in self.url_to_id
        self.url_to_id[doc.url] = self.doc_count
        # update forward index
        self.forward_index[str(self.doc_count)] = doc
        # update inverted index
        for position, term in enumerate(doc.text):
            if term.is_stop_word():
                continue
            stem = term.stem
            # postings_list = self.inverted_index[stem] if stem in self.inverted_index else []
            # postings_list.append((position, self.doc_count))
            # self.inverted_index[stem] = postings_list
            if stem not in self.inverted_index:
                self.inverted_index[stem] = []
            self.inverted_index[stem].append((position, self.doc_count))

    def get_documents(self, query_term):
        return self.inverted_index.get(query_term.stem, [])

    def get_document_text(self, doc_id):
        return self.forward_index[str(doc_id)].text

    def get_document_score(self, doc_id):
        if self.forward_index[str(doc_id)].score > 2:
            print("HI")
        return self.forward_index[str(doc_id)].score

    def get_url(self, doc_id):
        return self.forward_index[str(doc_id)].url

    def get_title(self, doc_id):
        return self.forward_index[str(doc_id)].title


def create_index_from_dir(crawled_data_dir, index_directory, IndexesImplementation=ShelveIndexes):
    indexer = IndexesImplementation()
    indexer.start_indexing(index_directory)
    # progress bar
    filenames = [name for name in os.listdir(crawled_data_dir)]
    # widgets = [' Indexing: ', Percentage(), ' ', Bar(marker=RotatingMarker())]
    indexed_docs_num = 0
    # progressbar = ProgressBar(widgets=widgets, maxval=len(filenames))
    # progressbar.start()
    # loop through each file in crawled_data
    for filename in os.listdir(crawled_data_dir):
        indexed_docs_num += 1
        # progressbar.update(indexed_docs_num)
        # open and read file
        file_to_open = os.path.join(crawled_data_dir, filename)
        with open(file_to_open, encoding="utf-8") as doc:
            json_doc = json.load(doc)
        # get data about document
        doc_title = json_doc["title"]
        doc_text = to_doc_terms(json_doc["text"])
        doc_url = json_doc["url"]
        doc_score = json_doc["score"]
        # create new document
        new_document = Document(doc_title, doc_text, doc_url, int(doc_score))
        print(indexed_docs_num)
        if indexed_docs_num % 100 == 0:  # TODO
            print(indexed_docs_num, "Syncing...")
            indexer.sync()
            print(indexed_docs_num, "Synced!")
        # add it to indexer
        indexer.add_document(new_document)
        # progressbar.update(indexed_docs_num)
        # save indexes on disk in JSON file
    indexer.save_on_disk()


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
