import requests
from bs4 import BeautifulSoup
import json

url = 'http://www.reddit.com/r/learnprogramming/comments/ppu8cc/10_year_uiux_developer_fails_another_code/'
start_url='http://www.reddit.com/r/learnprogramming/'

def donwloadRedditToJson(url):
    assert url.startswith('http://www.reddit.com/r/learnprogramming/')
    response = requests.get(url+'.json', headers={'User-agent': 'Search Reddit Bot v0.1'})
    if response.status_code != 200:
        raise Exception("Error status code: {}".format(response.status_code))
    content = BeautifulSoup(response.text, 'lxml').text
    # TODO verify is this zero
    return json.loads(content)[0]['data']['children'][0]['data']


def parseText(redditJson):
    # print(redditJson['selftext'])
    # print(redditJson['title'])
    return redditJson['selftext']


def parsePage(url):
    response = requests.get(url, headers={'User-agent': 'Search Reddit Bot v0.1'})
    content = BeautifulSoup(response.text, 'lxml')


# data = donwloadRedditToJson(url)
# print(parseText(data))




