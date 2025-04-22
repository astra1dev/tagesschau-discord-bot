"""
tagesschau-discord-bot: discord bot using the tagesschau API to get news

https://github.com/astra1dev/tagesschau-discord-bot
"""

import os
import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime
from dotenv import load_dotenv
import psutil
import datetime
import time

# Load settings from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))
TIME_TO_CHECK = float(os.getenv("TIME_TO_CHECK"))

# Create bot and set up news api
bot = commands.Bot(command_prefix=None, intents=discord.Intents.all(), help_command=None)
news_api = "https://tagesschau.de/api2u/news/"
last_news = None # prevent the bot from sending the same news multiple times

# for uptime calculation
start_time = time.time()


@bot.event
async def on_ready() -> None:
  """
  Called when the client is done preparing the data received from Discord.
  Usually after login is successful and the Client.guilds and co. are filled up.
  :return: None
  """
  i = 0
  print(f"[✅] {bot.user.name}#{bot.user.discriminator} (ID: {bot.user.id}, Display Name: {bot.user.display_name}) "
        f"is connected to the following servers:")
  for _ in bot.guilds:
    print(f"{str(i + 1)}: {str(bot.guilds[i].name)}, ID: {str(bot.guilds[i].id)}")
    i += 1

  await bot.tree.sync()
  newsfeed.start()
  print("\n[✅] Slash commands loaded.")


@bot.tree.command(name="info", description="Shows the bot's status, latency and more")
async def info(interaction: discord.Interaction) -> None:
  """
  Shows the bot's status, latency and more
  :param interaction: The discord interaction object
  :return: None
  """
  # Calculate uptime
  uptime_seconds = time.time() - start_time
  days, remainder = divmod(uptime_seconds, 86400)
  hours, remainder = divmod(remainder, 3600)
  minutes, seconds = divmod(remainder, 60)

  if days > 0:
    uptime = f"{int(days)} day{'s' if days > 1 else ''}, {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
  else:
    uptime = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

  connected_since = datetime.datetime.fromtimestamp(start_time, datetime.UTC).strftime("%Y-%m-%d, %H:%M:%S")
  creation_time = bot.user.created_at.strftime("%Y-%m-%d, %H:%M:%S")

  shard_id = bot.shard_id if bot.shard_id is not None else "Not Sharded"

  # Get CPU and RAM usage
  cpu_usage = psutil.cpu_percent(interval=1)
  ram = psutil.virtual_memory()
  ram_total = ram.total / (1024 ** 3)  # Convert bytes to GB
  ram_used = ram.used / (1024 ** 3)
  ram_usage = ram.percent

  embed = discord.Embed(title=":pencil: Bot Information", colour=discord.Colour(0x00ff00),
                        timestamp=datetime.datetime.now(datetime.UTC))
  embed.add_field(name="⏱️ Latency", value=f"{str(round(bot.latency * 1000))}ms")
  embed.add_field(name="🌍 Servers", value=f"{str(len(bot.guilds))}")
  embed.add_field(name="👥 Users", value=f"{str(len([member for guild in bot.guilds for member in guild.members]))}")
  embed.add_field(name="⏳ Uptime", value=f"{uptime}")
  embed.add_field(name="🕰️ Connected Since", value=f"{connected_since}")
  embed.add_field(name="🗓️ Creation Time", value=f"{creation_time}")
  embed.add_field(name="💻 CPU Usage", value=f"{cpu_usage}%")
  embed.add_field(name="💻 RAM Usage", value=f"{ram_usage}% ({ram_used:.2f} GB / {ram_total:.2f} GB)")
  embed.add_field(name="⚙️ Shards", value=f"{shard_id} / {bot.shard_count}")
  embed.set_footer(text="created by Astral",
                   icon_url="https://cdn.discordapp.com/avatars/951884381209890877"
                            "/ad9abec491fb314fc796b14d6f2edf83.png")
  await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="news", description="Get the latest news")
async def news(interaction: discord.Interaction) -> None:
  """
  Fetches the latest news from the tagesschau API and sends it in an embed
  :param interaction: The discord interaction object
  :return: None
  """
  global last_news
  r = requests.get(news_api)
  r = r.json()["news"][0]

  if last_news == r:
    embed = discord.Embed(title=":x: Error", colour=discord.Colour(0xff0000), description="No new news available")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    return

  last_news = r
  title = r["title"]
  try:
    url = r["shareURL"]
  except KeyError:
    url = ""
  try:
    first_sentence = r["firstSentence"]
  except KeyError:
    first_sentence = ""
  thumbnail = r["teaserImage"]["imageVariants"]["1x1-840"]
  tags = [f"#{i['tag']}" for i in r["tags"]]
  embed = discord.Embed(title=title, url=url, description=f"{first_sentence}\n\nTags: {' '.join(tags)}",
                        colour=discord.Colour.blue())
  embed.set_image(url=thumbnail)
  embed.set_footer(text=f"Last update: {datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d, %H:%M:%S")}",
                   icon_url="https://cdn.discordapp.com/avatars/1284859085967069366/75bd7fbf552aceaa9bebfef4433840f4")
  await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Shows all commands")
async def help(interaction: discord.Interaction) -> None:
  """
  Sends a list of all commands in an embed
  :param interaction: The discord interaction object
  :return: None
  """
  embed = discord.Embed(title="All Commands", colour=discord.Colour.blue(),
                        description="- `/ping` - Shows the bot's status, latency and more\n- `/news` - Get the latest "
                                    "news\n- `/help` - Shows this message")
  await interaction.response.send_message(embed=embed, ephemeral=True)


@tasks.loop(minutes=TIME_TO_CHECK)
async def newsfeed() -> None:
  """
  Fetches the latest news from the tagesschau API and sends it in an embed
  :return: None
  """
  global last_news
  feedchannel = bot.get_channel(NEWS_CHANNEL_ID)
  r = requests.get(news_api)
  r = r.json()["news"][0]

  if last_news == r:
    return

  last_news = r
  title = r["title"]
  try:
    url = r["shareURL"]
  except KeyError:
    url = ""
  try:
    first_sentence = r["firstSentence"]
  except KeyError:
    first_sentence = ""
  thumbnail = r["teaserImage"]["imageVariants"]["1x1-840"]
  tags = [f"#{i['tag']}" for i in r["tags"]]
  embed = discord.Embed(title=title, url=url, description=f"{first_sentence}\n\nTags: {' '.join(tags)}",
                        colour=discord.Colour.blue())
  embed.set_image(url=thumbnail)
  embed.set_footer(text=f"Last update: {datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d, %H:%M:%S")}",
                   icon_url="https://cdn.discordapp.com/avatars/1284859085967069366/75bd7fbf552aceaa9bebfef4433840f4")
  await feedchannel.send(embed=embed)


bot.run(TOKEN)
