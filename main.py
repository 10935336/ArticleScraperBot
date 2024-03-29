#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: 10935336
# Creation date: 2023-04-20
# Modified date: 2024-01-24

import importlib
import pickle
import site
import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler
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
        logging.exception(f'Unexpected error in spiders_init(): {error}')


def get_all_current_articles_lists(objects_list):
    all_list = []
    try:
        for object_ in objects_list:
            logging.info(f"Now loading {object_}")
            object_.start()
            if object_.articles_json:
                all_list.append(json.loads(object_.articles_json))
    except Exception as error:
        logging.exception(f'Unexpected error in get_all_current_articles_lists(): {error}')

    return json.dumps(all_list, ensure_ascii=False)


def get_new_articles(all_current_articles_lists, previous_articles_file_path='previous_articles.json',
                     time_threshold=86400):
    """
    Get new articles from the given list of articles and save the new articles list to a file.

    time_threshold = days * 24 * 60 * 60
    15 days = 1296000
    3 days = 259200
    1 day = 86400

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

        new_articles = []

        # Loop through each article in the current article list
        for current_article_list in current_articles_lists:
            for current_article in current_article_list:
                is_new = True

                # If the article_id acquisition fails, record an error and skip
                if current_article['article_id'] is None:
                    logging.error(f"article_id is null {current_article}")
                    continue

                # If the author id is new, skip this article,
                # and effectively avoid misjudgment when the last acquisition fails or the next acquisition fails
                if current_article['author_id'] not in previous_authors_ids:
                    continue

                # If some APIs do not return,
                # current_article['article_id'] will be recorded as 0, skipped to avoid misjudgment
                if current_article['article_id'].isdigit():
                    if int(current_article['article_id']) == 0:
                        continue

                # Skip when the difference between creation_time and snapshot_time exceeds the value of time_threshold
                # and skip time diff judgment for articles with creation_time == 0, further avoid misjudgment
                if current_article['creation_time'] is not None and current_article['creation_time'].isdigit():
                    if int(current_article['creation_time']) != 0:
                        time_diff = int(current_article['snapshot_time']) - int(current_article['creation_time'])
                        if time_diff > time_threshold:
                            is_new = False

                # Use the article_id and author_id field of the article as a unique identifier,
                # to find whether it exists in the last obtained article list
                for previous_articles_lists_list in previous_articles_lists:
                    for previous_article in previous_articles_lists_list:
                        if current_article['article_id'] == previous_article['article_id'] and current_article[
                            'author_id'] == previous_article['author_id']:
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
        logging.exception(f'Unexpected error in get_new_articles(): {error}')
        logging.error(f'Current article: {current_article}')

    return new_articles


def get_articles_summary(all_current_articles_lists, start_time_threshold=86400, end_time=None):
    """
    The time interception range is "end_time - start_time_threshold" to "end_time",
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
        logging.exception(f'Unexpected error in get_articles_summary(): {error}')

    return channel_article_count


def time_judgment(target_time_hour: int, time_range: timedelta, current_time: datetime) -> bool:
    """
    Determine whether the current time is near a certain range, and if so, return True.
    for example,
    time_judgment(target_time=20, time_range=timedelta(minutes=20) returns True if 15 minutes around 20

    :param current_time: class 'datetime.datetime',e.g. datetime.now() 2023-05-21 20:13:42.637117
    :param target_time_hour: Pass in the hour, e.g., 15 is 3pm
    :param time_range: class 'datetime.timedelta' Pass in the delivery time range in timedelta(), for example, timedelta(minutes=20) is 20 minutes before and after target_time
    :return: True or False
    """
    start_time = current_time.replace(hour=target_time_hour, minute=0, second=0, microsecond=0) - time_range
    end_time = current_time.replace(hour=target_time_hour, minute=0, second=0, microsecond=0) + time_range
    return start_time <= current_time <= end_time


def push_new_articles(new_articles, push_func, current_time, records_expire_days=7,
                      records_name='article_pushed_records.pkl'):
    """
    Check whether duplicate articles have been pushed within 7 days, and push

    :param new_articles: new_articles
    :param push_func: push function name
    """
    records_dir = os.path.dirname(os.path.abspath(__file__))
    records_path = os.path.join(records_dir, '.', records_name)

    def load_records(records_path):
        try:
            with open(records_path, 'rb') as f:
                records = pickle.load(f)
        except FileNotFoundError:
            records = []
        return records

    def check_if_article_is_pushed(article, records, current_time):
        for record in records:
            if record['article'] == article and current_time - record['push_time'] < timedelta(
                    days=records_expire_days):
                # Already pushed
                return True
        # Not pushed
        return False

    def record_pushed_article(article, records, current_time):
        records.append({
            'article': article,
            'push_time': current_time
        })

    def save_records(records):
        with open(records_path, 'wb') as f:
            pickle.dump(records, f)

    def clean_expired_records_and_save(records, current_time):
        # Calculate the difference between the current time and the push time in the record.
        # If this time difference is less than or equal to records_expire_days days,
        # it means that this record has not expired, and it will be added to the new list.
        new_records = [record for record in records if
                       current_time - record['push_time'] <= timedelta(days=records_expire_days)]
        save_records(new_records)

    records = load_records(records_path)

    # Determine whether the article has been pushed
    unpushed_articles = []
    for article in new_articles:
        if not check_if_article_is_pushed(article, records, current_time):
            unpushed_articles.append(article)

    # Push if there are unpushed articles
    if unpushed_articles:
        push_func(unpushed_articles)

        # Add pushed articles to the pushed list
        for article in unpushed_articles:
            record_pushed_article(article, records, current_time)

    # clean expired records and save new records
    clean_expired_records_and_save(records, current_time)


def setup_logging(log_name='spider.log', max_bytes=10485760, backup_count=3):
    # maximum size of the log file 10MB (10*1024*1024=10485760)
    # maximum backup_count 3

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    data_format = "%Y/%m/%d %H:%M:%S"

    logdir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(logdir, log_name)

    logging.basicConfig(handlers=[RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)],
                        level=logging.INFO, format=log_format, datefmt=data_format,
                        encoding='utf-8')

if __name__ == "__main__":
    # Important
    # run this to make it run on absolute paths
    site.addsitedir(realpath(join(dirname(__file__), '..')))
    site.addsitedir(realpath(dirname(__file__)))

    # log
    setup_logging()

    # Define the current time here to avoid incorrect time due to long processing time
    current_time = datetime.now()

    # get current_articles_lists
    objects_list = spiders_init(load_spiders_list())
    all_current_articles_lists = get_all_current_articles_lists(objects_list)

    # get new_articles
    new_articles = get_new_articles(all_current_articles_lists)

    # push new articles to dingtalk
    logging.info(f'new articles: {new_articles}')
    push_new_articles(new_articles=new_articles, push_func=push_new_articles_to_dingtalk, current_time=current_time)

    # If the current time is around 20 o'clock for 15 minutes
    if time_judgment(target_time_hour=20, time_range=timedelta(minutes=15), current_time=current_time):
        # get articles_summary
        articles_summary = get_articles_summary(all_current_articles_lists)
        # push summary to dingtalk
        logging.info(f'articles summary: {articles_summary}')
        push_summary_to_dingtalk(articles_summary)
