import requests
from bs4 import BeautifulSoup
import json

url = 'https://www.reddit.com/r/learnprogramming/comments/ppu8cc/10_year_uiux_developer_fails_another_code/.json'


def donwloadRedditToJson(url):
    response = requests.get(url, headers={'User-agent': 'botick_0.1'})
    if response.status_code != 200:
        raise Exception("Error status code: {}".format(response.status_code))
    content = BeautifulSoup(response.text, 'lxml').text
    # TODO verify is this zero
    return json.loads(content)[0]['data']['children'][0]['data']


def parseText(redditJson):
    # print(redditJson['selftext'])
    # print(redditJson['title'])
    return redditJson['selftext']

data = donwloadRedditToJson(url)
print(parseText(data))
