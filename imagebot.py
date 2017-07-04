"""
imagebot
Author: Zane Bilous
Last Updated: 7/04/2017

Download image posts from subreddits.

Usage:
    - Specify the download path in the DOWNLOAD_PATH variable,
      or in the argument to download_from_subreddit(s).

    - Specify client ID and client secret in praw.ini.
"""
import io
import json
import multiprocessing
import os
import zipfile
from urllib.parse import urlparse

import praw
import requests
from bs4 import BeautifulSoup

DOWNLOAD_PATH = '.'
# urls containing these extensions will be recognized as direct images
IMAGE_FORMATS = ('.png', '.gif', '.gifv', '.jpg', '.jpeg')

# selectors.json contains tag/attribute identifiers for image links
with open('selectors.json', 'r') as f:
    IMAGE_SELECTORS = json.load(f)

# imagebot refers to the name in praw.ini
reddit = praw.Reddit('imagebot')
# use Session so TCP connections are reused
s = requests.Session()


def get_request(url):
    """Checks for bad responses and returns request object."""
    # some website URL schemes do not have the protocol included
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    req = s.get(url)
    if req.status_code != 200:
        print(f'Encountered bad url: {url}')
        return None
    return req


def get_image_url(url):
    """Returns direct image url from supported page."""
    req = get_request(url)
    if req is None:
        return None
    # get domain name from url: http://imgur.com/ASoeL -> imgur.com
    domain = urlparse(url).netloc
    error_msg = f'[-] Encountered unsupported URL: {url} with domain {domain}'

    try:
        # copy the dict because we pop from it
        selectors = IMAGE_SELECTORS[domain].copy()
    except KeyError:
        print(error_msg)
        return None

    # attribute containing the image link, pop it from dict
    # so we can easily unpack the other selectors to the find method
    link = selectors.pop('link')
    soup = BeautifulSoup(req.text, 'html.parser')
    # unpack selectors into keyword arguments
    img = soup.find(**selectors)

    try:
        return img.get(link)
    except AttributeError:
        print(error_msg)


def download_image(url, path=DOWNLOAD_PATH, chunksize=512):
    """Downloads image to the specified download path."""
    req = get_request(url)
    if req is None:
        return None

    filename = os.path.basename(url)
    with open(os.path.join(path, filename), 'wb') as file:
        for chunk in req.iter_content(chunksize):
            file.write(chunk)
    return True


def download_album(url, path=DOWNLOAD_PATH):
    """Downloads an album from imgur as a zip file and extracts it."""
    req = get_request(f'{url}/zip')
    if req is None:
        return None

    with zipfile.ZipFile(io.BytesIO(req.content)) as file:
        file.extractall(path)
    return True


def get_subreddit_posts(sub, sort='hot', lim=10):
    """Takes a subreddit string and returns an iterable of sorted posts."""
    subreddit = reddit.subreddit(sub)
    # dictionary containing sorted subreddit objects
    subreddit_sorter = {
        'hot': subreddit.hot,
        'top': subreddit.top,
        'new': subreddit.new,
        'rising': subreddit.rising,
        'controversial': subreddit.controversial
    }
    sorted_subreddit = subreddit_sorter[sort]
    return sorted_subreddit(limit=lim)


def route_posts(posts, albums, gifs, nsfw, path):
    """Routes reddit posts to the correct download function."""
    for post in posts:
        # ignore sticky posts and self posts
        if post.stickied or post.is_self:
            continue
        # check for nsfw
        if post.over_18 and not nsfw:
            continue

        url = post.url
        # check for direct image
        if not url.lower().endswith(IMAGE_FORMATS):
            url = get_image_url(url)
            # get_image_url returns none if it couldn't find link
            if not url:
                continue
        # check for gif
        if url.endswith(('.gif', '.gifv')) and not gifs:
            print(f'[-] Ignoring gif {url}')
            continue
        # check for imgur album
        if '/a/' in url:
            if not albums:
                print(f'[-] Ignoring album {url}')
                continue
            download = download_album(url, path)
        else:
            download = download_image(url, path)
        # download returns true if succeeded
        if download:
            print(f'[+] Downloaded {post.title}')


def download_from_subreddit(sub, sort='hot', lim=10, albums=True,
                            gifs=True, nsfw=False, path=DOWNLOAD_PATH):
    """Downloads images from specifed subreddit.
    Arguments:
       sub:    subreddit to download from, as a string
       sort:   sorting method of subreddit, as a string
       lim:    limit of posts to download, as an int
       albums: download albums or not, as a bool
       gifs:   download gifs or not, as a bool,
       nsfw:   download nsfw or not, as a bool
       path:   download path, as a string
    """
    posts = get_subreddit_posts(sub, sort, lim)
    route_posts(posts, albums, gifs, nsfw, path)


def download_from_subreddits(subs, sort='hot', lim=10, albums=True,
                             gifs=True, nsfw=False, path=DOWNLOAD_PATH):
    """Downloads from multiple subreddits at once using multiprocessing."""
    args = [(sub, sort, lim, albums, gifs, nsfw, path) for sub in subs]
    p = multiprocessing.Pool()
    p.starmap(download_from_subreddit, args)
    p.close()
    p.join()
