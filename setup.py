import sys
from setuptools import setup

if sys.version_info < (3, 6):
    sys.exit('Python 3.6+ is required.')

setup(
    name="imgbot",
    version="1.2.2",
    description="Subreddit image downloader.",
    author="Zane Bilous",
    author_email="zanebilous@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/Zane-/imgbot",
    py_modules=['imgbot'],
    keywords='bot reddit images',
    install_requires=['praw', 'requests', 'bs4'],
)
