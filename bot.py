import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define intents
intents = discord.Intents.default()  # This enables only the default intents
intents.messages = True  # If your bot needs to receive messages
intents.guilds = True  # If your bot needs to work with guild (server) information

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    fetch_summoner_data.start()


@bot.command(
    name="add_summoner", help="Adds a League of Legends summoner name to track."
)
async def add_summoner(ctx, summoner_name: str):
    mongo_db.add_summoner(summoner_name)
    await ctx.send(f"Summoner {summoner_name} added.")


@tasks.loop(hours=24)
async def fetch_summoner_data():
    summoners = await mongo_db.get_summoners()
    print(summoners)
    for summoner in summoners:
        data = await lol_api.fetch_summoner_data(summoner["name"])
        print(data)


bot.run(os.getenv("DISCORD_TOKEN"))
