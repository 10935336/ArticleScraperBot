#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: NetEase self-media designated authors crawl articles
# Author: 10935336
# Creation date: 2023-04-21
# Modified date: 2023-05-11

import json
import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class NetEaseNewsSelfMediaSpider:
    def __init__(self):
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }
        self.authors_list = []
        self.articles_json = ''

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self):

        new_list = []
        time_format = '%Y-%m-%d %H:%M'
        current_time = int(datetime.now().timestamp())

        try:
            for author in self.authors_list:
                # read author
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://www.163.com/dy/media/" + author_id_l + ".html"

                response = requests.get(url=url, headers=self.headers)
                if response.status_code == 200:
                    result = response.content.decode("utf-8")
                    soup = BeautifulSoup(result, 'html.parser')

                    # exclude sidebar
                    container = soup.find('div', {'class': 'content_left tab_wrap js-list-tab-box'})
                    for element in container.find_all('a', {'class': 'title'}):
                        link = element.get('href')
                        title = element.text
                        time_str = element.find_parent('h4').find_next_sibling('div', {'class': 'tail'}).find('span', {
                            'class': 'time'}).text

                        article_id_match = re.search(r'/(?:video|article)/([A-Z0-9]+)', link)
                        if article_id_match:
                            article_id = article_id_match.group(1)
                        else:
                            article_id = "0"

                        dt = datetime.strptime(time_str, time_format)
                        timestamp = int(dt.timestamp())

                        new_list.append(
                            {
                                'title': title,
                                "article_id": article_id,
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "网易新闻",
                                'link': link,
                                "creation_time": str(timestamp),
                                "snapshot_time": str(current_time)
                            }
                        )

                    self.articles_json = json.dumps(new_list, ensure_ascii=False)

                else:
                    logging.exception(f"Get response error in {url}")

        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'neteasenewsselfmedia_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    wy = NetEaseNewsSelfMediaSpider()
    wy.start()
    print(wy.articles_json)