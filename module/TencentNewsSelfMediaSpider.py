#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Tencent self-media designated authors crawl articles
# Author: 10935336
# Creation date: 2023-04-22
# Modified date: 2023-05-19

import json
import logging
import os
from datetime import datetime

import requests


class TencentNewsSelfMediaSpider:
    def __init__(self):
        self.authors_list = []
        self.articles_json = ''
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self, retry_times=3, contents_num="15", page='0'):
        # The content_num value is preferably 15, otherwise the subsequent posts may not be filled in order
        new_list = []
        current_time = int(datetime.now().timestamp())

        for retry in range(retry_times):
            try:
                # Check if the author list has mkey, if not, add it
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    url = "https://pacaio.match.qq.com/om/mediaArticles?" + \
                          "mid=" + author_id_l + \
                          "&num=" + contents_num + \
                          "&page=" + page + \
                          "&expIds="

                    response = requests.get(url=url, headers=self.headers)
                    if response.status_code == 200:

                        raw_json_unescaped = json.loads(response.text)

                        # Iterate through the list in the raw JSON data
                        for item in raw_json_unescaped['data']:
                            title = item['title']
                            link = item['vurl']
                            creation_time = item['timestamp']
                            article_id = item['id']

                            new_list.append(
                                {
                                    "title": title,
                                    "article_id": article_id,
                                    "author_name": author_name_l,
                                    "author_id": author_id_l,
                                    "channel_name": "腾讯新闻",
                                    "link": link,
                                    "creation_time": str(creation_time),
                                    "snapshot_time": str(current_time)
                                }
                            )

                    self.articles_json = json.dumps(new_list, ensure_ascii=False)
                    # break on success
                    if self.articles_json:
                        break

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
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'tencentnewsselfmedia_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    tx = TencentNewsSelfMediaSpider()
    tx.start()
    print(tx.articles_json)
