#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Medium designated authors crawl articles
# Author: 10935336
# Creation date: 2023-05-28
# Modified date: 2023-05-28

import json
import logging
import os
from datetime import datetime

import dateparser
import requests
from bs4 import BeautifulSoup


class MediumSpider:
    def __init__(self):
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        }
        self.authors_list = []
        self.articles_json = ''

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self, retry_times=3):
        new_list = []
        current_time = int(datetime.now().timestamp())

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    # read author
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    url = "https://medium.com/@" + author_id_l

                    response = requests.get(url=url, headers=self.headers)
                    if response.status_code == 200:
                        result = response.content.decode("utf-8")
                        soup = BeautifulSoup(result, 'html.parser')

                        articles = soup.find_all('article')
                        for article in articles:
                            title = article.find('h2').text

                            link = article.find('a', {'aria-label': 'Post Preview Title'})['href']
                            url_without_query = link.split('?')[0]
                            full_url = url + url_without_query

                            article_id = url_without_query.split('/')[-1]

                            time_str = article.find('p', {'class': 'be b bf z dl'}).text
                            dt = dateparser.parse(time_str)
                            timestamp = int(dt.timestamp())


                            new_list.append(
                                {
                                    'title': title,
                                    "article_id": article_id,
                                    "author_name": author_name_l,
                                    "author_id": author_id_l,
                                    "channel_name": "Medium",
                                    'link': full_url,
                                    "creation_time": str(timestamp),
                                    "snapshot_time": str(current_time)
                                }
                            )

                        self.articles_json = json.dumps(new_list, ensure_ascii=False)
                        # break on success
                        if self.articles_json:
                            break

                    else:
                        logging.exception(f"Get response error in {url}")

            except Exception as error:
                logging.exception(f"Error getting or parsing the response: {error}")
                self.articles_json = []

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.articles_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'medium_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    me = MediumSpider()
    me.start()
    print(me.articles_json)
