# imagebot
Download image posts from a subreddit.

Default arguments for downloading:

	sort:   hot
	limit:  10
	albums: True
	gifs:   True
	nsfw:   False
	path:   current directory


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
subs = ['pics', 'wallpapers', 'funny']
bot(subs)
```
___

### Supported websites:

imgur, flickr, tinypic, reddit, wall.alphacoders, deviantart

To add more websites, modify selectors.json

Format:
```
"domain of website, including subdomains": {
	"name": name of tag to select,
	attribute: identifying attribute of tag,
	"link": attribute containing link
}
```
___


Requires Python 3.6+

Third-party libraries used: [BeautifulSoup 4.6.0](https://pypi.python.org/pypi/beautifulsoup4), [praw 4.5.1](https://pypi.python.org/pypi/praw), [requests 2.16.5](https://pypi.python.org/pypi/requests)
