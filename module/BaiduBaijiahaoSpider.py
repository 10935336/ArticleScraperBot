#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Baidu baijiahao designated authors crawl articles
# Note: I don't know how to use requests to get that, risk control is strict,
# and the page must be refreshed to get the correct response.
# Author: 10935336
# Creation date: 2023-04-20
# Modified date: 2023-05-19


import json
import logging
import os
import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class BaiduBaijiahaoSpider:
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

    def fill_uk_for_authors_list(self, authors_list_path=None, write_back=True):

        def get_uk_by_id(author_id_l):
            # Get the uk from the author's homepage
            url = "https://author.baidu.com/home/" + author_id_l
            try:
                self.driver.implicitly_wait(10)

                self.driver.get(url)

                content = self.driver.find_element(By.XPATH, '//*[@id="main"]').get_attribute("url")

                uk_pattern = re.compile(r'uk=(.+?)&')
                uk_match = uk_pattern.search(content)

                if uk_match:
                    uk_value = uk_match.group(1)
                    if uk_value is None or uk_value == 'null':
                        logging.exception("cannot get uk")
                    else:
                        return uk_value
                else:
                    logging.exception('uk value not found')

            except Exception as error:
                logging.exception(f'Cannot get uk: {error}')

        def write_uk_back_to_list(authors_list_path):
            try:
                with open(authors_list_path, 'w', encoding='utf-8') as w:
                    json.dump(self.authors_list, w, ensure_ascii=False)
            except Exception as error:
                logging.exception(f'{authors_list_path} write error: {error}')

        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'baidubaijiahao_authors_list.json')

        try:
            # I know that selenium should not be initialized here,
            # it will make get_uk_by_id() impossible to call independently,
            # but if I initialize it in get_uk_by_id(),
            # it will cause selenium to be initialized in a loop,
            # and then the browser will not exit.
            self.driver_init()

            # Check if the author list has uk, if not, add it
            for item in self.authors_list:
                if 'author_uk' not in item or item['author_uk'] == 'null' or item['author_uk'] == 'Null' or item[
                    'author_uk'] == None:
                    # Pycharm want we to do "'author_uk' is None", but CPython wants me to do "'author_uk' == None"
                    author_id = item['author_id']
                    uk_value = get_uk_by_id(author_id)
                    item['author_uk'] = uk_value

        except Exception as error:
            logging.exception(f'Cannot get author_id: {error}')

        # Make sure selenium quits, but doesn't always work
        try:
            self.driver.close()
        except Exception:
            pass

        try:
            self.driver.quit()
            self.driver.quit()
        except Exception:
            pass

        if write_back:
            write_uk_back_to_list(authors_list_path)

    def get_articles_list(self, retry_times=3, tab='article', contents_num='50', type_='newhome', action='dynamic',
                          format_='json'):
        new_list = []
        current_time = int(datetime.now().timestamp())

        try:
            for item in self.authors_list:
                if 'author_uk' not in item or item['author_uk'] == 'null' or item['author_uk'] == 'Null' or item[
                    'author_uk'] == None:
                    self.fill_uk_for_authors_list()
        except Exception as error:
            logging.exception(f'Get uk error: {error}')

        self.driver_init()

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                        author_uk_l = author['author_uk']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    url = "https://mbd.baidu.com/webpage?" + "tab=" + tab + "&num=" + contents_num + "&type=" + type_ \
                          + "&action=" + action + "&format=" + format_ + "&uk=" + author_uk_l

                    self.driver.implicitly_wait(10)

                    # too fast will connection reset
                    time.sleep(3)

                    self.driver.get(url=url)
                    self.driver.refresh()
                    self.driver.refresh()

                    raw_json = self.driver.find_element(By.XPATH, "/html/body/pre").text

                    # avoid escape
                    raw_json_unescaped = json.loads(json.dumps(json.loads(raw_json), ensure_ascii=False))

                    # Iterate through the list in the raw JSON data
                    for item in raw_json_unescaped['data']['list']:
                        title = item['itemData']['title']
                        creation_time = item['itemData']['created_at']
                        link = item['itemData']['url']
                        article_id = item['itemData']['shoubai_c_articleid']

                        new_list.append(
                            {
                                "title": title,
                                "article_id": article_id,
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "百度百家号",
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
                logging.exception(f"Error on getting or parsing the response: {error}")
                self.articles_json = []

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.articles_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

        # Make sure selenium quits, but doesn't always work
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
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'baidubaijiahao_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    bjh = BaiduBaijiahaoSpider()
    bjh.start()
    print(bjh.articles_json)
