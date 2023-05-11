#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Bilibili designated authors crawl articles and videos
# Author: 10935336
# Creation date: 2023-04-26
# Modified date: 2023-05-11

import json
import logging
import os
import re
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup


class BaiduTiebaSpider:

    def __init__(self):
        self.articles_json = ''
        self.authors_list = []
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        }

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self):
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://tieba.baidu.com/home/main?" + "id=" + author_id_l

                response = requests.get(url=url, headers=self.headers)

                if response.status_code == 200:
                    result = response.content.decode("utf-8")
                    soup = BeautifulSoup(result, 'html.parser')

                    elements = soup.find_all('div', {'class': 'thread_name'})

                    for element in elements:
                        title = element.find('a')['title']
                        link = "https://tieba.baidu.com" + element.find('a')['href']
                        bar_name = element.find('a').find_next_sibling('a').text

                        article_id_match = re.search(r'/p/(\d+)', link)
                        if article_id_match:
                            article_id = article_id_match.group(1)
                        else:
                            article_id = None

                        post_time_text = soup.find('div', {'class': 'n_post_time'}).text

                        # two type of time
                        try:
                            post_time = datetime.strptime(post_time_text, '%Y-%m-%d')
                            creation_time = int(post_time.timestamp())
                        except ValueError:
                            post_time = datetime.strptime(post_time_text, '%H:%M').time()
                            # Date converted to today, not 1900-1-1
                            post_datetime = datetime.combine(date.today(), post_time)
                            creation_time = int(post_datetime.timestamp())

                        new_list.append(
                            {
                                "title": title,
                                "article_id": article_id,
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "百度贴吧" + '-' + bar_name,
                                "link": link,
                                "creation_time": str(creation_time),
                                "snapshot_time": str(current_time)
                            }
                        )

                    self.articles_json = json.dumps(new_list, ensure_ascii=False)

        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'baidutieba_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()

if __name__ == "__main__":
    tb = BaiduTiebaSpider()
    tb.start()
    print(tb.articles_json)