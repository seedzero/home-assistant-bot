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
    reddit = praw.Reddit(user_agent=c['app_ua'],
                         client_id=c['app_id'],
                         client_secret=c['app_secret'],
                         username='HomeAssistantBot',
                         refresh_token=c['app_refresh'])
    return reddit


def postToReddit(entries, flair, sticky=None):
    for entry in reversed(entries):
        log("Attempting to post: " + entry['title'])
        try:
            sr = r.subreddit(subreddit)
            sub = sr.submit(entry['title'], url=entry['link'], send_replies=False, resubmit=False)
        except praw.exceptions.APIException as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            log(message)
            continue
        log("Posted " + entry['title'] + " " + entry['link'])
        sub.flair.select(flair)
        log("Flair " + flair + " added for post " + entry['title'])
        if sticky and entry['id'] == sticky['id']:
            sub.mod.sticky(state=True, bottom=True)
            log("Post " + entry['title'] + "made sticky.")

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
    newsticky = unposted_releases[0]
    postToReddit(unposted_releases,
                 fl['release'],
                 sticky=newsticky)
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
