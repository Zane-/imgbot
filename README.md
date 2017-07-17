# imgbot
Download image posts from subreddits.

requires python 3.6+

___

### Installation

`pip install imgbot`

Or download and extract source and run `python setup.py install`    in the same directory.

___

### Example Usage:
```python
import imgbot
# using praw.ini for authorization
bot = imgbot.ImgBot(site_name='imgbot')
# or passing in auth kwargs
bot2 = imgbot.ImgBot(
	client_id='notactualID',
	client_secret='notactualsecret',
	user_agent='imgbot'
)
bot.download('gifs', gifs=False, path='./gifs', lim=20, sort='con')
# alternate download call
bot('pics', sort='topmonth', lim=100)
# download from multiple subreddits
bot('pics', 'wallpapers', 'funny', lim=5, gifs=False, path='./pics', sort='topweek')
# set download path through attribute, argument, or on instantiation
bot.path = './downloads'
bot3 = imgbot.ImgBot('./downloads', site_name='imgbot')
```
___

Download arguments:

	sort (string): Subreddit sorting method. Defaults to 'hot'.
	               Can be in 'hot', 'new', 'ris', 'con', 'top', 'topyear' 'topmonth', 'topweek', 'topday', 'tophour'
	limit (int):   Amount of posts to download. Defaults to 10.
	albums (bool): download albums or not. Defaults to True.
	gifs (bool):   download gifs or not. Defaults to True.
	nsfw (bool):   Download nsfw or not. Defaults to False.
	path (string): Path to download from. Defaults to current directory.


To authenticate the bot, pass in client_id, client_secret, and user_agent to ImgBot, or pass site_name to use praw.ini

Go to https://www.reddit.com/prefs/apps/ if you do not already have API keys.

### Supported websites:

imgur, flickr, tinypic, reddit, wall.alphacoders, deviantart, gfycat

To add more websites, create a file named 'selectors.json' in the directory the bot is run from.

Format:
```python
{
	"domain of website, including subdomains": {
		"name": name of tag to select,
		attribute: identifying attribute of tag,
		"link": attribute containing link
	}
}

// so if you had a site called images.example.com, the image link was in a link tag
// the identifying attribute of the link was rel='image_src'
// and the attribute containing the link was href, selectors.json would look like:
{
	"images.example.com": {
        "name": "link",
        "rel": "image_src",
        "link": "href"
     }
 }
 // and the bot would now be able to extract image links from images.examples.com
```
___


Third-party libraries used: [BeautifulSoup 4.6.0](https://pypi.python.org/pypi/beautifulsoup4), [praw 5.0.1](https://pypi.python.org/pypi/praw), [requests 2.16.5](https://pypi.python.org/pypi/requests)
