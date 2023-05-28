#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Twitter designated authors crawl articles
# Note: This is fetched in HTML, not from API
# Cause if your project has "free access" you can only use these endpoints:
# * POST /2/tweets
# * DELETE /2/tweets/:id
# * GET /2/users/me
# We need * GET /2/tweets/search/recent
# I do not want pay 100USD/month to Elon Musk
# So that's it
# Author: 10935336
# Creation date: 2023-05-12
# Modified date: 2023-05-26


import json
import logging
import os
import re
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class TwitterHTMLSpider:
    def __init__(self):
        self.driver = ''
        self.options = ''
        self.authors_list = []
        self.articles_json = ''

    def driver_init(self):
        # Driver setting
        self.options = Options()
        # disable automatic notice
        self.options.set_preference("dom.webdriver.enabled", False)
        self.options.set_preference('useAutomationExtension', False)
        # disable json viewer
        self.options.set_preference("devtools.jsonview.enabled", False)
        # headless mode
        self.options.add_argument('-headless')
        # Driver init
        self.driver = webdriver.Firefox(options=self.options)

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self, retry_times=3):
        new_list = []
        current_time = int(datetime.now().timestamp())

        self.driver_init()

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']

                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    self.driver.implicitly_wait(10)

                    url = "https://twitter.com/" + str(author_id_l)

                    self.driver.get(url)

                    time.sleep(10)

                    # scroll down twice
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    time.sleep(10)

                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, "html.parser")

                    tweets = soup.find_all('div', {'data-testid': 'cellInnerDiv'})

                    for tweet in tweets:
                        text_div = tweet.find("div", {"data-testid": "tweetText"})
                        if text_div is not None:
                            text = text_div.text
                            clean_text = re.sub(r'http\S+', '', text)
                        else:
                            clean_text = "The post appears to have no text\n此帖子无文本"


                        link_a = tweet.find("a", href=lambda x: x and "/status/" in x)
                        if link_a is not None:
                            link = link_a["href"]
                            full_link = "https://twitter.com" + link_a["href"]
                            article_id = link.split('/')[-1]
                        else:
                            full_link = None
                            article_id = "0"

                        time_element = soup.find('time')
                        if time_element is not None:
                            datetime_value = time_element['datetime']
                            datetime_obj = datetime.strptime(datetime_value, '%Y-%m-%dT%H:%M:%S.%fZ')
                            timestamp = int(datetime_obj.timestamp())
                        else:
                            timestamp = "0"

                        new_list.append(
                            {
                                "title": str(clean_text),
                                "article_id": str(article_id),
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "Twitter",
                                "link": full_link,
                                "creation_time": str(timestamp),
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

        try:
            self.driver.close()
        except Exception:
            pass

        try:
            self.driver.quit()
            self.driver.quit()
        except Exception:
            pass

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'twitterhtml_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    twi = TwitterHTMLSpider()
    twi.start()
    print(twi.articles_json)
