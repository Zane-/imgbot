# imagebot
Download image posts from a subreddit.

Default arguments:

	sort:   hot
	limit:  10
	albums: True
	gifs:   True
	nsfw:   False
	path:   current directory


Specify authorization info in praw.ini (obtain from [reddit](https://www.reddit.com/prefs/apps/))
___

### Supported websites:

imgur, flickr, tinypic, reddit, wall.alphacoders, deviantart

To add more websites, modify selectors.json

Format:
```
"imgur.com": {  // name of domain, including www. (if in actual url) and .com
	"name": "link", // name of tag containing the image link, name of thie member must be "name"
	"rel": "image_src", // identifiying attribute, can be anything -> 'class': 'image'
	"link": "href" // attribute containing the link, name of this member must be "link"
}
```
___

### Example Usage:
```
download_from_subreddit('earthporn', sort='top', lim=10, albums=False, nsfw=True)
download_from_subreddits(['highqualitygifs', 'gifs'], gifs=False)
```
___

Requires Python 3.6+

Third-party libraries used: [BeautifulSoup 4.6.0](https://pypi.python.org/pypi/beautifulsoup4), [praw 4.5.1](https://pypi.python.org/pypi/praw), [requests 2.16.5](https://pypi.python.org/pypi/requests)
