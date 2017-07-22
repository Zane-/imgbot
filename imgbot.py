import functools
import io
import json
import multiprocessing
import os
import time
import zipfile
from urllib.parse import urlparse

import praw
import prawcore
import requests
from bs4 import BeautifulSoup

# use session so TCP connections are reused across bots
session = requests.Session()
# these extensions will be recognized as direct images
IMAGE_FORMATS = ('.png', '.gif', '.gifv', '.jpg', '.jpeg')
IMAGE_SELECTORS = {
    # defeult seems to be common pattern across domains
    "default": {"name": "meta", "property": "og:image", "link": "content"},
    "imgur.com": {"name": "link", "rel": "image_src", "link": "href"},
    "tinypic.com": {"name": "a", "class": "thickbox", "link": "href"},
    "gfycat.com": {"name": "meta", "property": "og:url", "link": "content"}
}

if os.path.isfile('selectors.json'):
    try:
        with open('selectors.json') as file:
            selectors = json.load(file)
            IMAGE_SELECTORS = {**IMAGE_SELECTORS, **selectors}
    except (json.decoder.JSONDecodeError, IOError):
        print('[-] Failed to load/decode selectors.json. Check formatting.')


def get_request(url):
    """Checks for bad responses and returns request object."""
    # some website URL schemes do not have the protocol included
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    req = session.get(url)
    if not req.ok:
        raise ConnectionError
    return req


def get_image_url(url):
    """Returns direct image url from supported page."""
    try:
        req = get_request(url)
    except ConnectionError:
        raise
    # get domain name from url: http://imgur.com/xxxxx -> imgur.com
    domain = urlparse(url).netloc
    selectors = IMAGE_SELECTORS.get(domain, IMAGE_SELECTORS["default"]).copy()
    # pop link to easily unpack other keys to find
    link = selectors.pop('link')
    soup = BeautifulSoup(req.text, 'html.parser')
    img = soup.find(**selectors)
    try:
        return img.get(link)
    except AttributeError:
        raise


def download_image(req, path):
    """Downloads image to the specified path."""
    filename = os.path.basename(req.url)
    with open(os.path.join(path, filename), 'wb') as file:
        for chunk in req.iter_content(512):
            file.write(chunk)


def download_album(req, path):
    """Extracts a zipped imgur album to the specified path."""
    with zipfile.ZipFile(io.BytesIO(req.content)) as file:
        file.extractall(path)


def route_posts(posts, albums, gifs, nsfw, path):
    """Routes reddit posts to the correct download function."""
    for post in posts:
        if post.stickied or post.is_self:
            continue
        elif post.over_18 and not nsfw:
            continue

        url = post.url
        # /a/ is in imgur album url
        if '/a/' in url:
            if not albums:
                print(f'[-] Ignoring album: {post.title}')
                continue
            url = f'{url}/zip'
        else:
            if not url.lower().endswith(IMAGE_FORMATS):
                try:
                    url = get_image_url(url)
                except ConnectionError:
                    print(f'[-] Encountered bad URL: {url}')
                    continue
                except AttributeError:
                    print(f'[-] Failed to extract image: {url}')
                    continue

        if url.endswith(('.gif', '.gifv')) and not gifs:
            print(f'[-] Ignoring gif: {post.title}')
            continue

        try:
            req = get_request(url)
        except ConnectionError:
            print(f'[-] Encountered bad url: {url}')
            continue

        if '/a/' in url:
            download_album(req, path)
        else:
            download_image(req, path)
        print(f'[+] Downloaded {post.title}')



class ImgBot(object):
    """Downloads images from subreddits.

    Args:
        path: Download path as a string.
              Optional. Defaults to current directory.
        **auth: authorization kwargs for praw.Reddit.
                auth kwargs should either be site_name if using praw.ini
                or client_id, client_secret, and user_agent.

    Attributes:
        path: Path to download images to unless otherwise specified.
        reddit: An authenticated reddit object.

    Example usage:
        >> bot = imgbot.ImgBot(
               './pics',
               client_id='xxxx',
               client_secret='xxxx',
               user_agent='imgbot'
           )
        >> bot('pics')
        [+] Downloaded ...
    """

    def __init__(self, path='.', **auth):
        self.path = path
        self.reddit = praw.Reddit(**auth)

    def get_subreddit_posts(self, sub, sort='hot', lim=10):
        """Takes a subreddit and returns an iterable of sorted posts."""
        subreddit = self.reddit.subreddit(sub)
        subreddit_sorter = {
            'hot': subreddit.hot,
            'top': subreddit.top,
            'new': subreddit.new,
            'ris': subreddit.rising,
            'con': subreddit.controversial
        }
        if sort in ('topyear', 'topmonth', 'topweek', 'topday', 'tophour'):
            # slice time_filter from top
            sorted_posts = subreddit.top(limit=lim, time_filter=sort[3:])
        else:
            sorted_posts = subreddit_sorter[sort](limit=lim)
        return sorted_posts

    def validate_subreddit(self, sub):
        """Checks if a subreddit exists."""
        try:
            self.reddit.subreddits.search_by_name(sub, exact=True)
        except prawcore.exceptions.NotFound:
            print(f'[-] Subreddit {sub} does not exist.')
            return False
        else:
            return True

    def download(self, *sub, sort='hot', lim=10, albums=True,
                 gifs=True, nsfw=False, path=None):
        """Downloads images from a subreddit.

        Args:
            *sub: String(s) of subreddit(s) to download from.
            sort: Sorting method of subreddit posts. Must be in
                  ('hot', 'top', 'new', 'ris', 'con', 'topyear',
                   'topmonth', 'topweek', 'topday', 'tophour').
                  Optional. Defaults to 'hot'.
            lim: How many posts to download.
                 Optional. Defaults to 10.
            albums: Flag for downloading albums.
                    Optional. Defaults to True.
            gifs: Flag for downloading gifs.
                  Optional. Defaults to True.
            nsfw: Flag for downloading NSFW posts.
                  Optional. Defaults to False.
            path: Path to download images to.
                  Optional. Defaults to path class attribute.
        """
        if path is None:
            path = self.path
        # support multiple subs with multiprocessing
        if len(sub) > 1:
            # get rid of subreddits that don't exist
            subs = filter(self.validate_subreddit, sub)
            # create a partial preserving kwargs to use with map
            f = functools.partial(self.download, sort=sort, lim=lim,
                                  albums=albums, gifs=gifs, nsfw=nsfw,
                                  path=path)
            p = multiprocessing.Pool()
            p.map(f, subs)
            p.close()
            p.join()
        else:
            start_time = time.time()
            posts = self.get_subreddit_posts(sub[0], sort, lim)
            route_posts(posts, albums, gifs, nsfw, path)
            print(f'[+] Finished downloading from {sub[0]} in {time.time() - start_time:{2}.{3}} seconds')

    def __call__(self, *args, **kwargs):
        self.download(*args, **kwargs)
