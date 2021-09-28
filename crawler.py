import requests
from datetime import datetime
import time
import json
import os.path
from base64 import b64encode
import argparse


class RedditCrawler(object):

    def __init__(self, subreddit, storage_dir):
        # start url is which url we start crawl from
        self.start_url = "subreddit=" + subreddit
        # directory we write all crawled data to
        self.storage_dir = storage_dir
        # try to create a directory
        try:
            os.mkdir(storage_dir)
        except FileExistsError:
            print("Folder is already created")
            exit()

    # crawl function to crawl given subreddit
    def crawl(self, num_of_posts):
        # time variables used for pushshift reddit API
        start_time = datetime.utcnow()
        previous_epoch = int(start_time.timestamp())
        # url to use pushshift API
        url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&{}&before="
        # number of crawled data
        count = 0

        # crawl num_of_posts times
        for i in range(0, int(num_of_posts / 100)):
            # api request
            new_url = url.format("submission", self.start_url) + str(previous_epoch)
            json_text = requests.get(new_url, headers={'User-Agent': "Surfearch"})
            # pushshift has a rate limit, if we send requests too fast it will start returning error messages
            time.sleep(1)
            # get data from http request
            try:
                json_data = json_text.json()
            except json.decoder.JSONDecodeError:
                time.sleep(1)
                continue
            # check if we got data
            if 'data' not in json_data:
                break
            # get data from json
            objects = json_data['data']
            # if we did not get data
            if len(objects) == 0:
                # if it was the first loop then subreddit does not exist
                if i == 0:
                    os.rmdir(self.storage_dir)
                    raise SyntaxError("Subreddit does not exist")
                # data has run out
                else:
                    break
            # loop through all data we got
            for data in objects:
                # update time variables appropriately
                previous_epoch = data['created_utc'] - 1
                count += 1
                # get data from post on subreddit
                title = data['title']
                try:
                    description = data['selftext']
                except Exception:
                    description = ""
                data_to_write = title + "\n\n\n" + description
                link = data['full_link']
                # write data from post to file with name of 64encoded link
                stored_text_file_name = os.path.join(self.storage_dir,
                                                     str(b64encode(link.encode("utf-8")).decode("utf-8")))
                with open(stored_text_file_name, "w", encoding="utf-8") as stored_text_file:
                    stored_text_file.write(data_to_write)
                print("Crawled: {:.2f}%".format((count / num_of_posts) * 100))

        print("Success crawled: " + str(count))


def main():
    # get arguments
    parser = argparse.ArgumentParser(description="Crawl /r/{your subreddit}")
    parser.add_argument("r")
    parser.add_argument("storage_dir")
    parser.add_argument("count_of_crawl")
    args = parser.parse_args()
    print("Crawling subreddit: " + args.r)
    print("to folder: " + args.storage_dir)
    print("Amount of expected crawled data: " + args.count_of_crawl)
    crawler = RedditCrawler(args.r, args.storage_dir)
    # crawl
    try:
        crawler.crawl(int(args.count_of_crawl))
    except ValueError:
        print("Third Argument is not an integer")
        exit()
    except SyntaxError as error:
        print(error)


if __name__ == "__main__":
    main()
