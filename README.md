# imagebot
Download image posts from a subreddit.

Only supports imgur and direct images for now.

Default values:

	sort: hot
	limit: 10
	albums: True
	download path: current directory


Specify authorization variables with info from [reddit](https://www.reddit.com/prefs/apps/)
___

### Example Usage:

download_from_subreddit('wallpapers', sort='top', lim=10, albums=False)
___

Requires Python 3.6+

Third-party libraries used: BeautifulSoup 4.6.0, praw 4.5.1, requests 2.16.5
