# imagebot
Download image posts from a subreddit.

Default keyword arguments:

	sort (string in 'hot', 'top', 'new', 'controversial', 'rising'): 'hot'
	limit (int):  10
	albums (bool): True
	gifs (bool):   True
	nsfw (bool):   False
	path (string):   current directory


Use praw.ini for authorization and pass site_name keyword argument to ImageBot,
or pass client_id, client_secret, and user_agent keyword arguments.
___

### Example Usage:
```python
import imagebot
# using praw.ini for authorization
bot = imagebot.ImageBot(site_name='imagebot')
# or passing in auth kwargs
bot2 = imagebot.ImageBot(client_id='notactualID', client_secret='notactualsecret', user_agent='imagebot')
bot.download('gifs', gifs=False, path='./gifs', lim=20, sort='controversial')
# alternate download call
bot('pics', lim=100)
# download from multiple subreddits
bot('pics', 'wallpapers', 'funny', lim=5, gifs=False, path='./pics', sort='top')
# set download path through attribute, argument, or on instantiation
bot.path = './downloads'
bot3 = imagebot.ImageBot('./downloads', site_name='imagebot')
```
___

### Supported websites:

imgur, flickr, tinypic, reddit, wall.alphacoders, deviantart

To add more websites, modify selectors.json

Format:
```python
"domain of website, including subdomains": {
	"name": name of tag to select,
	attribute: identifying attribute of tag,
	"link": attribute containing link
}
```
___


Requires Python 3.6+

Third-party libraries used: [BeautifulSoup 4.6.0](https://pypi.python.org/pypi/beautifulsoup4), [praw 5.0.1](https://pypi.python.org/pypi/praw), [requests 2.16.5](https://pypi.python.org/pypi/requests)
