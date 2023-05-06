#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Sohu self-media designated authors crawl articles
# Author: 10935336
# Creation date: 2023-04-22
# Modified date: 2023-05-05

import json
import logging
import re
from datetime import datetime

import requests


class SohuNewsSelfMediaSpider:
    def __init__(self):
        self.articles_json = ''
        self.authors_list = []
        self.articles_json = ''
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
        }

        self.post_data = ''

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def fill_mkey_for_authors_list(self, authors_list_path=r".\conf\sohonewsselfmedia_authors_list.json",
                                   write_back=True):

        def get_mkey_by_id(author_id_l):
            # Get the mkey from the author's homepage
            url = "https://mp.sohu.com/profile?xpt=" + author_id_l
            try:
                response = requests.get(url=url, headers=self.headers)
                content = response.text
                if response.status_code == 200:
                    mkey_pattern = re.compile(r'mkey:([0-9]+)')
                    mkey_match = mkey_pattern.search(content)
                    if mkey_match:
                        mkey_value = mkey_match.group(1)
                        if mkey_value is None:
                            logging.exception("Cannot get mkey")
                        else:
                            return mkey_value
                    else:
                        logging.exception('mkey value not found')
                else:
                    logging.exception("Get response error")
            except Exception as error:
                logging.exception(f'Cannot get mkey: {error}')

        def write_meky_back_to_list(authors_list_path):
            try:
                with open(authors_list_path, 'w', encoding='utf-8') as w:
                    json.dump(self.authors_list, w, ensure_ascii=False)
            except Exception as error:
                logging.exception(f'{authors_list_path} write error: {error}')

        try:
            # Check if the author list has mkey, if not, add it
            for item in self.authors_list:
                if 'author_mkey' not in item:
                    author_id = item['author_id']
                    mkey_value = get_mkey_by_id(author_id)
                    item['author_mkey'] = mkey_value
        except Exception as error:
            logging.exception(f'Get author_id error: {error}')

        if write_back:
            write_meky_back_to_list(authors_list_path)

    def get_articles_list(self, contents_num="50"):
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for item in self.authors_list:
                if 'author_mkey' not in item:
                    self.fill_mkey_for_authors_list()
        except Exception as error:
            logging.exception(f'Get mkey error: {error}')

        try:
            # Check if the author list has mkey, if not, add it
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                    author_mkey_l = author['author_mkey']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                # The specific value of all the values that are 0 does not matter,
                # but cannot be deleted, resourceId affects the header of the returned json.
                self.post_data = json.dumps({
                    "suv": "0", "pvId": "0", "clientType": 3, "resourceParam":
                        [{"page": 1, "size": contents_num,
                          "spm": "0", "resourceId": "10935",
                          "context": {"pro": "0", "feedType": "0", "mkey": author_mkey_l},
                          "resProductParam": {"productId": 0, "productType": 0},
                          "productParam": {"productId": 325, "productType": 13, "categoryId": 0, "mediaId": 0}
                          }]
                })

                response = requests.post(url="https://cis.sohu.com/cisv4/feeds", headers=self.headers,
                                         data=self.post_data)
                if response.status_code == 200:

                    raw_json_unescaped = json.loads(response.text)

                    # Iterate through the list in the raw JSON data
                    for key in raw_json_unescaped:
                        for item in raw_json_unescaped[key]['data']:
                            title = item['resourceData']['contentData']['title']
                            # millisecond timestamp
                            creation_time = item['resourceData']['contentData']['postTime'] / 1000
                            link = "https://www.sohu.com" + item['resourceData']['contentData']['url']
                            article_id = item['resourceData']['contentData']['id']
                            # author_id = item['resourceData']['contentData']['authorId']

                            new_list.append(
                                {
                                    "title": title,
                                    "article_id": str(article_id),
                                    "author_id": author_id_l,
                                    "author_name": author_name_l,
                                    "channel_name": "搜狐新闻",
                                    "link": link,
                                    "creation_time": str(int(creation_time)),
                                    "snapshot_time": str(current_time)
                                }
                            )

                    self.articles_json = json.dumps(new_list, ensure_ascii=False)
        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path=r".\conf\sohonewsselfmedia_authors_list.json"):
        self.load_authors(authors_list_path)
        self.get_articles_list()
