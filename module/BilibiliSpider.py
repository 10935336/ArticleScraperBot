#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Bilibili designated authors crawl articles and videos
# Author: 10935336
# Creation date: 2023-04-23
# Modified date: 2023-05-06

import json
import logging
import os
from datetime import datetime

import requests


class BilibiliSpider:

    def __init__(self):
        self.videos_json = ''
        self.articles_json = ''
        self.authors_list = []
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_videos_list(self, contents_num="25", sourt_by="publish_time"):
        # Waring contents_num cannot to be too big, or the stupid bilibili api will return incomplete json
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://api.bilibili.com/x/space/wbi/arc/search?" + "mid=" + author_id_l \
                      + "&ps=" + contents_num + "&sort=" + sourt_by + '&pn=' + '1' + '&index=' + '1'

                response = requests.get(url=url, headers=self.headers)

                if response.status_code == 200:

                    raw_json_unescaped = json.loads(response.text)

                    # Stupid api design
                    if raw_json_unescaped['code'] == "-404" or raw_json_unescaped[
                        'code'] == "404" or not raw_json_unescaped.get('data', {}).get('list', {}).get('vlist'):
                        # User has no videos
                        new_list.append(
                            {
                                "title": None,
                                "article_id": "0",
                                "author_id": author_id_l,
                                "author_name": author_name_l,
                                "channel_name": "哔哩哔哩视频",
                                "link": None,
                                "creation_time": "0",
                                "snapshot_time": str(current_time)
                            }
                        )

                    else:
                        # User has videos
                        for item in raw_json_unescaped['data']['list']['vlist']:
                            title = item['title']
                            creation_time = item['created']
                            link = "https://www.bilibili.com/video/av" + str(item['aid']) + "/"

                            new_list.append(
                                {
                                    "title": title,
                                    "article_id": str(item['bvid']),
                                    "author_id": author_id_l,
                                    "author_name": author_name_l,
                                    "channel_name": "哔哩哔哩视频",
                                    "link": link,
                                    "creation_time": str(creation_time),
                                    "snapshot_time": str(current_time)
                                }
                            )

                self.videos_json = json.dumps(new_list, ensure_ascii=False)

        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")

    def get_articles_list(self, contents_num="30", sourt_by="publish_time"):
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://api.bilibili.com/x/space/wbi/article?" + "mid=" + author_id_l + "&ps=" + contents_num + "&sort=" + sourt_by

                response = requests.get(url=url, headers=self.headers)

                if response.status_code == 200:

                    raw_json_unescaped = json.loads(response.text)

                    # Stupid api design
                    if raw_json_unescaped.get('data', {}).get('articles'):
                        # User has articles
                        for item in raw_json_unescaped['data']['articles']:
                            title = item['title']
                            creation_time = item['publish_time']
                            link = "https://www.bilibili.com/read/cv" + str(item['id'])

                            new_list.append(
                                {
                                    "title": title,
                                    "article_id": str(item['id']),
                                    "author_id": author_id_l,
                                    "author_name": author_name_l,
                                    "channel_name": "哔哩哔哩文章",
                                    "link": link,
                                    "creation_time": str(creation_time),
                                    "snapshot_time": str(current_time)
                                }
                            )
                    else:
                        # User has no articles
                        new_list.append(
                            {
                                "title": None,
                                "article_id": '0',
                                "author_id": author_id_l,
                                "author_name": author_name_l,
                                "channel_name": "哔哩哔哩文章",
                                "link": None,
                                "creation_time": "0",
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)
        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def combine_video_and_articles(self):
        try:
            self.articles_json = json.dumps(json.loads(self.articles_json) + json.loads(self.videos_json),
                                        ensure_ascii=False)
        except Exception as error:
            logging.exception(f"Error in combine video and articles list: {error}")
            self.articles_json = []

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'bilibili_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_videos_list()
        self.get_articles_list()
        self.combine_video_and_articles()
