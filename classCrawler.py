import requests
from datetime import datetime
import time
import json
import sys
import os.path
from base64 import b64encode


class RedditCrawler(object):
    # crawled_data = []

    def __init__(self, subreddit, storage_dir):
        if subreddit == "":
            print("Fill in subreddit")
            sys.exit(0)
        self.start_url = "subreddit=" + subreddit
        self.storage_dir = storage_dir
        os.mkdir(storage_dir)

    def crawl(self, num_of_posts):
        start_time = datetime.utcnow()
        url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&{}&before="
        print("Saving submissions")
        count = 0
        previous_epoch = int(start_time.timestamp())

        for i in range(0, int(num_of_posts / 100)):
            new_url = url.format("submission", self.start_url) + str(previous_epoch)
            print("new url is " + new_url)
            json_text = requests.get(new_url, headers={'User-Agent': "Surfearch"})
            # pushshift has a rate limit, if we send requests too fast it will start returning error messages
            time.sleep(1)
            try:
                json_data = json_text.json()
            except json.decoder.JSONDecodeError:
                time.sleep(1)
                continue
            if 'data' not in json_data:
                break
            objects = json_data['data']
            if len(objects) == 0:
                break
            for data in objects:
                previous_epoch = data['created_utc'] - 1
                count += 1
                title = data['title']
                try:
                    description = data['selftext']
                except Exception:
                    description = ""

                data_to_write = title + "\n\n\n" + description
                link = data['full_link']
                stored_text_file_name = os.path.join(self.storage_dir,
                                                     str(b64encode(link.encode("utf-8")).decode("utf-8")))
                print(stored_text_file_name)
                with open(stored_text_file_name, "w", encoding="utf-8") as stored_text_file:
                    stored_text_file.write(data_to_write)

        print("SUCCESS")


crawler = RedditCrawler("learnprogramming", "crawled_urls")
crawler.crawl(100)
# for obj in crawler.crawled_data:
#     print(obj)
# print("Number of crawled data is: " + str(len(crawler.crawled_data)))
