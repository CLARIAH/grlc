#!/usr/bin/env python

# cache.py: grlc spec caching utilities
import json
import urllib.request, urllib.error, urllib.parse
import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

# Name of the cache json file
CACHE_NAME = "db-cache.json"

def init_cache():
    '''
    Initializes the grlc cache (json file)
    '''
    cache_obj = json.loads("{}")
    try:
        with open(CACHE_NAME, 'r') as cache_file:
            try:
                cache_obj = json.load(cache_file)
            except ValueError:
                print("The cache file seems to be empty, starting with flushed cache")
    except IOError:
        print("The cache file seems to be empty, starting with flushed cache")

    print("Loaded JSON cache")

    return cache_obj

def is_cache_updated(cache_obj, repo_uri):
    if repo_uri not in cache_obj:
        return False
    cache_date = cache_obj[repo_uri]['date']
    stream = urllib.request.urlopen(repo_uri)
    resp = json.load(stream)
    github_date = resp['pushed_at']

    return cache_date > github_date
