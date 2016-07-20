#!/usr/bin/env python3

import configparser
import feedparser
import logging
import os
import praw

scr_dir = os.path.dirname(os.path.abspath(__file__))
ini_path = os.path.join(scr_dir, 'home-assistant-bot.ini')
log_path = os.path.join(scr_dir, 'home-assistant-bot.log')

logging.basicConfig(filename=log_path,
                    format='%(asctime)s %(name)-12s %(levelname)-8s '
                           '%(message)s',
                    datefmt='%d-%m-%y %H:%M:%S',
                    filemode='w',
                    level=logging.DEBUG)
log = logging.debug

config = configparser.ConfigParser()
config.read(ini_path)

c = config['SETTINGS']
if c['testing'] == "1":
    fl = config['FLAIR_TEST']
    hi = config['HISTORY_TEST']
    subreddit = c['subreddittest']
    log("Running in Test Mode")
else:
    fl = config['FLAIR']
    hi = config['HISTORY']
    subreddit = "HomeAssistant"

rel = feedparser.parse("https://home-assistant.io/blog/"
                       "categories/release-notes/atom.xml")
blog = feedparser.parse("https://home-assistant.io/atom.xml")

unposted_blog = []
unposted_releases = []

last_release = hi['lastrelease']
last_blog = hi['lastblog']


def login():
    r = praw.Reddit(c['app_ua'])
    r.set_oauth_app_info(c['app_id'], c['app_secret'], c['app_uri'])
    r.refresh_access_information(c['app_refresh'])
    return r


def postToReddit(entries, flair):
    for entry in reversed(entries):
        log("Attempting to post: " + entry['title'])
        sub = r.submit(subreddit, entry['title'], url=entry['link'])
        log("Posted " + entry['title'] + " " + entry['link'])
        r.select_flair(sub,
                       flair_template_id=flair)
        log("Flair " + flair + " added for post " + entry['title'])

r = login()

for entry in blog['entries']:
    if entry['id'] not in [rels['id'] for rels in rel['entries']]:
        if entry["id"] == last_blog:
            break
        else:
            unposted_blog.append(entry)

for entry in rel['entries']:
    if entry['id'] == last_release:
        break
    else:
        unposted_releases.append(entry)

if unposted_releases:
    postToReddit(unposted_releases,
                 fl['release'])
    hi['lastrelease'] = unposted_releases[0]['id']
else:
    log("No unposted releases.")

if unposted_blog:
    postToReddit(unposted_blog, fl['blog'])
    hi['lastblog'] = unposted_blog[0]['id']
else:
    log("No unposted blog entries.")

with open(ini_path, 'w') as configfile:
    config.write(configfile)
