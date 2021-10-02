# Surfearch
Reddit post searcher with given subreddit

!Heroky deployment is not working!

Usage:
0. Make sure to install nltk libraries! (You will see what you should install when trying to use scripts)

1. Use crawler.py for crawling your subreddit with arguments
    --r - Subreddit to crawl
    --storage_dir Directory to store posts
    --count_of_crawl Number of crawled posts
    It's safe to use storage_dir: crawled_data

2. Now, use indexer.py for data you crawled in 1. with arguments
    --crawled_data - Crawled data directory
    --index_dir - Index directory
    It's safe to use crawled_data: crawled_data, index_dir: indexes

3. Finally, use web_ui.api and you can search for given query in data you crawled (Available with non-fancy design :))
