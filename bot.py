import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import os
from dotenv import load_dotenv
import json

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


@bot.command(
    name="add_summoner", help="Adds a League of Legends summoner name to track."
)
async def add_summoner(ctx, summoner_riot_id: str):
    await mongo_db.add_summoner(summoner_riot_id)
    await ctx.send(f"Summoner {summoner_riot_id} added.")


@bot.command(name="stats")
async def stats(ctx, summoner_riot_id: str):
    await ctx.send(f"Loading ranked solo queue stats for {summoner_riot_id}...")

    matches_data = await lol_api.fetch_match_data_by_range(7, summoner_riot_id)
    stats = await lol_api.get_stats_by_summoner(matches_data, summoner_riot_id)

    formatted_stats_output = "\n".join(
        [f"{key} {value}" for key, value in stats.items()]
    )

    await ctx.send(
        f"Summoner {summoner_riot_id}'s stats for the past 7 days. \n{formatted_stats_output}"
    )


bot.run(os.getenv("DISCORD_TOKEN"))
