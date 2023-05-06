#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Tencent self-media designated authors crawl articles
# Author: 10935336
# Creation date: 2023-04-22
# Modified date: 2023-05-06

import json
import logging
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

    def get_articles_list(self, contents_num="15", page='0'):
        # The content_num value is preferably 15, otherwise the subsequent posts may not be filled in order
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            # Check if the author list has mkey, if not, add it
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://pacaio.match.qq.com/om/mediaArticles?mid=" + author_id_l + "&num=" + contents_num + '&page=' + page + '&expIds='

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
                                "author_id": author_id_l,
                                "author_name": author_name_l,
                                "channel_name": "腾讯新闻",
                                "link": link,
                                "creation_time": str(creation_time),
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)

        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path="./conf/tencentnewsselfmedia_authors_list.json"):
        self.load_authors(authors_list_path)
        self.get_articles_list()
