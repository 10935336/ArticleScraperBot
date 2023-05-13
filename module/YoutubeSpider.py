#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Youtube designated channel crawl videos, obtain from the official api - YouTube Data API v3
# Note: Need API Key :https://console.cloud.google.com/apis/api/youtube.googleapis.com
# Author: 10935336
# Creation date: 2023-05-12
# Modified date: 2023-05-12

import json
import logging
import os
from datetime import datetime

import requests


class YoutubeSpider:
    def __init__(self):
        self.articles_json = ''
        self.api_key_list = []
        self.authors_list = []
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 13.0; Nexus 15 Build/MRA99N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
        }

    def load_api_key(self, api_key_path):
        try:
            with open(api_key_path, 'r', encoding='utf-8') as r:
                self.api_key_list = json.load(r)
        except Exception as error:
            logging.exception(f'{api_key_path} read error: {error}')

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def fill_uploads_id_for_authors_list(self, authors_list_path=None, write_back=True):

        def get_uploads_id_by_id(channel_id, api_key):

            url = "https://www.googleapis.com/youtube/v3/channels?" + \
                  "id=" + str(channel_id) + \
                  "&key=" + str(api_key) + \
                  "&part=contentDetails"
            try:
                response = requests.get(url=url, headers=self.headers)
                if response.status_code == 200:
                    raw_json_unescaped = json.loads(response.text)
                    uploads_id = raw_json_unescaped["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                    return uploads_id
            except Exception as error:
                logging.exception(f'get uploads_id error: {error}')

        def write_uploads_id_back_to_list(authors_list_path):
            try:
                with open(authors_list_path, 'w', encoding='utf-8') as w:
                    json.dump(self.authors_list, w, ensure_ascii=False)
            except Exception as error:
                logging.exception(f'{authors_list_path} write error: {error}')

        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'youtube_authors_list.json')

        try:
            for key in self.api_key_list:
                api_key = key['api_key']
            # Check if the author list has uploads_id, if not, add it
            for item in self.authors_list:
                if 'uploads_id' not in item:
                    author_id = item['author_id']
                    uploads_id_value = get_uploads_id_by_id(author_id, api_key)
                    item['uploads_id'] = uploads_id_value
        except Exception as error:
            logging.exception(f'Get author_id error: {error}')

        if write_back:
            write_uploads_id_back_to_list(authors_list_path)

    def get_articles_list(self, max_results=20, part='snippet'):
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for key in self.api_key_list:
                api_key = key['api_key']
        except Exception as error:
            logging.exception(f'Cannot find wanted value in api_key_list: {error}')

        # Check if the author list has mkey, if not, add it
        try:
            for item in self.authors_list:
                if 'uploads_id' not in item:
                    self.fill_uploads_id_for_authors_list()
        except Exception as error:
            logging.exception(f'Get uploads_id error: {error}')

        try:
            for author in self.authors_list:
                try:
                    author_id_l = author['author_id']
                    author_name_l = author['author_name']
                    uploads_id_l = author['uploads_id']
                except Exception as error:
                    logging.exception(f'Cannot find wanted value in authors_list: {error}')

                url = "https://www.googleapis.com/youtube/v3/playlistItems?" + \
                      "playlistId=" + str(uploads_id_l) + \
                      "&key=" + str(api_key) + \
                      "&part=" + str(part) + \
                      "&maxResults=" + str(max_results)

                response = requests.get(url=url, headers=self.headers)
                if response.status_code == 200:

                    raw_json_unescaped = json.loads(response.text)

                    # Iterate through the list in the raw JSON data
                    for item in raw_json_unescaped["items"]:
                        title = item["snippet"]["title"]
                        video_id = item["snippet"]["resourceId"]["videoId"]
                        link = "https://www.youtube.com/watch?v=" + video_id

                        # time
                        datetime_obj = datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
                        timestamp = int(datetime_obj.timestamp())

                        new_list.append(
                            {
                                "title": title,
                                "article_id": video_id,
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "Youtube",
                                "link": link,
                                "creation_time": str(timestamp),
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)
        except Exception as error:
            logging.exception(f"Error getting or parsing the response: {error}")
            self.articles_json = []

    def start(self, authors_list_path=None, api_key_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'youtube_authors_list.json')
        if api_key_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            api_key_path = os.path.join(module_dir, '..', 'conf', 'youtube_apikey_list.json')
        self.load_api_key(api_key_path)
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    ytb = YoutubeSpider()
    ytb.start()
    print(ytb.articles_json)
