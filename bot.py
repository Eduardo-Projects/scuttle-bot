import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import lol
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define intents
intents = discord.Intents.all()
intents.messages = True  # If your bot needs to receive messages
intents.guilds = True  # If your bot needs to work with guild (server) information

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    fetch_summoner_data.start()


@bot.command(
    name="add_summoner", help="Adds a League of Legends summoner name to track."
)
async def add_summoner(ctx, summoner_riot_id: str):
    await mongo_db.add_summoner(summoner_riot_id)
    await ctx.send(f"Summoner {summoner_riot_id} added.")


@tasks.loop(hours=24)
async def fetch_summoner_data():
    summoners = await mongo_db.get_summoners()
    for summoner in summoners:
        data = await lol_api.fetch_summoner_puuid_by_riot_id(summoner["name"])
        print(data)


bot.run(os.getenv("DISCORD_TOKEN"))
