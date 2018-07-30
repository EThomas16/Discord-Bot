"""
TODO:
    Improve current queueing system
    further functionality, need suggestions/ideas
"""
#necessary
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
#extra functionality
import time
import youtube_dl
import simplejson
from image_processing import ImProcess
from talking_clock  import TalkingClock
#online information acquisition
import lxml
from lxml import etree
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError

#loads opus here to ensure that any audio related functionality is initialised first
if not discord.opus.is_loaded():
    discord.opus.load_opus()

class Bot():
    def __init__(self, bot):
        self.bot = bot
        #extra functionality initialised
        self.clock = TalkingClock()
        self.song_list = []
        #used in audio management
        self.stop = False
        self.is_playing = False
        self.player = None
        self.im_process = ImProcess()

    @commands.command(name='detectFeline', pass_context=True, no_pm=True)
    async def cat_detect(self, ctx, args):
        """Handles the detection of cats from images in URLs given to the bot"""
        url = ctx.message.content
        #manipulates the string to take only the url
        url = str(url[14:])
        valid_url = await self.scrape_image(url, ctx, method="cat")
        if valid_url:
            #if the url is valid then the haar classifier is used
            cat_msg = self.im_process.cat_detect()
            cat_check = False
            try:
                #gets the number of cats from the first letter of the returned message
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
                #the bot then uploads the edited file from the results folder
                await self.bot.send_file(ctx.message.channel, 'Results/cat_image_result.jpg')
                await self.bot.send_message(ctx.message.channel, cat_msg)

    @commands.command(name='recogniseText', pass_context=True, no_pm=True)
    async def recognise_text(self, ctx, args):
        """Recognises text from a given image using google's tesseract"""
        url = ctx.message.content
        url = str(url[15:])
        valid_url = await self.scrape_image(url, ctx, method="text")
        if valid_url:
            text = self.im_process.tesseract_process()
            await self.bot.send_message(ctx.message.channel, "I think this image says...\n```{}```".format(text))

    async def scrape_image(self, url, ctx, method=""):
        #TODO: not used, check this
        req = Request(url, headers={'User-Agent': 'Magic Browser'})
        valid_url = False
        try:
            if method == "cat":
                #tries to retrieve the url
                urlretrieve(url, 'Source_Images/cat_image.jpg')
            elif method == "text":
                urlretrieve(url, 'Source_Images/tesseract_input.jpg')
            valid_url = True

        except FileNotFoundError as err:
            #if the file is not found then the bot states the error in the current channel
            await self.bot.send_message(ctx.message.channel, 'There is an error on my end, please wait...')

        except HTTPError as err:
            #or if the url given is invalid or is blocked then a separate error is given
            await self.bot.send_message(ctx.message.channel, 'URL not accepted, please try using a url that ends in .jpg or .png')

        return valid_url

    @commands.command(name='list', pass_context=True, no_pm=True)
    async def command_list(self, ctx, args=''):
        """Prints the list of commands for the bot from a .txt file"""
        #reads the commands from the given file
        with open(file='commands.txt') as commands:
            command_list = commands.readlines()
            commands.close()
        #with the bot then printing the commands to the channel
        await self.bot.say(''.join(command_list))

    @commands.command(name='test', pass_context=True, no_pm=True)
    #can add args to get the content of the user's message
    #args has a default of an empty string to prevent no parameter 'args' error
    async def test(self, ctx, args=''):
        """A test method for ensuring the bot's functionality"""
        message = ctx.message.content
        print(message)
        await self.bot.say('you just said {}'.format(message))

    @commands.command(name='request', pass_context=True, no_pm=True)
    async def yt_player(self, ctx, args):
        """"Sets the url and plays audio for the given song"""
        #initialises an instance of the audio class
        #gets the message content and the voice channel of the user
        message = ctx.message.content
        channel = ctx.message.author.voice_channel
        await self.play_audio(message, channel)

    async def play_audio(self, message, channel):
        """A very primitive audio player for processing short youtube videos and playing them to the given voice channel"""
        # main audio handling section
        song_url = message[9:]
        #gets the video title and sends it to the channel
        video_title = self.get_video_title(song_url)
        #appends the new song to the list of current songs
        self.song_list.append(song_url)
        #resets stop to prevent bot getting locked out of playing audio
        self.stop = False
        try:
            # checks if player is done and loops
            print(self.is_playing)
            if not self.is_playing:
                await self.bot.say("Now playing {}".format(video_title))
                #bot joins the voice channel
                voice = await self.bot.join_voice_channel(channel)
                #calls the create player method to create a method of getting audio from the url
                await self.create_player(song_url, voice)
                #now the audio is playing, sets the attribute to true
                self.is_playing = True
                #while the song is playing...
                while self.is_playing:
                    #checks that the song isn't done
                    while not self.player.is_done():
                        if not self.stop:
                            #asyncio.sleep required (with await keyword) as time.sleep halts entire process rather than just the event loop
                            await asyncio.sleep(1)
                        else:
                            await voice.disconnect()
                            self.is_playing = False
                    # gives time for the song to be processed and leaves a delay before checking for next song
                    # removes the song that has just been played from the list
                    self.song_list.pop(0)
                    await asyncio.sleep(3)
                    #if there are songs left in the list...
                    if len(self.song_list) > 0:
                        #plays those songs using the player
                        song_url = self.song_list[0]
                        video_title = self.get_video_title(song_url)
                        await self.bot.say("Now playing {}".format(video_title))
                        await self.create_player(song_url, voice)
                    else:
                        # if player is done, then the bot disconnects from the channel
                        await voice.disconnect()
                        self.is_playing = False

            else:
                #if the player is already playing gives a message
                await self.bot.say("Song already playing, please use the !queue command to add a song to the queue")
                for i in range(len(self.song_list)):
                    if i > 1:
                        self.song_list.pop(i)

        except AttributeError as att_err:
            print('The following attribute error occurred in play_audio {}'.format(att_err))

    async def create_player(self, song_url, voice, volume=0.3):
        """creates the audio player to allow for playing of youtube videos"""
        # creates an object to download the youtube video from the url
        # the arguments ensure that the bot stays connected, fixes the random stop error
        self.player = await voice.create_ytdl_player(song_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        self.player.volume = volume
        # starts the youtube player to play the audio of the video to the author's audio channel
        self.player.start()

    @commands.command(name='stop', pass_context=True, no_pm=True)
    async def audio_stop(self):
        """simply stops the audio from playing,
        must be a method as it is a command that needs to overwrite play_audio"""
        self.stop = True

    @commands.command(name='queue', pass_context=True, no_pm=True)
    async def audio_queue(self, ctx, args=''):
        """adds a song to the queue using the !queue command"""
        song_url = ctx.message.content[7:]
        #appends the song to the list attribute for use in play_audio
        self.song_list.append(song_url)
        #also gets the video title and states the song has been added to the queue
        video_title = self.get_video_title(song_url)
        await self.bot.say("{} added to the queue".format(video_title))

    def get_video_title(self, url):
        """Gets the video title using lxml"""
        # enter the youtube url here
        youtube = etree.HTML(urlopen(url).read())
        # get xpath using firepath firefox addon
        video_title = youtube.xpath("//span[@id='eow-title']/@title")
        print(''.join(video_title))
        #stores video title then returns for use elsewhere...
        video_title = ''.join(video_title)
        return video_title

#insert bot token and id here, must be string
bot_token = ''
bot_id = ''
#tries to initialise the bot
try:
    bot = commands.Bot(command_prefix='!')
    bot.add_cog(Bot(bot))
#if it fails, it states the reason for failure
except Exception as e:
    print('Exception setting the bot {}'.format(e))
#once the bot is ready its credentials are printed
@bot.event
async def on_ready():
    print('Logged in as\n{}\n{}\n------------'.format(bot.user.name, bot.user.id))
#and then runs the bot
bot.run(bot_token)

