import os
import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load settings from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))
TIME_TO_CHECK = float(os.getenv("TIME_TO_CHECK"))

# Create bot and set up news api
bot = commands.Bot(command_prefix="t!", intents=discord.Intents.all(), help_command=None)
news_api = "https://tagesschau.de/api2u/news/"
last_news = None # prevent the bot from sending the same news multiple times


@bot.event
async def on_ready():
  print(f"Bot: {str(bot.user)}\nID: {str(bot.user.id)}")
  newsfeed.start()

@bot.command()
async def ping(ctx):
  ping_answer = discord.Embed(title=":ping_pong: Pong!", colour=discord.Colour(0x00ff00),
                              description="Nice to meet you " + ctx.author.mention +
                                          "\n**Latency:** " + str(round(bot.latency * 1000)) + "ms")
  ping_answer.set_footer(text="created by Astral",
                         icon_url="https://cdn.discordapp.com/avatars/951884381209890877"
                                  "/ad9abec491fb314fc796b14d6f2edf83.png")
  await ctx.send(embed=ping_answer, ephemeral=True)

@bot.command()
async def news(ctx):
  global last_news
  r = requests.get(news_api)
  r = r.json()["news"][0]

  if last_news == r:
    await ctx.send("No new news available")
    return

  last_news = r
  title = r["title"]
  thumbnail = r["teaserImage"]["imageVariants"]["1x1-840"]
  url = r["shareURL"]
  first_sentence = r["firstSentence"]
  embed = discord.Embed(title=title, url=url, description=first_sentence,
                        colour=discord.Colour.blue())
  embed.set_image(url=thumbnail)
  await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
  embed = discord.Embed(title="All Commands", colour=discord.Colour.blue(), description="- t!ping - Checks the bot's latency\n- t!news - Get the latest news\n- t!help - Shows this message")
  await ctx.send(embed=embed)

@tasks.loop(minutes=TIME_TO_CHECK)
async def newsfeed():
  global last_news
  feedchannel = bot.get_channel(NEWS_CHANNEL_ID)
  r = requests.get(news_api)
  r = r.json()["news"][0]

  if last_news == r:
    return

  last_news = r
  title = r["title"]
  url = r["shareURL"]
  first_sentence = r["firstSentence"]
  thumbnail = r["teaserImage"]["imageVariants"]["1x1-840"]
  tags = [f"#{i['tag']}" for i in r["tags"]]
  embed = discord.Embed(title=title, url=url, description=f"{first_sentence}\n\nTags: {' '.join(tags)}",
                        colour=discord.Colour.blue())
  embed.set_image(url=thumbnail)
  embed.set_footer(text=f"Last update: {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}", icon_url="https://yt3.googleusercontent.com/uVxn7PluM02NDuZo-busUOpiqM0bwhXU_le_FHHjF314Z11B1kar1TK9X2RT9sIBpEdcUhhYMOU=s160-c-k-c0x00ffffff-no-rj")
  await feedchannel.send(embed=embed)


bot.run(TOKEN)
