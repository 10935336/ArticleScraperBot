#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Bilibili designated authors crawl articles and videos
# Author: 10935336
# Creation date: 2023-04-23
# Modified date: 2023-05-29

import json
import logging
import os
import time
import urllib.parse
from datetime import datetime
from functools import reduce
from hashlib import md5

import requests


class BilibiliSpider:
    def __init__(self):
        self.videos_json = ''
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

    def get_signed_parameters(self, parameters: dict):
        """
        Copy from https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/sign/wbi.md
        Refer https://github.com/SocialSisterYi/bilibili-API-collect/issues/631#issuecomment-1558747661
        """
        mixinKeyEncTab = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
            33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
            61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
            36, 20, 34, 44, 52
        ]

        def getMixinKey(orig: str):
            '对 imgKey 和 subKey 进行字符顺序打乱编码'
            return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

        def encWbi(params: dict, img_key: str, sub_key: str):
            '为请求参数进行 wbi 签名'
            mixin_key = getMixinKey(img_key + sub_key)
            curr_time = round(time.time())
            params['wts'] = curr_time  # 添加 wts 字段
            params = dict(sorted(params.items()))  # 按照 key 重排参数
            # 过滤 value 中的 "!'()*" 字符
            params = {
                k: ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
                for k, v
                in params.items()
            }
            query = urllib.parse.urlencode(params)  # 序列化参数
            wbi_sign = md5((query + mixin_key).encode()).hexdigest()  # 计算 w_rid
            params['w_rid'] = wbi_sign
            return params

        def getWbiKeys():
            '获取最新的 img_key 和 sub_key'
            resp = requests.get('https://api.bilibili.com/x/web-interface/nav')
            resp.raise_for_status()
            json_content = resp.json()
            img_url: str = json_content['data']['wbi_img']['img_url']
            sub_url: str = json_content['data']['wbi_img']['sub_url']
            img_key = img_url.rsplit('/', 1)[1].split('.')[0]
            sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
            return img_key, sub_key

        def get_query(parameters: dict):
            """
            获取签名后的查询参数
            """
            img_key, sub_key = getWbiKeys()
            signed_params = encWbi(
                params=parameters,
                img_key=img_key,
                sub_key=sub_key
            )
            query = urllib.parse.urlencode(signed_params)
            return query

        return get_query(parameters)

    def get_videos_list(self, retry_times=3, contents_num="20", sourt_by="publish_time"):
        # Waring contents_num cannot to be too big, or the stupid api will return incomplete json
        new_list = []
        current_time = int(datetime.now().timestamp())

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    raw_parameter = {
                        "mid": author_id_l,
                        "ps": contents_num,
                        "sort": sourt_by,
                        "pn": 1,
                        "index": 1
                    }

                    # anti anti crawl
                    signed_parameter = self.get_signed_parameters(raw_parameter)

                    url = "https://api.bilibili.com/x/space/wbi/arc/search?" + signed_parameter

                    response = requests.get(url=url, headers=self.headers)

                    if response.status_code == 200:
                        raw_json_unescaped = json.loads(response.text)

                        # Bilibili’s risk control has been strengthened, sometimes you will get -403 in JSON;
                        # retry 5 times
                        max_attempts = 5
                        attempts = 0
                        while raw_json_unescaped['code'] == -403 and attempts < max_attempts:
                            time.sleep(5)

                            response = requests.get(url=url, headers=self.headers)
                            raw_json_unescaped = json.loads(response.text)
                            attempts += 1

                            if raw_json_unescaped['code'] == -403:
                                time.sleep(10)
                            elif raw_json_unescaped['code'] == 0:
                                break

                        # Stupid api design
                        if raw_json_unescaped['code'] == -404 or not raw_json_unescaped.get('data', {}).get('list',
                                                                                                            {}).get(
                            'vlist'):
                            # User has no videos
                            new_list.append(
                                {
                                    "title": None,
                                    "article_id": "0",
                                    "author_name": author_name_l,
                                    "author_id": author_id_l,
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
                                        "author_name": author_name_l,
                                        "author_id": author_id_l,
                                        "channel_name": "哔哩哔哩视频",
                                        "link": link,
                                        "creation_time": str(creation_time),
                                        "snapshot_time": str(current_time)
                                    }
                                )

                self.videos_json = json.dumps(new_list, ensure_ascii=False)
                # break on success
                if self.videos_json:
                    break

            except Exception as error:
                logging.exception(f"Error getting or parsing the response: {error}")

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.videos_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

    def get_articles_list(self, retry_times=3, contents_num="15", sourt_by="publish_time"):
        # Waring contents_num cannot to be too big, or the stupid api will return incomplete json
        new_list = []
        current_time = int(datetime.now().timestamp())

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    raw_parameter = {
                        "mid": author_id_l,
                        "ps": contents_num,
                        "sort": sourt_by,
                    }

                    # anti anti crawl
                    signed_parameter = self.get_signed_parameters(raw_parameter)

                    url = "https://api.bilibili.com/x/space/wbi/article?" + signed_parameter

                    response = requests.get(url=url, headers=self.headers)

                    if response.status_code == 200:
                        raw_json_unescaped = json.loads(response.text)

                        # Bilibili’s risk control has been strengthened, sometimes you will get -403 in JSON;
                        # retry 5 times
                        max_attempts = 5
                        attempts = 0
                        while raw_json_unescaped['code'] == -403 and attempts < max_attempts:
                            time.sleep(5)

                            response = requests.get(url=url, headers=self.headers)
                            raw_json_unescaped = json.loads(response.text)
                            attempts += 1

                            if raw_json_unescaped['code'] == -403:
                                time.sleep(10)
                            elif raw_json_unescaped['code'] == 0:
                                break

                        # Stupid api design
                        if raw_json_unescaped['code'] == "-404" or raw_json_unescaped[
                            'code'] == -404 or not raw_json_unescaped.get('data', {}).get('articles'):
                            # User has no articles
                            new_list.append(
                                {
                                    "title": None,
                                    "article_id": "0",
                                    "author_name": author_name_l,
                                    "author_id": author_id_l,
                                    "channel_name": "哔哩哔哩文章",
                                    "link": None,
                                    "creation_time": "0",
                                    "snapshot_time": str(current_time)
                                }
                            )
                        else:
                            # User has articles
                            for item in raw_json_unescaped['data']['articles']:
                                title = item['title']
                                creation_time = item['publish_time']
                                link = "https://www.bilibili.com/read/cv" + str(item['id'])

                                new_list.append(
                                    {
                                        "title": title,
                                        "article_id": str(item['id']),
                                        "author_name": author_name_l,
                                        "author_id": author_id_l,
                                        "channel_name": "哔哩哔哩文章",
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


if __name__ == "__main__":
    bb = BilibiliSpider()
    bb.start()
    print(bb.articles_json)
