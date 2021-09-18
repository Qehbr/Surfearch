import requests
from datetime import datetime
import time
import json
import sys

subreddit = "learnprogramming"
filter_string = None
if subreddit == "":
    print("Fill in subreddit")
    sys.exit(0)
else:
    filter_string = "subreddit="+subreddit

url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&{}&before="

start_time = datetime.utcnow()


def crawl():
    print("Saving submissions")
    count = 0
    data = []
    previous_epoch = int(start_time.timestamp())
    for i in range(0, 2):
        print("CURRENT i is " + str(i) + " CURRENT count is " + str(count))
        new_url = url.format("submission", filter_string) + str(previous_epoch)
        print("new url is " + new_url)
        json_text = requests.get(new_url, headers={'User-Agent': "Surfearch"})
        time.sleep(1)  # pushshift has a rate limit, if we send requests too fast it will start returning error messages
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
        for object in objects:
            previous_epoch = object['created_utc'] - 1
            count += 1
            try:
                description = object['selftext']
            except Exception:
                description = ""
            # print(object)
            result = {
                'title': object['title'],
                'description': description.strip().replace('\n', ' ')
            }
            data.append(result)
    print("SUCCESS")
    return data


data = crawl()
for object in data:
    print(object)
print(len(data))