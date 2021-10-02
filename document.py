# Document class storing its title, text, url and score on reddit
class Document(object):
    def __init__(self, title, text, url, score):
        self.title = title
        self.text = text
        self.url = url
        self.score = score

    def __eq__(self, other):
        return self.url == other.url
