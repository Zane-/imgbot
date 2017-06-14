"""
imagebot
Author: Zane
Last Updated: 6/13/2017

Downloads image posts from specified subreddit.
Defaults:
    - sorting:         hot
    - post limit:      10
    - download albums: True
    - download dir:    current directory
Only supports imgur and direct image links.

Usage:
    - Specify the download path in the DOWNLOAD_PATH variable,
      or in the argument to download_from_subreddit.

    - Specify subreddit, sort, limit, in call to
      download_from_subreddit, or change defaults.
      Example: download_from_subreddit('wallpapers', 'top', 10)

    - Specify bot credentials in module-level variables.
"""
import io
import multiprocessing
import os
import zipfile

import praw
import requests
from bs4 import BeautifulSoup

# User Config: obtain this info at https://www.reddit.com/prefs/apps/
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = 'imagebot 1.0'
REDIRECT_URI = 'http://localhost:8080'
DOWNLOAD_PATH = '.'

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     redirect_uri=REDIRECT_URI,
                     user_agent=USER_AGENT)
# use session so TCP connections are reused
s = requests.Session()


def get_request(url):
    """Checks for bad responses and returns request object."""
    req = s.get(url)
    if req.status_code != requests.codes.ok:
        print(f'Encountered bad url: {url}')
        return None
    return req


def get_image_url(url):
    """Returns direct image url fropm imgur page."""
    req = get_request(url)
    if req is None:
        return None
    soup = BeautifulSoup(req.text, 'html.parser')
    img = soup.find('link', rel='image_src')
    if img:
        return img.get("href")
    else:
        print(f'Encountered unsupported url: {url}')
        return None


def download_image(url, path=DOWNLOAD_PATH, chunksize=512):
    """Downloads image to the specified download path."""
    req = get_request(url)
    if req is None:
        return None
    filename = os.path.basename(url)
    with open(os.path.join(path, filename), 'wb') as file:
        for chunk in req.iter_content(chunksize):
            file.write(chunk)


def download_album(url, path=DOWNLOAD_PATH):
    """Downloads an album from imgur as a zip file and extracts it."""
    req = get_request(f'{url}/zip')
    if req is None:
        return None
    with zipfile.ZipFile(io.BytesIO(req.content)) as file:
        file.extractall(path)


def is_direct_image(url):
    """Checks if a url is a direct image url."""
    return url.lower().endswith(('.png', '.gif', '.jpg', '.jpeg'))


def get_subreddit_posts(sub, lim, sort='hot'):
    """Takes a subreddit string and returns an iterable of sorted posts."""
    subreddit = reddit.subreddit(sub)
    subreddit_sort = {
        'hot': subreddit.hot,
        'top': subreddit.top,
        'new': subreddit.new
    }
    return subreddit_sort[sort](limit=lim)


def route_post(post, albums, path):
    """Routes a reddit post object to the correct download function."""
    if post.stickied or post.is_self:
            return None
    url = post.url
    # check for imgur album
    if '/a/' in url:
        if not albums:
            return None
        download_album(url, path)
    else:
        if not is_direct_image(url):
            url = get_image_url(url)
        if url:
            download_image(url, path)
    if url:
        print(f'Downloaded {url}')


def download_from_subreddit(sub, sort='hot', lim=10, albums=True,
                            path=DOWNLOAD_PATH):
    """Downloads images from specifed subreddit.
    Arguments:
       sub:    subreddit to download from, as a string
       sort:   sorting method of subreddit, as a string
               limited to 'new', 'hot', and 'top'
       lim:    limit of posts to download, as an int
       albums: download albums or not, as a bool
       path:   download path, as a string
    """
    posts = get_subreddit_posts(sub, lim, sort)
    for post in posts:
        route_post(post, albums, path)


def download_from_subreddits(subs, sort='hot', lim=10, albums=True,
                             path=DOWNLOAD_PATH):
    """Downloads from multiple subreddits, creating a process for each sub.
    Subreddits must be contained in an iterable. Passing too many
    subreddits will start to become inefficient.
    """
    processes = []
    for sub in subs:
        p = multiprocessing.Process(target=download_from_subreddit,
                                    args=(sub, sort, lim, albums, path))
        processes.append(p)
        p.start()
    # clean up processes
    for p in processes:
        p.join()
