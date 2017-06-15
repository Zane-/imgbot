"""
imagebot
Author: Zane
Last Updated: 6/15/2017

Downloads image posts from subreddits.

Default arguments:
    - sorting:         hot
    - post limit:      10
    - download albums: True
    - download gifs:   True
    - download nsfw:   True
    - download dir:    current directory

Usage:
    - Specify the download path in the DOWNLOAD_PATH variable,
      or in the argument to download_from_subreddit.

    - Specify client ID and client secret in module-level variables.

    - Current websites supported:
        imgur, flickr, tinypic, wall.alphacoders, and deviantart
        To add more websites, modify selectors.json:
            Format:
                "name of website, including subdomains": {
                    "name": name of tag to select,
                    anything: identifying attribute of tag,
                    "link": attribute containing link
                }
"""
import io
import json
import multiprocessing
import os
import zipfile

import praw
import requests
from bs4 import BeautifulSoup

# User Config: obtain this info at https://www.reddit.com/prefs/apps/
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = 'imagebot 1.1'
REDIRECT_URI = 'http://localhost:8080'

DOWNLOAD_PATH = '.'
# add supported image formats here
IMAGE_FORMATS = ('.png', '.gif', '.gifv', '.jpg', '.jpeg')

with open('selectors.json', 'r') as f:
    IMAGE_SELECTORS = json.load(f)

REDDIT = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    user_agent=USER_AGENT
)

# use Session so TCP connections are reused
S = requests.Session()


def get_request(url):
    """Checks for bad responses and returns request object."""
    # some website URL schemes do not have the protocol included
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    req = S.get(url)
    if req.status_code != 200:
        print(f'Encountered bad url: {url}')
        return None
    return req


def get_image_url(url):
    """Returns direct image url from supported page."""
    req = get_request(url)
    if req is None:
        return None
    # split the domain name from the url
    domain = url.split('//')[-1].split('/')[0]
    error_msg = f'[-] Encountered unsupported URL: {url} with domain {domain}'

    try:
        # copy the dict because we pop from it
        selectors = IMAGE_SELECTORS[domain].copy()
    except KeyError:
        print(error_msg)
        return None

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
    subreddit = REDDIT.subreddit(sub)
    subreddit_sorter = {
        'hot': subreddit.hot,
        'top': subreddit.top,
        'new': subreddit.new,
        'rising': subreddit.rising,
        'controversial': subreddit.controversial
    }
    sorted_subreddit = subreddit_sorter[sort]
    return sorted_subreddit(limit=lim)


def route_post(post, albums, gifs, nsfw, path):
    """Routes a reddit post object to the correct download function."""
    # ignore sticky posts and self posts
    if post.stickied or post.is_self:
        return None
    if post.over_18 and not nsfw:
        return None

    url = post.url
    # check for direct image
    if not url.lower().endswith(IMAGE_FORMATS):
        url = get_image_url(url)
    if not url:
        return None
    # check for gif
    if url.endswith(('.gif', '.gifv')) and not gifs:
        print(f'[-] Ignoring gif {url}')
        return None

    # check for imgur album
    if '/a/' in url:
        if not albums:
            print(f'[-] Ignoring album {url}')
            return None
        download = download_album(url, path)
    else:
        download = download_image(url, path)
    # download returns true if succeeded
    if download:
        print(f'[+] Downloaded {post.title}')


def download_from_subreddit(sub, sort='hot', lim=10, albums=True,
                            gifs=True, nsfw=True, path=DOWNLOAD_PATH):
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
    for post in posts:
        route_post(post, albums, gifs, nsfw, path)


def download_from_subreddits(subs, sort='hot', lim=10, albums=True,
                             gifs=True, nsfw=True, path=DOWNLOAD_PATH):
    """Downloads from multiple subreddits, creating a process for each sub.
    Subreddits must be contained in an iterable. Passing too many
    subreddits will start to become slow.
    """
    processes = []
    for sub in subs:
        process = multiprocessing.Process(target=download_from_subreddit,
                                          args=(sub, sort, lim,
                                                albums, gifs, nsfw, path))
        processes.append(process)
        process.start()
    # clean up processes
    for process in processes:
        process.join()
