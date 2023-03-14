#
import os
import discord
from discord.ext import commands, tasks
import requests


####################################

TOKEN = [YOUR_TOKEN_HERE]  # Put the token of your bot here
CHANNEL = [YOUR_CHANNEL_ID_HERE]  # Channel where the bot sends the latest news every x minutes
TIME = [YOUR_TIME_HERE]    # How often do you want the bot to send the latest news? (in minutes)

####################################


bot = commands.Bot(command_prefix="t!", intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
  print("Online!")
  print("\nBot:" + str(bot.user))
  print("\nID:" + str(bot.user.id))
  newsfeed.start()

@bot.command()
async def ping(ctx):
  await ctx.send("Pong")

@bot.command()
async def news(ctx):
  r = requests.get("https://www.tagesschau.de/api2/news/")
  r = r.json()["news"][0]
  title = r["title"]
  try:
    thumbnail = r["teaserImage"]["mittelgross1x1"]["imageurl"]
    URL = r["shareURL"]
    firstSentence = r["firstSentence"]
    embed = discord.Embed(title=title, url=URL, description=firstSentence,   
                          colour=discord.Colour.blue())
    embed.set_image(url=thumbnail)
    await ctx.send(embed=embed)
  except KeyError:
    await ctx.send("Error sending news")

@bot.command()
async def help(ctx):
  embed = discord.Embed(title="All Commands", colour=discord.Colour.blue(), description="t!ping, t!news")
  await ctx.send(embed=embed)

@tasks.loop(minutes=TIME)
async def newsfeed():
  feedchannel = bot.get_channel(CHANNEL)
  r = requests.get("https://www.tagesschau.de/api2/news/")
  r = r.json()["news"][0]
  title = r["title"]
  try:
    URL = r["shareURL"]
    firstSentence = r["firstSentence"]
    thumbnail = r["teaserImage"]["mittelgross1x1"]["imageurl"]
    embed = discord.Embed(title=title, url=URL, description=firstSentence, 
                        colour=discord.Colour.blue())
    embed.set_image(url=thumbnail)
    await feedchannel.send(embed=embed)
  except KeyError:
    pass


bot.run(TOKEN)
