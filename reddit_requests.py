import praw

class RedditBot():
    def __init__(self, id, secret, user, password, agent):
        self.reddit = praw.Reddit(client_id=id,
                                  client_secret=secret,
                                  username=user,
                                  password=password,
                                  user_agent=agent)
        # TODO: add blacklist of subreddits that could cause search issues i.e. me_irl, anime_irl etc.
        self.blacklist = []

    def get_hot_posts(self, sub='announcements', _limit=1, rand=False):
        if not rand:
            subreddit = self.reddit.subreddit(sub)
        elif rand:
            subreddit = self.reddit.random_subreddit(nsfw=False)
        hot_posts = subreddit.hot(limit=_limit)
        # loops through x number of hot posts to provide the details of the post
        print('Subreddit: {}'.format(subreddit.display_name))
        for post in hot_posts:
            if not post.stickied:
                print('Title: {}\nUpvotes: {}\nDownvotes: {}\nURL: {}'.format(post.title,
                                                                       post.ups,
                                                                       post.downs,
                                                                       post.url))

    def get_post_comments(self, sub, query='', _limit=1):
        search_results = self.search_subreddit(sub=sub, query=query)
        for result in search_results:
            result.comments.replace_more(limit=0)
            # shows the title and info of the post
            print('Title: {}\nUpvotes: {}\nDownvotes: {}\nURL: {}\n'.format(result.title,
                                                                          result.ups,
                                                                          result.downs,
                                                                          result.url))
            for comment in result.comments.list():
                # then the comments are shown
                print('Parent ID: {}\nComment ID: {}\nComment Body: {}\n------------------------'.format(comment.parent(),
                                                                                                         comment.id,
                                                                                                         comment.body, ))

    def get_subscriptions(self):
        # acquires a list generator of the subreddits the bot's account is subscribed to
        subs = list(self.reddit.user.subreddits(limit=None))
        for sub in subs:
            print('Subreddit: {}'.format(sub))
        # returns a listing generator of subreddits that the user is subscribed to
        return subs

    def search_subreddit(self, sub, query='', sort_filter='relevance', time='all', _limit=5, show_top=False):
        # initialised as -1 so that the limit is reached
        counter = -1
        subreddit = self.reddit.subreddit(sub)
        # sort: relevance, hot, top, new
        # time_filter: all, day, hour, month, week, year
        search_results = subreddit.search(query, sort=sort_filter, time_filter=time)
        search_results = list(search_results)
        # for if the user wishes to return a specific number of posts
        if show_top:
            for result in search_results:
                counter += 1
                # allows for limitation of the number of results returned
                if counter < _limit:
                    print('Title: {}\nUpvotes: {}\nDownvotes: {}\nURL: {}'.format(result.title,
                                                                                  result.ups,
                                                                                  result.downs,
                                                                                  result.url))
                else:
                    # breaks the loop once the post limit has been reached
                    break
        else:
            return search_results