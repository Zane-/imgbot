# imagebot
Download image posts from a subreddit.

Default arguments:

	sort:   hot
	limit:  10
	albums: True
	gifs:   True
	nsfw:   True
	path:   current directory


Specify authorization variables with info from [reddit](https://www.reddit.com/prefs/apps/)
___

### Supported websites:

imgur, flickr, tinypic, reddit, wall.alphacoders, deviantart

To add more websites, modify selectors.json

Format:
```
"domain of website, including subdomains": {
	"name": "name of tag to select",
	anything: identifying attribute of tag,
	"link": attribute containing link
}
```
___

### Example Usage:
```
download_from_subreddit('earthporn', sort='top', lim=10, albums=False, nsfw=False)
download_from_subreddits(['wallpapers', 'pics', 'funny'])
```
___

Requires Python 3.6+

Third-party libraries used: [BeautifulSoup 4.6.0](https://pypi.python.org/pypi/beautifulsoup4), [praw 4.5.1](https://pypi.python.org/pypi/praw), [requests 2.16.5](https://pypi.python.org/pypi/requests)
