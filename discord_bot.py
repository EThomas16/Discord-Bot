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
import time
import os

import cv2
from PIL import Image
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from discord import Game, opus, utils
import youtube_dl
import simplejson
import lxml
from lxml import etree
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError

import utils
from reddit_requests import RedditBot
from image_processing import ImageProcess

class Bot():
    def __init__(self, key_store_path: str):
        if not opus.is_loaded():
            opus.load_opus()

        keys = []
        with open(key_store_path, 'r') as key_file:
            keys = key_file.readlines()
            for idx, key in enumerate(keys):
                keys[idx] = key.split(":")[1].strip()

        self.bot_token = keys[0]
        self.bot_id = keys[1]

        self.song_list = []
        self.stop = False
        self.is_playing = False
        self.player = None

        self.admin_roles = ["Butcher of Reports", "Admin"]
        self.image_store_path = "Other_Images"
        self.images = Images(self.image_store_path)
        
        self.image_processing = ImageProcess()
        self.reddit = RedditBot(id=keys[2],
                                secret=keys[3],
                                user=keys[4],
                                password=keys[5],
                                agent=keys[6])

    def setup_bot(self):
        """
        Initialises the bot and sets its presence message
        """
        try:
            self.bot = commands.Bot(command_prefix='!')
            self.bot.add_cog(self)
        except Exception as err:
            print(f"Exception setting the bot {err}")
        @self.bot.event
        async def on_ready():
            # required the type argument of 1 to make the presence visible
            await self.bot.change_presence(game=Game(name="with Cookies", type=1))
            print(f"Logged in as\n{self.bot.user.name}\n{self.bot.user.id}\n------------")
        
    def init_audio(self):
        """
        Used to set up the audio player for the bot, if required
        """
        self.audio = Audio(self.bot)

    def run(self):
        """
        Uses the bot token provided from the file to run the bot
        """
        self.bot.run(self.bot_token)

    """ 
    Each command method takes the same parameters:

    Keyword arguments:
    ctx -- message information
    args -- extra arguments passed with the message

    Command decorator arguments:
    name -- message contents required to trigger the method, along with bot_prefix
    pass_context -- allows for original message to be passed as a parameter (default True)
    no_pm -- source of message from channel or private message (default True)
    """
    @commands.has_role("Admin")
    @commands.command(name='clear', pass_context=True, no_pm=True)
    async def clear_messages(self, ctx, args=''):
        """
        Removes a set number of messages from a channel based on the command structure:
        clear {number of messages to clear}
        if the number is instead all the entire channel is cleared
        this command is limited to the specified role only (default: Admin)
        """
        messages = []
        limit = ctx.message.content.split(" ")[1].strip()
        if limit.lower() is "all":
            limit = None
        elif limit.isdigit():
            limit = int(limit)
        else:
            await self.bot.say("```Invalid argument for clearing messages, please use:\n- all\n- a positive integer value```")
            return
        
        async for message in self.bot.logs_from(ctx.message.channel, limit=limit):
            messages.append(message)

        if len(messages) == 1:
            await self.bot.delete_message(messages[0])
            return
        await self.bot.delete_messages(messages)

    @commands.command(name='list_commands', pass_context=True, no_pm=True)
    async def command_list(self, ctx, args=''):
        """
        Prints the list of commands for the bot from a .txt file
        """
        with open(file='commands.txt') as commands:
            command_list = commands.readlines()
        await self.bot.say(''.join(command_list))

    @commands.command(name='admin_roles', pass_context=True, no_pm=True)
    async def admin_list(self, ctx, args=''):
        message = '\n'.join(self.admin_roles)
        await self.bot.say(f"Current admin roles being tracked are: ```{message}```")

    @commands.command(name='add_admin_role', pass_context=True, no_pm=True)
    async def set_admin(self, ctx, args=''):
        if True in utils.check_roles(self.admin_roles, ctx.message.author):
            self.admin_roles.append(' '.join(ctx.message.content.split(" ")[1:]))
            await self.bot.say("Successfully added a new administrator role")
        else:
            await self.bot.say("You do not have rights to set administrator roles")

    @commands.command(name="todo", pass_context=True, no_pm=True)
    async def add_to_todo(self, ctx, args=''):
        split_message = ctx.message.content.split(" ")
        split_message = ' '.join(split_message[1:])
        
        if split_message == "show":
            with open('todo.txt', 'r') as todo:
                todo_list = todo.readlines()
            if len(todo_list) == 0:
                message_to_say = "No features requested yet."
            else:
                message_to_say = f"This is the list of requested features:\n```{''.join(todo_list)}```"

            await self.bot.say(message_to_say)
            return

        if split_message == "clear":
            if True in utils.check_roles(self.admin_roles, ctx.message.author):
                utils.clear_file("todo.txt")
                await self.bot.say("The administrator has successfully cleared the list")
                return

            await self.bot.say("You do not have the permission to clear this list.")
            return

        if len(split_message) < 25:
            await self.bot.say("Request not detailed enough. Please write a request in the format:\nRequest title - details of request.")
            return

        user = ctx.message.author
        with open('todo.txt', 'a') as todo:
            todo.write(f"{user} -- {split_message}\n")
        await self.bot.say("Thanks for requesting a new feature for me! It will be assessed in due course, please be patient.")

    @commands.command(name='image', pass_context=True, no_pm=True)
    async def send_image(self, ctx, args=''):
        if ctx.message.content.split(" ")[1] == "show":
            message = "The following images are what I have stored.```"
            for key in self.images.image_dict:
                message += f"\n{key}"
            message += "```"
            await self.bot.say(message)
            await self.bot.delete_message(ctx.message)
            return

        await self.bot.send_file(ctx.message.channel, self.images.image_dict[ctx.message.content.split(" ")[1]])
        await self.bot.delete_message(ctx.message)

    @commands.command(name='add_image', pass_context=True, no_pm=True)
    async def add_image(self, ctx, args=''):
        if len(self.images.image_dict) > 25:
            await self.bot.say("I have too many images stored, please request the folder to be cleared before any more are added!")

        if ''.join(ctx.message.content.split(" ")[1].split(".")[-1:]) == "gif":
            ImageProcess.scrape_image(ctx.message.content.split(" ")[1], '_'.join(ctx.message.content.split(' ')[2:]))
            await self.bot.say("A fine addition to my collection!")
            await self.bot.delete_message(ctx.message)
            self.images = Images(self.image_store_path)
            return

        image, error_message = ImageProcess.scrape_image(ctx.message.content.split(" ")[1])

        if error_message:
            await self.bot.say(error_message)
            return

        cv2.imwrite(f"Other_images/{'_'.join(ctx.message.content.split(' ')[2:])}.png", image)
        self.images = Images(self.image_store_path)
        await self.bot.say("A fine addition to my collection!")
        await self.bot.delete_message(ctx.message)

    @commands.command(name='remove_image', pass_context=True, no_pm=True)
    async def remove_image(self, ctx, args=''):
        if True not in utils.check_roles(self.admin_roles, ctx.message.author):
            await self.bot.say("You do not have permission to do that.")
            await self.bot.delete_message(ctx.message)
            return

        for ext in ['.jpg', '.png', '.gif']:
            try:
                os.remove(f"{self.image_store_path}/{' '.join(ctx.message.content.split(' ')[1:])}{ext}")
                await self.bot.say("Image successfully removed.")
                await self.bot.delete_message(ctx.message)
                self.images = Images(self.image_store_path)
                return
            except:
                print("Couldn't find extension")
                pass

    @commands.command(name='spongify', pass_context=True, no_pm=True)
    async def spongify(self, ctx, args=''):
        split_message = ctx.message.content.split(" ")[1:]
        phrase = []
        for word in split_message:
            word = word.lower()
            for idx, letter in enumerate(word):
                if (idx % 2) == 0:
                    letter = letter.upper()
                phrase.append(letter)
            phrase.append(" ")

        await self.bot.delete_message(ctx.message)
        await self.bot.say(''.join(phrase))

    @commands.has_role("Admin")
    @commands.command(name='test', pass_context=True, no_pm=True)
    async def test(self, ctx, args=''):
        """
        A test method for ensuring the bot's functionality
        """
        message = ctx.message.content
        print(message)
        await self.bot.say(f"you just said {message}")
    
    @commands.command(name='tesseract', pass_context=True, no_pm=True)
    async def call_tesseract(self, ctx, args=''):
        """
        Runs tesseract OCR on an image provided through a URL
        """
        image, error_message = ImageProcess.scrape_image(ctx.message.content.split(" ")[1])
        # will meet the condition if the error_message string is not empty
        if error_message:
            await self.bot.say(error_message)
            return

        text_from_image = self.image_processing.tesseract_process(image)
        bot_message = f"Text found in image: {text_from_image}"
        if not text_from_image:
            bot_message = "No text found in image"
        
        await self.bot.say(bot_message)
        
    @commands.command(aliases=['detect_feline', 'find_cat'], pass_context=True, no_pm=True)
    async def cat_detect(self, ctx, args):
        """
        Handles the detection of cats from images in URLs given to the bot
        """
        image, error_message = ImageProcess.scrape_image(ctx.message.content.split(" ")[1])
        # will meet the condition if the error_message string is not empty
        if error_message:
            await self.bot.say(error_message)
            return

        num_cats = self.image_processing.detect_cat(image)
        if num_cats == 0:
            await self.bot.send_message(ctx.message.channel, 'There are no cats present, please try again')
        else:
            await self.bot.send_file(ctx.message.channel, 'Results/cat_image_result.jpg')
            await self.bot.send_message(ctx.message.channel, f'{num_cats} cat(s) found!')

    @commands.command(name='request', pass_context=True, no_pm=True)
    async def yt_player(self, ctx, args):
        """"
        Sets the url and plays audio for the given song
        """
        message = ctx.message.content
        channel = ctx.message.author.voice_channel
        await self.audio.play_audio(message, channel)

    @commands.command(name='stop', pass_context=True, no_pm=True)
    async def audio_stop(self):
        """
        Stops the audio from playing,
        must be a method as it is a command that needs to overwrite play_audio
        """
        self.audio.stop = True

    @commands.command(name='queue', pass_context=True, no_pm=True)
    async def audio_queue(self, ctx, args=''):
        """
        Adds a song to the queue using the !queue command
        """
        song_url = ctx.message.content.split(" ")[1]
        # appends the song to the list attribute for use in play_audio
        self.audio.song_list.append(song_url)
        # also gets the video title and states the song has been added to the queue
        video_title = self.audio.extract_video_title(song_url)
        await self.bot.say(f"{video_title} added to the queue")

    @commands.command(name='search_subreddit', pass_context=True, no_pm=True)
    async def search_subreddit(self, ctx, args=''):
        """
        Searches a specific subreddit for a given post
        """
        message = ctx.message.content
        split_message = message.split(" ")
        # TODO: add options for search parameters i.e. sort, time_filter etc.
        subreddit = split_message[1]
        limit_list = split_message[-2:]
        limit = limit_list[1]
        command_start = len(split_message[0]) + len(subreddit) + 1

        if limit[0] != limit:
            search_query = message[command_start:]
            search_results = self.reddit.search_subreddit(sub=subreddit, query=search_query)
            print('printing search results for no limit')
            await self.print_search_results(search_results)
        else:
            command_end = len(limit_list[0] + limit_list[1])
            search_query = message[command_start:-command_end]
            print('query: {}'.format(search_query))
            search_results = self.reddit.search_subreddit(sub=subreddit, query=search_query)
            print('current limit: {}'.format(limit))
            await self.print_search_results(search_results, limit=limit)

    async def print_search_results(self, search_results, limit=1, limit_check=False):
        await self.bot.say('I retrieved your search query results for you!')
        # TODO: ensure all results are printed when no limit is given
        for idx, result in enumerate(search_results):
            if not limit_check:
                await self.bot.say(f'Title: {result.title}\nUpvotes: {result.ups}\nDownvotes: {result.downs}\nURL: {result.url}')
                break
            elif idx < limit and limit_check:
                await self.bot.say(f'Title: {result.title}\nUpvotes: {result.ups}\nDownvotes: {result.downs}\nURL: {result.url}')
            else:
                break

    @commands.command(name='thonk', pass_context=True, no_pm=True)
    async def emoji_test(self, ctx, args=''):
        # TODO: expand this? is that really a good idea?
        await self.bot.say(':thinking:')

class Audio():
    def __init__(self, bot):
        self.SLEEP_TIME = 1
        self.bot = bot

        self.is_playing = False
        self.video_title = ""

        self.song_list = []
        self.stop = False
        self.player = None
        self.response = ""

    async def create_player(self, song_url, voice, volume=0.3):
        """
        Creates the audio player to allow for playing of youtube videos
        
        Keyword arguments:
        song_url -- youtube URL of the video to take audio from
        voice -- audio channel of the user
        volume -- how loud the bot is when playing the video (default 0.3)
        """
        # the arguments ensure that the bot stays connected, fixes the random stop error
        self.player = await voice.create_ytdl_player(song_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        self.player.volume = volume
        self.player.start()

    async def play_audio(self, message: str, channel):
        """
        A very primitive audio player for processing short youtube videos and playing them to the given voice channel
        
        Keyword arguments:
        message -- contains the youtube URL to read
        channel -- audio channel of the user that sent the message

        Returns:
        response -- the message for the bot to send
        """
        song_url = message.split(" ")[1]
        self.video_title = self.extract_video_title(song_url)
        if "Despacito" in self.video_title:
            await self.bot.say("That's so sad")
        self.song_list.append(song_url)
        self.stop = False
        try:
            await self.play_loop(channel, song_url)
        except AttributeError as att_err:
            print('The following attribute error occurred in play_audio {}'.format(att_err))

    def extract_video_title(self, url: str) -> str:
        """
        Gets the video title using lxml
        
        Keyword arguments:
        url -- the URL of the youtube video which is parsed to get the title from XML of the webpage
        """
        youtube = etree.HTML(urlopen(url).read())
        video_title = youtube.xpath("//span[@id='eow-title']/@title")
        print(''.join(video_title))
        video_title = ''.join(video_title)
        return video_title
    
    async def play_loop(self, channel, song_url):
        """
        Loops whilst the audio is playing, checking the status of the player throughout

        Keyword arguments:
        voice -- the voice channel to join, a discord.py voice_channel object
        song_url -- the youtube URL of the audio to play
        """
        if not self.is_playing:
            await self.bot.say(f"Now playing {self.video_title}")
            voice = await self.bot.join_voice_channel(channel)
            await self.create_player(song_url, voice)
            self.is_playing = True

            while self.is_playing:
                while not self.player.is_done():
                    await self.check_player_status(voice)
                self.song_list.pop(0)

                await asyncio.sleep(3)

                if len(self.song_list) > 0:
                    self.initialise_song(voice)
                else:
                    await voice.disconnect()
                    self.is_playing = False
        else:
            self.check_song_list()

    async def initialise_song(self, voice):
        """
        Used to create a new player if a song is added to the queue, and none are already present

        Keyword arguments:
        voice -- the voice channel to join, a discord.py voice_channel object
        """
        song_url = self.song_list[0]
        video_title = self.extract_video_title(song_url)
        self.video_title = video_title
        await self.bot.say(f"Now playing {self.video_title}")
        await self.create_player(song_url, voice)
    
    def check_song_list(self):
        """
        Loops over the list of songs in the queue to get rid of the remaining songs
        """
        for idx in range(len(self.song_list)):
            if idx > 1:
                self.song_list.pop(idx)
    
    async def check_player_status(self, voice):
        """
        Checks the current status of the audio player to see if it should stop

        Keyword arguments:
        voice -- the current voice channel the bot is in
        """
        if not self.stop:
            await asyncio.sleep(self.SLEEP_TIME)
        else:
            await voice.disconnect()
            self.is_playing = False

class Images():
    def __init__(self, source_folder):
        self.image_dict = {}
        for root, subdirs, files in os.walk(source_folder):
            for name in files:
                self.image_dict[name.split('.')[0]] = os.path.join(root, name)
        
if __name__ == "__main__":
    key_store_path = "H:/Programming/LocalStorage/discord_bot_keys.txt"
    bot = Bot(key_store_path)
    bot.setup_bot()
    bot.init_audio()
    bot.run()