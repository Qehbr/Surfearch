import argparse
import json
import os.path
from joblib.numpy_pickle_utils import xrange
from lang_proc import to_doc_terms
import shelve
from document import Document


# class used for indexing using shelves
class ShelveIndexes(object):
    def __init__(self):
        # creating shelves
        self.inverted_index = None
        self.forward_index = None
        self.url_to_id = None
        # initialize class variables
        self.doc_count = 0
        self.block_count = 0
        self.index_dir = ""
        self._doc_count = 0
        self._avgdl = 0

    # total number of docs
    def total_doc_count(self):
        return self._doc_count

    # average length of docs (used in bm25 ranking)
    def average_doc_len(self):
        return self._avgdl

    # saving indexes on disk
    def save_on_disk(self):
        self.inverted_index.close()
        self.forward_index.close()
        self.url_to_id.close()
        self._merge_blocks()

    # loading indexes from disk
    def load_from_disk(self, index_dir):
        self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"))
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"))
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"))

        # count variables used for mb25 ranking
        self._doc_count = 0
        total_word_count = 0
        for (docid, text) in self.forward_index.items():
            self._doc_count += 1
            total_word_count += len(text.text)
        self._avgdl = total_word_count / self._doc_count

    # index all indexes
    def start_indexing(self, index_dir):
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"), "n", writeback=True)
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"), "n", writeback=True)
        # update index directory
        self.index_dir = index_dir

    # sync indexes
    def sync(self):
        self.inverted_index.sync()
        self.forward_index.sync()
        self.url_to_id.sync()

    # merge block of inverted (merged) index
    def _merge_blocks(self):
        # get blocks
        blocks = [shelve.open(os.path.join(self.index_dir, "inverted_index_block{}".format(i))) for i in
                  xrange(self.block_count)]
        keys = set()
        for block in blocks:
            keys |= set(block.keys())
        # open merged index
        merged_index = shelve.open(os.path.join(self.index_dir, "inverted_index"), "n")
        key_ind = 0
        # for each key update merged index
        for key in keys:
            key_ind += 1
            merged_index[key] = sum([block.get(key, []) for block in blocks], [])
        # save merged index
        merged_index.close()

    # create a new block of data if needed
    def _create_new_ii_block(self):
        # save old inverted index
        if self.inverted_index:
            self.inverted_index.close()
        # create new inverted index with new block
        self.inverted_index = shelve.open(
            os.path.join(self.index_dir, "inverted_index_block{}".format(self.block_count)), "n", writeback=True)
        # update block count
        self.block_count += 1

    def add_document(self, doc):
        # create new block if needed (per 200)
        if self.doc_count % 200 == 0:
            self._create_new_ii_block()
        self.doc_count += 1
        # check if doc was already added
        assert doc.url not in self.url_to_id
        # update url to id
        self.url_to_id[doc.url] = self.doc_count
        # update forward index
        self.forward_index[str(self.doc_count)] = doc
        # update inverted index
        for position, term in enumerate(doc.text):
            # check if stop word
            if term.is_stop_word():
                continue
            # update by stem!
            stem = term.stem
            if stem not in self.inverted_index:
                self.inverted_index[stem] = []
            self.inverted_index[stem].append((position, self.doc_count))

    # getters
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


# create indexes function
def create_index_from_dir(crawled_data_dir, index_directory, IndexesImplementation=ShelveIndexes):
    indexer = IndexesImplementation()
    # start indexing
    indexer.start_indexing(index_directory)
    indexed_docs_num = 0
    # loop through each file in crawled_data
    for filename in os.listdir(crawled_data_dir):
        indexed_docs_num += 1
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
        # sync if needed
        if indexed_docs_num % 100 == 0:
            indexer.sync()
        # add it to indexer
        indexer.add_document(new_document)
    # save indexes on disk in JSON file
    indexer.save_on_disk()


def main():
    # get arguments
    parser = argparse.ArgumentParser(description="Index /r/{your subreddit}")
    parser.add_argument("--crawled_data", dest="crawled_data", required=True, help="Crawled data directory")
    parser.add_argument("--index_dir", dest="index_dir", required=True, help="Index directory")
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
