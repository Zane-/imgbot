from setuptools import setup

setup(
    name="imagebot",
    version="1.1.0",
    description="Subreddit image downloader.",
    author="Zane Bilous",
    author_email="zanebilous@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/Zane-/imagebot",
    py_modules=['imagebot'],
<<<<<<< HEAD
    keywords='bot reddit images',
=======
>>>>>>> dab3787b80a403b9c304e2a684798e28195d8ef5
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
)