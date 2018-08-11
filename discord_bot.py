"""
TODO:
    Improve current queueing system
    New functionality:
        PRAW - https://praw.readthedocs.io/en/latest/
            Get all replies from a parent comment
            Search for a specific post in a given subreddit
            Get top posts from a subreddit
        OpenCV - https://github.com/opencv/opencv
            ???
        JSON APIs
            Query google maps API with a specific address and return the URL for its location to the channel
"""
# necessary
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
# extra functionality
import time
import youtube_dl
import simplejson
from haar_classifier import HaarClassifier
from talking_clock  import TalkingClock
from reddit_requests import RedditBot
# online information acquisition
import lxml
from lxml import etree
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError

# loads opus here to ensure that any audio related functionality is initialised first
if not discord.opus.is_loaded():
    discord.opus.load_opus()

class Bot():
    def __init__(self, bot):
        self.bot = bot
        # extra functionality initialised
        self.h_class = HaarClassifier()
        self.clock = TalkingClock()
        self.song_list = []
        #used in audio management
        self.stop = False
        self.is_playing = False
        self.player = None
        # Insert reddit application information below
        # can change this information to a new user application
        self.reddit = RedditBot(id='',
                                secret='',
                                user='',
                                password='',
                                agent='')

    """ Each command method takes the same parameters:

    Keyword arguments:
    ctx -- message information
    args -- extra arguments passed with the message

    Command decorator arguments:
    name -- message contents required to trigger the method, along with bot_prefix
    pass_context -- allows for original message to be passed as a parameter (default True)
    no_pm -- source of message from channel or private message (default True)
    """

    @commands.command(name='detect_feline', pass_context=True, no_pm=True)
    async def cat_detect(self, ctx, args):
        """Handles the detection of cats from images in URLs given to the bot"""
        url = ctx.message.content
        # manipulates the string to take only the url
        url = str(url[14:])
        # not used, check this
        req = Request(url, headers={'User-Agent': 'Magic Browser'})
        valid_url = False
        try:
            # tries to retrieve the url
            urlretrieve(url, 'Source_Images/cat_image.jpg')
            valid_url = True

        except FileNotFoundError as err:
            # if the file is not found then the bot states the error in the current channel
            await self.bot.send_message(ctx.message.channel, 'There is an error on my end, please wait...')

        except HTTPError as err:
            # or if the url given is invalid or is blocked then a separate error is given
            await self.bot.send_message(ctx.message.channel, 'URL not accepted, cats cannot be found. Abort!')

        if valid_url:
            # if the url is valid then the haar classifier is used
            cat_msg = self.h_class.cat_detect()
            cat_check = False
            try:
                # gets the number of cats from the first letter of the returned message
                num_cats = cat_msg[:1]
                print('number of cats test {}'.format(num_cats))
                cat_check = True

            except ValueError:
                print('No cats detected...')
            # TODO: except value error to prevent error with casting to int when no cats detected
            if num_cats == 'T':
                # otherwise if there are no cats then the file is not reuploaded
                await self.bot.send_message(ctx.message.channel, cat_msg)

            elif  int(num_cats) >= 0 and cat_check:
                # the bot then uploads the edited file from the results folder
                await self.bot.send_file(ctx.message.channel, 'Results/cat_image_result.jpg')
                await self.bot.send_message(ctx.message.channel, cat_msg)

    @commands.command(name='list', pass_context=True, no_pm=True)
    async def command_list(self, ctx, args=''):
        """Prints the list of commands for the bot from a .txt file"""
        # reads the commands from the given file
        with open(file='commands.txt') as commands:
            command_list = commands.readlines()
            commands.close()
        # with the bot then printing the commands to the channel
        await self.bot.say(''.join(command_list))

    @commands.command(name='test', pass_context=True, no_pm=True)
    # can add args to get the content of the user's message
    # args has a default of an empty string to prevent no parameter 'args' error
    async def test(self, ctx, args=''):
        """A test method for ensuring the bot's functionality"""
        message = ctx.message.content
        print(message)
        await self.bot.say('you just said {}'.format(message))

    @commands.command(name='request', pass_context=True, no_pm=True)
    async def yt_player(self, ctx, args):
        """"Sets the url and plays audio for the given song"""
        # initialises an instance of the audio class
        # gets the message content and the voice channel of the user
        message = ctx.message.content
        channel = ctx.message.author.voice_channel
        await self.play_audio(message, channel)

    async def play_audio(self, message, channel):
        """A very primitive audio player for processing short youtube videos and playing them to the given voice channel
        
        Keyword arguments:
        message -- contains the youtube URL to read
        channel -- audio channel of the user that sent the message
        """
        song_url = message[9:]
        # gets the video title and sends it to the channel
        video_title = self.get_video_title(song_url)
        # appends the new song to the list of current songs
        self.song_list.append(song_url)
        # resets stop to prevent bot getting locked out of playing audio
        self.stop = False
        try:
            # checks if player is done and loops
            print(self.is_playing)
            if not self.is_playing:
                await self.bot.say("Now playing {}".format(video_title))
                voice = await self.bot.join_voice_channel(channel)
                await self.create_player(song_url, voice)
                self.is_playing = True
                while self.is_playing:
                    # checks that the song isn't done
                    while not self.player.is_done():
                        if not self.stop:
                            # asyncio.sleep required (with await keyword) as time.sleep halts entire process rather than just the event loop
                            await asyncio.sleep(1)
                        else:
                            await voice.disconnect()
                            self.is_playing = False
                    # gives time for the song to be processed and leaves a delay before checking for next song
                    # removes the song that has just been played from the list
                    self.song_list.pop(0)
                    await asyncio.sleep(3)
                    # if there are songs left in the list...
                    if len(self.song_list) > 0:
                        # plays those songs using the player
                        song_url = self.song_list[0]
                        video_title = self.get_video_title(song_url)
                        await self.bot.say("Now playing {}".format(video_title))
                        await self.create_player(song_url, voice)
                    else:
                        # if player is has no songs left in the queue, then the bot disconnects from the channel
                        await voice.disconnect()
                        self.is_playing = False

            else:
                await self.bot.say("Song already playing, please use the !queue command to add a song to the queue")
                for i in range(len(self.song_list)):
                    if i > 1:
                        self.song_list.pop(i)

        except AttributeError as att_err:
            print('The following attribute error occurred in play_audio {}'.format(att_err))

    async def create_player(self, song_url, voice, volume=0.3):
        """creates the audio player to allow for playing of youtube videos
        
        Keyword arguments:
        song_url -- youtube URL of the video to take audio from
        voice -- audio channel of the user
        volume -- how loud the bot is when playing the video (default 0.3)
        """
        # creates an object to download the youtube video from the url
        # the arguments ensure that the bot stays connected, fixes the random stop error
        self.player = await voice.create_ytdl_player(song_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        self.player.volume = volume
        # starts the youtube player to play the audio of the video to the author's audio channel
        self.player.start()

    @commands.command(name='stop', pass_context=True, no_pm=True)
    async def audio_stop(self):
        """stops the audio from playing,
        must be a method as it is a command that needs to overwrite play_audio"""
        self.stop = True

    @commands.command(name='queue', pass_context=True, no_pm=True)
    async def audio_queue(self, ctx, args=''):
        """adds a song to the queue using the !queue command"""
        song_url = ctx.message.content[7:]
        # appends the song to the list attribute for use in play_audio
        self.song_list.append(song_url)
        # also gets the video title and states the song has been added to the queue
        video_title = self.get_video_title(song_url)
        await self.bot.say("{} added to the queue".format(video_title))

    def get_video_title(self, url):
        """Gets the video title using lxml"""
        # enter the youtube url here
        youtube = etree.HTML(urlopen(url).read())
        # get xpath using firepath firefox addon
        video_title = youtube.xpath("//span[@id='eow-title']/@title")
        print(''.join(video_title))
        # stores video title then returns for use elsewhere...
        video_title = ''.join(video_title)
        return video_title

    @commands.command(name='search_subreddit', pass_context=True, no_pm=True)
    async def search_subreddit(self, ctx, args=''):
        """searches a specific subreddit for a given post"""
        # TODO: extract relevant information from user command
        counter = -1
        message = ctx.message.content
        # gets the costituent parts of the message
        split_message = message.split(' ')
        # TODO: add options for search parameters i.e. sort, time_filter etc.
        # given the command structured required, the subreddit and parameters are acquired from the split message
        subreddit = split_message[1]
        limit_list = split_message[-2:]
        limit = limit_list[1]
        command_start = len(split_message[0]) + len(split_message[1]) + 1

        if limit[0] != limit:
            # no command end required because the remainder of the message after the initial command is required
            search_query = message[command_start:]
            # TODO: add relevant error handling for when a subreddit isn't given
            search_results = self.reddit.search_subreddit(sub=subreddit, query=search_query)
            print('printing search results for no limit')
            await self.print_search_results(search_results)
        else:
            # used for retrieving the query
            command_end = len(limit_list[0] + limit_list[1])
            # gets the query by looking after the nth character in the message string
            search_query = message[command_start:-command_end]
            print('query: {}'.format(search_query))
            search_results = self.reddit.search_subreddit(sub=subreddit, query=search_query)
            print('current limit: {}'.format(limit))
            await self.print_search_results(search_results, limit=limit)

    async def print_search_results(self, search_results, limit=1, limit_check=False):
        counter = -1
        await self.bot.say('I retrieved your search query results for you!')
        # TODO: ensure all results are printed when no limit is given
        for result in search_results:
            counter += 1
            if not limit_check:
                await self.bot.say('Title: {}\nUpvotes: {}\nDownvotes: {}\nURL: {}'.format(result.title,
                                                                                           result.ups,
                                                                                           result.downs,
                                                                                           result.url))
                break
            elif counter < limit and limit_check:
                await self.bot.say('Title: {}\nUpvotes: {}\nDownvotes: {}\nURL: {}'.format(result.title,
                                                                                     result.ups,
                                                                                     result.downs,
                                                                                     result.url))
            else:
                break

    @commands.command(name='thonk', pass_context=True, no_pm=True)
    async def emoji_test(self, ctx, args=''):
        # TODO: expand this? is that really a good idea?
        await self.bot.say(':thinking:')

# insert bot token and id here, must be string
# TODO: remove this information when uploading to GitHub
bot_token = ''
bot_id = ''
# tries to initialise the bot
try:
    bot = commands.Bot(command_prefix='!')
    bot.add_cog(Bot(bot))
# if it fails, it states the reason for failure
except Exception as e:
    print('Exception setting the bot {}'.format(e))
# once the bot is ready its credentials are printed
@bot.event
async def on_ready():
    print('Logged in as\n{}\n{}\n------------'.format(bot.user.name, bot.user.id))
# and then runs the bot
bot.run(bot_token)

