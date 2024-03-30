import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import os
from dotenv import load_dotenv
from datetime import datetime

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


# Event that runs only when bot first starts up
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

    weekly_report_automatic.start()
    print("Started weekly report automatic job.")

    fetch_all_summoner_match_data.start()
    print("Started automatic summoner match data fetch job.")


# Runs when bot is added to new discord server
# Adds discord server data to database
@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name} with Guild ID: {guild.id} ")
    await mongo_db.add_guild(guild.name, guild.id)


# Adds riot id and puuid to summoners list of the corresponding discord server in database
@bot.command(
    name="add_summoner", help="Adds a League of Legends summoner name to track."
)
async def add_summoner(ctx, summoner_riot_id: str):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    summoner_added = await mongo_db.add_summoner(summoner_riot_id, guild_id)

    if summoner_added:
        await ctx.send(f"Summoner {summoner_riot_id} added.")
    else:
        await ctx.send(f"Failed to add summoner {summoner_riot_id}.")


# Displays a list of all summoners for given discord server
@bot.command(
    name="show_summoners",
    help="Displays a list of all summoners for given discord server",
)
async def show_summoners(ctx):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_name = ctx.guild.name
    guild_id = ctx.guild.id
    summoners = await mongo_db.get_summoners(guild_id)

    if summoners:
        formatted_output = ", ".join([summoner["name"] for summoner in summoners])
        await ctx.send(f"{guild_name}'s Summoners: {formatted_output}")
    else:
        await ctx.send(
            f"{guild_name} does not have any summoners. Add summoners by typing !add_summoner 'RiotName #Tag'"
        )


# Displays a summoner's formatted weekly stats
@bot.command(
    name="stats_weekly", help="Retrives a summoner's formatted weekly solo queue stats."
)
async def stats_weekly(ctx, summoner_riot_id: str):
    await ctx.send(f"*Loading ranked solo queue stats for **{summoner_riot_id}** ...*")

    # Make sure riot id exists
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        stats = await lol_api.fetch_summoner_stats_by_day_range(puuid, range=7)
        formatted_stats_data = "\n".join(
            [f"{key}: {value}" for key, value in stats.items()]
        )
        formatted_stats_data = "\n>>> {}".format(formatted_stats_data)

        await ctx.send(
            f"**Summoner {summoner_riot_id}'s stats for the past 7 days.** {formatted_stats_data}"
        )
    else:
        await ctx.send(
            f"Error getting data for summoner **{summoner_riot_id}**. Make sure this user exists."
        )


# Displays discord server's formatted overall stats for all summoners
@bot.command(
    name="weekly_report", help="Displays discord server's formatted overall stats"
)
async def weekly_report(ctx):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_name = ctx.guild.name
    guild_id = ctx.guild.id

    await ctx.send(
        f"*Loading weekly report for **{guild_name}**, this may take a few minutes ...*"
    )

    stats = await lol_api.fetch_weekly_report(guild_id)

    if stats:
        summoners = await mongo_db.get_summoners(guild_id)
        summoners_names = [summoner["name"] for summoner in summoners]
        summoners_names_formatted = ", ".join(summoners_names)
        formatted_stats_data = [
            f"{item['Key']}:\n{item['Name']} - {item['Max Value']}\n" for item in stats
        ]
        formatted_stats_data = "\n".join(formatted_stats_data)
        formatted_stats_output = "\n>>> {}".format(formatted_stats_data)

        await ctx.send(
            f"**Weekly Report. Summoners analyzed: {summoners_names_formatted}** {formatted_stats_output}"
        )
    else:
        await ctx.send(
            f"**Error fetching weekly report. Make sure you have added summoners to your server with !add_summoner 'Name #Tag'**"
        )


# Automatic task that fetches and displays a weekly report every Sunday at 8:00 pm
@tasks.loop(minutes=1)
async def weekly_report_automatic():
    now = datetime.now()

    # check if it is 8:00 pm on a Sunday
    if now.weekday() == 6 and now.hour == 20 and now.minute == 0:
        all_guilds = bot.guilds
        for guild in all_guilds:
            guild_id = guild.id
            channel_id = await mongo_db.get_main_channel(guild_id)

            print(f"\nGetting weekly report for Guild with ID: {guild_id}")

            if channel_id:
                channel = bot.get_channel(channel_id)

                if channel:
                    await channel.send(
                        f"*Loading weekly report, this may take a few minutes ...*"
                    )

                    stats = await lol_api.fetch_weekly_report(guild_id)

                    if stats:
                        summoners = await mongo_db.get_summoners(guild_id)
                        summoners_names = [summoner["name"] for summoner in summoners]
                        summoners_names_formatted = ", ".join(summoners_names)
                        formatted_stats_data = [
                            f"{item['Key']}:\n{item['Name']} - {item['Max Value']}\n"
                            for item in stats
                        ]
                        formatted_stats_data = "\n".join(formatted_stats_data)
                        formatted_stats_output = "\n>>> {}".format(formatted_stats_data)

                        await channel.send(
                            f"**Weekly Report. Summoners analyzed: {summoners_names_formatted}** {formatted_stats_output}"
                        )
                    else:
                        await channel.send(
                            f"**Error fetching weekly report. Make sure you have added summoners to your server with !add_summoner 'Name #Tag'**"
                        )
                else:
                    print("Channel not found.")
            else:
                print(f"Guild with id {guild_id} does not have a main channel set.")


# Sets the text channel where automatic messages will be sent, such as weekly reports
@bot.command(
    name="set_main_channel",
    help="Sets the text channel where automatic messages will be sent",
)
async def set_main_channel(ctx):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    main_channel_changed = await mongo_db.set_main_channel(guild_id, channel_id)

    if main_channel_changed:
        await ctx.send("\nMain channel set.")
    else:
        await ctx.send(
            "\nFailed to set main channel. Make sure this is not already the main channel."
        )


# Periodically retrieves the match data for all summoners on all servers and stores it in database
@tasks.loop(hours=4)
async def fetch_all_summoner_match_data():
    all_guilds = bot.guilds
    print(f"\nFetching all summoner match data.")

    # iterate through every registered guild
    for guild in all_guilds:
        print(f"\nFetching all summoner match data for guild {guild.name}")

        summoners = await mongo_db.get_summoners(guild.id)
        if summoners:
            # iterate through all summoners within guild
            for summoner in summoners:
                print(f"\nFetching summoner match data for summoner {summoner["name"]}")  
                puuid = summoner["puuid"]
                name = summoner["name"]

                await mongo_db.handle_summoner_in_match_data_collection(summoner_puuid=puuid, summoner_name=name)
                todays_match_data = await lol_api.fetch_matches_data_by_day_range(summoner_puuid=puuid, range=7)

                if todays_match_data:
                    for match in todays_match_data:
                        await mongo_db.add_match_data(summoner_puuid=puuid, match_data=match)
        else:
            print(f"No summoners in guild {guild.name} to fetch data for")

        print(f"\nDone fetching all summoner match data for guild {guild.name}")
    
    print(f"\nDone fetching all summoner match data.")
    


bot.run(os.getenv("DISCORD_TOKEN"))
