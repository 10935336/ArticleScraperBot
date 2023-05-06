#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Sina Weibo designated authors crawl articles
# Note: Use the mobile version page to obtain the uid,
# such as https://weibo.com/sinapapers to https://m.weibo.cn/u/2028810631.
# m.weibo.com has almost no authentication, but weibo.com is very strict.
# Author: 10935336
# Creation date: 2023-04-24
# Modified date: 2023-05-06

import json
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class SinaWeiboSpider:
    def __init__(self):
        self.articles_json = ''
        self.authors_list = []
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 13.0; Nexus 15 Build/MRA99N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self, uid='uid', containerid='107603'):
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

                # containerid consists of prefix + uid, and the prefix may change.
                url = 'https://m.weibo.cn/api/container/getIndex?' + "type=" + uid \
                      + "&value=" + author_id_l + "&containerid=" + str(
                    containerid) + str(author_id_l)

                response = requests.get(url=url, headers=self.headers)
                if response.status_code == 200:

                    raw_json_unescaped = json.loads(response.text)

                    # Iterate through the list in the raw JSON data
                    for item in raw_json_unescaped['data']['cards']:
                        article_id = item['mblog']['id']

                        # remove html tags
                        soup = BeautifulSoup(item['mblog']['text'], 'html.parser')
                        text = soup.get_text()

                        # PC link
                        link = "https://weibo.com/" + author_id_l + "/" + item['mblog']['bid']

                        # time
                        datetime_obj = datetime.strptime(item['mblog']['created_at'], "%a %b %d %H:%M:%S +0800 %Y")
                        timestamp = int(datetime_obj.timestamp())

                        new_list.append(
                            {
                                "title": text,
                                "article_id": article_id,
                                "author_id": author_id_l,
                                "author_name": author_name_l,
                                "channel_name": "新浪微博",
                                "link": link,
                                "creation_time": str(timestamp),
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)
        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path="./conf/sinaweibo_authors_list.json"):
        self.load_authors(authors_list_path)
        self.get_articles_list()
