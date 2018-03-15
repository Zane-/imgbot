import functools
import io
import json
import multiprocessing
import os
import zipfile
from urllib.parse import urlparse

import praw
import requests
from bs4 import BeautifulSoup

# urls ending with these will be recognized as direct images
IMAGE_FORMATS = ('.png', '.gif', '.gifv', '.jpg', '.jpeg')
IMAGE_SELECTORS = {
    # defeult seems to be a common pattern across domains
    "default": {"name": "meta", "property": "og:image", "link": "content"},
    "imgur.com": {"name": "link", "rel": "image_src", "link": "href"},
    "tinypic.com": {"name": "a", "class": "thickbox", "link": "href"},
    "gfycat.com": {"name": "meta", "property": "og:url", "link": "content"}
}
# use session so TCP connections are reused
session = requests.Session()

if os.path.isfile('selectors.json'):
    try:
        with open('selectors.json') as file:
            selectors = json.load(file)
    except json.decoder.JSONDecodeError:
        print('[-] Failed to decode selectors.json. Check formatting.')
    except IOError:
        print('[-] Failed to load selectors.json. Check permissions.')
    else:
        IMAGE_SELECTORS = {**IMAGE_SELECTORS, **selectors}


def get_request(url):
    """Checks for bad responses and returns request object.

    :return: request object
    :rtype: requests.model.Response
    :raises HTTPError: if request fails
    """
    # some website URL schemes do not have the protocol included
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    req = session.get(url)
    req.raise_for_status()
    return req


def get_direct_image_url(url):
    """Returns direct image url from supported page.

    :return: direct image url
    :rtype: str
    :raises ConnectionError: if the get_request fails
    :raises AttributeError: if the image could not be extracted
    """
    req = get_request(url)
    domain = urlparse(url).netloc
    selectors = IMAGE_SELECTORS.get(domain, IMAGE_SELECTORS["default"]).copy()
    link = selectors.pop('link')
    soup = BeautifulSoup(req.text, 'html.parser')
    img = soup.find(**selectors)
    return img.get(link)


def save_image(req, path):
    """Writes image to the path."""
    filename = os.path.basename(req.url)
    with open(os.path.join(path, filename), 'wb') as file:
        for chunk in req.iter_content(512):
            file.write(chunk)


def extract_album(req, path):
    """Extracts a zipped album to the path."""
    try:
        with zipfile.ZipFile(io.BytesIO(req.content)) as file:
            if zipfile.is_zipfile(file):
                file.extractall(path)
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        print("[-] Encountered bad zip file")


def get_post_image_url(url):
    """Returns url to download from reddit post.

    :return: image url or imgur album url
    :rtype: str
    :raises ConnectionError: if get_request in get_direct_image fails
    :raises AttributeError: if get_direct_image_url fails to get link
    """
    if url.endswith(IMAGE_FORMATS):
        return url
    elif '/a/' in url:  # imgur album
        return f'{url}/zip'
    else:
        return get_direct_image_url(url)


def ignore_post(url, albums, gifs, title):
    """Returns bool to ignore post."""
    if '/zip' in url and not albums:
        print(f'[-] Ignoring album: {title}')
        return True
    elif url.endswith(('.gif', '.gifv')) and not gifs:
        print(f'[-] Ignoring gif: {title}')
        return True
    else:
        return False


def route_posts(posts, albums, gifs, nsfw, path):
    """Routes reddit posts to the correct download function
    and catches any exceptions that may arise.
    """
    for post in posts:
        if any((post.stickied, post.is_self, post.over_18 and not nsfw)):
            continue

        try:
            url = get_post_image_url(post.url)
        except requests.exceptions.HTTPError:
            print(f'[-] Encountered bad url: {post.url}')
            continue
        except AttributeError:
            print(f'[-] Could not extract link from {post.url}')
            continue

        if not ignore_post(url, albums, gifs, post.title):
            try:
                req = get_request(url)
            except requests.exceptions.HTTPError:
                print(f'[-] Encountered bad url: {url}')
                continue

            if '/zip' in url:
                extract_album(req, path)
            else:
                save_image(req, path)

            print(f'[+] Downloaded {post.title}')



class ImgBot:
    """Downloads images from subreddits.

    :param str path: (optional) Download path. Defaults to '.'
    :param **auth: Authentication keywords for praw
        See below

    :Keyword Arguments:
        :param str site_name: site name of praw.ini config
        :param str client_id: client id for reddit app
        :param str client_secret: client secret for reddit app
        :param str user_agent: user agent bot projects
    """

    def __init__(self, path='.', **auth):
        self.path = path
        self.reddit = praw.Reddit(**auth)

    def get_subreddit_posts(self, sub, sort='hot', lim=10):
        """Takes a subreddit and returns an iterable of sorted posts.

        :return: reddit posts
        :rtype: praw.models.listing.generator.ListingGenerator
        """
        subreddit = self.reddit.subreddit(sub)
        sorts = {
            'hot': subreddit.hot,
            'top': subreddit.top,
            'new': subreddit.new,
            'rising': subreddit.rising,
            'controversial': subreddit.controversial
        }

        if sort in ('topyear', 'topmonth', 'topweek', 'topday', 'tophour'):
            sorted_posts = subreddit.top(limit=lim, time_filter=sort[3:])
        else:
            sorted_posts = sorts[sort](limit=lim)

        return sorted_posts

    def download(self, *sub, sort='hot', lim=10, albums=True,
                 gifs=True, nsfw=False, path=None):
        """Downloads images from a subreddit.

        :param str *sub: String(s) of subreddit(s) to download from.
        :param str sort: (optional) Sorting method of subreddit posts.
                         Must be in 'hot', 'top', 'new', 'rising',
                        'controversial','topyear', 'topmonth', 'topweek',
                        'topday', 'tophour'. Defaults to 'hot'.
        :param int lim: (optional) How many posts to download.
                        Defaults to 10.
        :param bool albums: (optional) Flag for downloading albums.
                            Defaults to True.
        :param bool gifs: (optional) Flag for downloading gifs.
                          Defaults to True.
        :param bool nsfw: (optional) Flag for downloading NSFW posts.
                          Defaults to False.
        :param str path: (optional) Download path. Defaults to '.'
        """
        path = self.path if path is None else path

        if len(sub) > 1:
            f = functools.partial(self.download, sort=sort, lim=lim,
                                  albums=albums, gifs=gifs, nsfw=nsfw,
                                  path=path)
            with multiprocessing.Pool() as p:
                p.map(f, sub)
        else:
            posts = self.get_subreddit_posts(sub[0], sort, lim)
            route_posts(posts, albums, gifs, nsfw, path)

    def __call__(self, *args, **kwargs):
        self.download(*args, **kwargs)

