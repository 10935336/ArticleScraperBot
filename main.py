#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: 10935336
# Creation date: 2023-04-20
# Modified date: 2023-05-12

import importlib
import site
from datetime import timedelta
from os.path import dirname, join, realpath

# Change to dynamic loading in the future
from module.DingTalkRobot import *


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


def get_all_current_articles_lists(objects_list):
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


def get_new_articles(all_current_articles_lists, previous_articles_file_path='previous_articles.json',
                     time_threshold=259200):
    """
    Get new articles from the given list of articles and save the new articles list to a file.

    :return [{},{}]
    """

    if previous_articles_file_path is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        previous_articles_file_path = os.path.join(module_dir, '.', 'previous_articles.json')

    try:
        # Convert a JSON string to a Python list
        current_articles_lists = json.loads(all_current_articles_lists)

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


def get_articles_summary(all_current_articles_lists, start_time_threshold=86400, end_time=None):
    """
    The time interception range is "end_time - start_time_threshold" to "end_time"
    For example, if
    start_time_threshold = 86400 (one day),  end_time = 1680086400
    Then the time interception range is 1680000000 to 1680084600
    That is, 2023-03-28 18:40:00 to 2023-03-29 18:40:00

    For "channel_name" and "author_name" in all_current_articles_lists.
    "channel_name" and "author_name" can be further subdivided by the new-style named like "foo-bar"
    we will take "foo" as "team_name" or "channel_name",
    if "team_name" or "channel_name" without "-" then extract all

    :return {'team_name' : {'channel_name': num,'channel_name': 'num',total: 'num'},'team_name' : {'channel_name': num,'channel_name': 'num',total: 'num'}}
    type dic
    """
    # Convert a JSON string to a Python list
    current_articles_lists = json.loads(all_current_articles_lists)

    channel_article_count = {}

    # The default end_time is snapshot_time which is close to the current time
    if end_time is None:
        try:
            end_time = int(current_articles_lists[0][0]['snapshot_time'])
        except Exception as error:
            logging.exception(f'Cannot get end_time: {error}')
            logging.error(f'trying to set end_time to current time')
            end_time = int(datetime.now().timestamp())

        try:
            start_time = end_time - int(start_time_threshold)
        except Exception as error:
            logging.exception(f'Cannot get start_time: {error}')

    try:
        for current_article_list in current_articles_lists:
            for current_article in current_article_list:

                # Check if the article is within start_time to end_time
                if start_time <= int(current_article['creation_time']) <= end_time:
                    pass
                else:
                    continue

                try:
                    # Get channel_name,
                    # "channel_name" can be further subdivided by the new-style named "foo-bar"
                    # we will take foo as channel_name, if "author_name" without "-" then extract all
                    channel_name_raw = current_article['channel_name']
                    channel_name = channel_name_raw.split('-')[0]

                    # Get team_name,
                    # "author_name" can be further subdivided by the new-style named "foo-bar"
                    # we will take foo as team_name, if "author_name" without "-" then extract all
                    team_name_raw = current_article['author_name']
                    team_name = team_name_raw.split('-')[0]

                except Exception as error:
                    logging.exception(f'Cannot get team_name or channel_name: {error}')

                # Whether team_name already exists in channel_article_count,
                # if it exists, add one to the count,
                # if not, increase the team_name key-value pair and set the value to 1
                if team_name in channel_article_count:
                    # same but channel_name
                    if channel_name in channel_article_count[team_name]:
                        channel_article_count[team_name][channel_name] += 1
                    else:
                        channel_article_count[team_name][channel_name] = 1
                else:
                    channel_article_count[team_name] = {channel_name: 1}

                # Calculate total count and add to channel_article_count
        for team_name, channel_info in channel_article_count.items():
            total_count = 0
            for channel_name, count in channel_info.items():
                total_count += count
            channel_article_count[team_name]['total'] = total_count

        # add time
        channel_article_count['time'] = {'start_time': start_time, 'end_time': end_time}

    except Exception as error:
        logging.exception(f'Unexpected error 4: {error}')

    return channel_article_count


def time_judgment(target_time_hour: int, time_range: timedelta) -> bool:
    """
    Determine whether the current time is near a certain range, and if so, return True
    for example,
    time_judgment(target_time=20, time_range=timedelta(minutes=20) return True if 15 minutes around 20

    :param target_time_hour: Pass in the hour, e.g. 15 is 3pm
    :param time_range: Pass in the delivery time range in timedelta(), for example, timedelta(minutes=20) is 20 minutes before and after target_time
    :return: True or False
    """

    current_time = datetime.now()
    start_time = current_time.replace(hour=target_time_hour, minute=0, second=0, microsecond=0) - time_range
    end_time = current_time.replace(hour=target_time_hour, minute=0, second=0, microsecond=0) + time_range
    return start_time <= current_time <= end_time


if __name__ == "__main__":
    # Important
    # run this to make it run on absolute paths
    site.addsitedir(realpath(join(dirname(__file__), '..')))
    site.addsitedir(realpath(dirname(__file__)))

    # log
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    data_format = "%m/%d/%Y %H:%M:%S"

    dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(dir, '.', 'spider.log')

    logging.basicConfig(filename=log_path, level=logging.INFO, format=log_format, datefmt=data_format,
                        encoding='utf-8')

    # get current_articles_lists
    objects_list = spiders_init(load_spiders_list())
    all_current_articles_lists = get_all_current_articles_lists(objects_list)

    # get new_articles
    new_articles = get_new_articles(all_current_articles_lists)

    # push new articles to dingtalk
    logging.info(f'new articles: {new_articles}')
    push_new_articles_to_dingtalk(new_articles)

    # If the current time is around 20 o'clock for 20 minutes
    if time_judgment(target_time_hour=20, time_range=timedelta(minutes=20)):
        # get articles_summary
        articles_summary = get_articles_summary(all_current_articles_lists)
        logging.info(f'articles summary: {articles_summary}')
        # push summary to dingtalk
        push_summary_to_dingtalk(articles_summary)
