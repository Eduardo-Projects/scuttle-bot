import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import os
from dotenv import load_dotenv
import datetime

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
    weekly_report.start()


@bot.command(
    name="add_summoner", help="Adds a League of Legends summoner name to track."
)
async def add_summoner(ctx, summoner_riot_id: str):
    summoner_added = await mongo_db.add_summoner(summoner_riot_id)
    if summoner_added:
        await ctx.send(f"Summoner {summoner_riot_id} added.")
    else:
        await ctx.send(f"Failed to add summoner {summoner_riot_id}.")


@bot.command(name="stats")
async def stats(ctx, summoner_riot_id: str):
    await ctx.send(f"*Loading ranked solo queue stats for **{summoner_riot_id}** ...*")

    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        stats = await lol_api.fetch_summoner_stats(puuid)
        formatted_stats_data = "\n".join(
            [f"{key} {value}" for key, value in stats.items()]
        )
        formatted_stats_output = "\n>>> {}".format(formatted_stats_data)

        await ctx.send(
            f"**Summoner {summoner_riot_id}'s stats for the past 7 days.** {formatted_stats_output}"
        )
    else:
        await ctx.send(f"Error getting data for summoner **{summoner_riot_id}**.")


@bot.command(name="last_game")
async def stats(ctx, summoner_riot_id: str):
    await ctx.send(
        f"*Loading last game ranked solo queue stats for **{summoner_riot_id}** ...*"
    )

    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        stats = await lol_api.fetch_summoner_stats_last_game(puuid)
        formatted_stats_data = "\n".join(
            [f"{key} {value}" for key, value in stats.items()]
        )
        formatted_stats_output = "\n>>> {}".format(formatted_stats_data)

        await ctx.send(
            f"**Summoner {summoner_riot_id}'s stats for the last game.** {formatted_stats_output}"
        )
    else:
        await ctx.send(f"Error getting data for summoner **{summoner_riot_id}**.")


@bot.command(name="test_weekly_report")
async def test_weekly_report(ctx):
    await ctx.send(f"*Loading weekly report ...*")

    summoners = await mongo_db.get_summoners()
    summoner_names = []
    stats = await lol_api.fetch_summoner_stats_batch(summoners)

    for summoner in summoners:
        summoner_names.append(summoner["name"])

    formatted_stats_data = [
        f"{item['Key']}:\n{item['Name']} - {item['Max Value']}\n" for item in stats
    ]
    formatted_stats_data = "\n".join(formatted_stats_data)
    formatted_stats_output = "\n>>> {}".format(formatted_stats_data)
    formatted_names = " | ".join(summoner_names)

    await ctx.send(
        f"**Weekly Report. Summoners analyzed: {formatted_names}** {formatted_stats_output}"
    )


@tasks.loop(minutes=1)
async def weekly_report():
    now = datetime.now()

    # check if it is 8:00pm on a Sunday
    if now.weekday() == 6 and now.hour == 20 and now.minute == 00:
        channel_id = os.getenv("BOT_CHANNEL_ID")
        channel = bot.get_channel(int(channel_id))

        if channel:
            await channel.send(f"*Loading weekly report ...*")

            summoners = await mongo_db.get_summoners()
            summoner_names = []
            stats = await lol_api.fetch_summoner_stats_batch(summoners)

            for summoner in summoners:
                summoner_names.append(summoner["name"])

            formatted_stats_data = [
                f"{item['Key']}:\n{item['Name']} - {item['Max Value']}\n"
                for item in stats
            ]
            formatted_stats_data = "\n".join(formatted_stats_data)
            formatted_stats_output = "\n>>> {}".format(formatted_stats_data)
            formatted_names = " | ".join(summoner_names)

            await channel.send(
                f"**Weekly Report. Summoners analyzed: {formatted_names}** {formatted_stats_output}"
            )
        else:
            print("Channel not found.")


bot.run(os.getenv("DISCORD_TOKEN"))
