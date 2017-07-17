from setuptools import setup

setup(
    name="imgbot",
    version="1.1.0",
    description="Subreddit image downloader.",
    author="Zane Bilous",
    author_email="zanebilous@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/Zane-/imgbot",
    py_modules=['imgbot'],
    keywords='bot reddit images',
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
)
