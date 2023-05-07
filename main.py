#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Obtain and compare the list of old and new articles, and push the latest articles
# Author: 10935336
# Creation date: 2023-04-20
# Modified date: 2023-05-06

import importlib
import json
import logging
import os
import site
from os.path import dirname, join, realpath

# Change to dynamic loading in the future
from module.DingTalkRobot import push_to_dingtalk


def load_spiders_list(spiders_list_path=None):
    if spiders_list_path is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        spiders_list_path = os.path.join(module_dir, '.', 'conf', 'spider_list.json')

    try:
        with open(spiders_list_path, 'r', encoding='utf-8') as r:
            spiders_list = json.load(r)
            r.close()
            return spiders_list
    except Exception as error:
        logging.exception(f'{spiders_list_path} read error: {error}')


def spiders_init(spiders_list):
    try:
        objects_list = []

        for spider in spiders_list:
            try:
                spider_id_l = spider['spider_id']
                object_name_l = spider['object_name']
            except Exception as error:
                logging.exception(f'Cannot find wanted value in spiders_list: {error}')

            # dynamic load module
            try:
                # module dir
                module = importlib.import_module('module.' + spider_id_l)
            except Exception as error:
                logging.exception(f'Cannot load module: {error}')

            # instantiating the object
            try:
                spider_class = getattr(module, spider_id_l)
                globals()[object_name_l] = spider_class()
                objects_list.append(globals()[object_name_l])
            except Exception as error:
                logging.exception(f'Instantiating the object error: {error}')

        return objects_list
    except Exception as error:
        logging.exception(f'Unexpected error 1: {error}')


def get_all_articles_list(objects_list):
    all_list = []
    try:
        for object_ in objects_list:
            logging.info(f"Now loading {object_}")
            object_.start()
            if object_.articles_json:
                all_list.append(json.loads(object_.articles_json))
    except Exception as error:
        logging.exception(f'Unexpected error 2: {error}')

    return json.dumps(all_list, ensure_ascii=False)


def get_new_articles(objects_list, previous_articles_file_path='previous_articles.json', time_threshold=259200):
    """
    Get new articles from the given list of articles and save the new articles list to a file.

    :return: List of new articles found in the given objects_list.
    """

    if previous_articles_file_path is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        previous_articles_file_path = os.path.join(module_dir, '.', 'previous_articles.json')


    try:
        # Convert a JSON string to a Python list
        current_articles_lists = json.loads(get_all_articles_list(objects_list))

        # If the previous_articles_file_path file exists, read the JSON string in the file as json list
        if os.path.exists(previous_articles_file_path):
            try:
                with open(previous_articles_file_path, 'r', encoding='utf-8') as f:
                    previous_articles_lists = json.load(f)
                    previous_authors_ids = set()

                    for current_article_list in previous_articles_lists:
                        for current_article in current_article_list:
                            previous_authors_ids.add(current_article['author_id'])

            except json.JSONDecodeError as error:
                logging.exception(f'JSON decode error: {error}')
                previous_articles_lists = []
                previous_authors_ids = set()

        else:
            previous_articles_lists = []
            previous_authors_ids = set()

        # 15 days  1296000
        # 3 days  259200
        # time_threshold = 15 * 24 * 60 * 60

        new_articles = []

        # Loop through each article in the current article list
        for current_article_list in current_articles_lists:
            for current_article in current_article_list:
                is_new = True

                # If the author id is new, skip this article,
                # and effectively avoid misjudgment when the last acquisition fails or the next acquisition fails
                if current_article['author_id'] not in previous_authors_ids:
                    continue

                # Skip when the difference between creation_time and snapshot_time exceeds the value of time_threshold
                # and skip time diff judgment for articles with creation_time == 0
                # further avoid misjudgment
                if current_article['creation_time'] != 0:
                    time_diff = int(current_article['snapshot_time']) - int(current_article['creation_time'])
                    if time_diff > time_threshold:
                        is_new = False

                # Use the article_id field of the article as a unique identifier
                # to find whether it exists in the last obtained article list
                for previous_articles_lists_list in previous_articles_lists:
                    for previous_article in previous_articles_lists_list:
                        if current_article['article_id'] == previous_article['article_id']:
                            is_new = False
                            break
                    if not is_new:
                        break

                # If the current article does not exist in the last obtained article list,
                # add it to the new article list
                if is_new:
                    new_articles.append(current_article)

        # Save the current article list to the previous_articles_file_path file for comparison at the next execution
        with open(previous_articles_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_articles_lists, f, ensure_ascii=False)

    except FileNotFoundError as error:
        new_articles = []
        logging.exception(f'File not found: {error}')
    except Exception as error:
        new_articles = []
        logging.exception(f'Unexpected error 3: {error}')

    return new_articles


if __name__ == "__main__":
    # Important, run this to make it run on absolute paths
    site.addsitedir(realpath(join(dirname(__file__), '..')))
    site.addsitedir(realpath(dirname(__file__)))

    # log
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    data_format = "%m/%d/%Y %H:%M:%S"

    module_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(module_dir, '.', 'spider.log')

    logging.basicConfig(filename=log_path, level=logging.INFO, format=log_format, datefmt=data_format,
                        encoding='utf-8')

    # get new_articles
    objects_list = spiders_init(load_spiders_list())
    new_articles = get_new_articles(objects_list)

    # push to dingtalk
    logging.info(new_articles)
    push_to_dingtalk(new_articles)
