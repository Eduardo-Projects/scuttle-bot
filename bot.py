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


# Event that runs only when bot first starts up
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

    report_automatic.start()
    print("Started automatic report job.")

# Runs when bot is added to new discord server
# Adds discord server data to database
@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name} with Guild ID: {guild.id} ")
    await mongo_db.add_guild(guild.name, guild.id)


# Sets the text channel where automatic messages will be sent, such as weekly reports
@bot.command(name="enable")
async def enable(ctx):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    main_channel_changed = await mongo_db.set_main_channel(guild_id, channel_id)

    if main_channel_changed:
        embed = discord.Embed(
            title=f"✅ Enable Command",
            description=f"Scuttle enabled on this channel",
            color=discord.Color.green(),
        )

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Enable Command",
            description=f"Scuttle is already enabled on this channel.",
            color=discord.Color.green(),
        )

        await ctx.send(embed=embed)


# Displays a list of all summoners for given discord server
@bot.group(invoke_without_command=True)
async def summoners(ctx):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_name = ctx.guild.name
    guild_id = ctx.guild.id
    summoners = await mongo_db.get_summoners(guild_id)

    if summoners:
        embed = discord.Embed(
            title=f"🎮 {guild_name}'s Summoners",
            description=f"This is a list of all the summoners added to this guild.",
            color=discord.Color.green(),
        )
        for summoner in summoners:
            embed.add_field(name="", value=f"🟢 {summoner["name"]}")

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoners",
            description=f"{guild_name} does not have any summoners. Add summoners by typing !add_summoner 'RiotName #Tag'",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


# Adds riot id and puuid to summoners list of the corresponding discord server in database
@summoners.command(name="add")
async def summoners_add(ctx, *, summoner_riot_id: str):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    guild_name = ctx.guild.name
    summoner_added = await mongo_db.add_summoner(summoner_riot_id, guild_id)

    if summoner_added:
        await ctx.send(f"Summoner {summoner_riot_id} added.")
        embed = discord.Embed(
            title=f"✅ Summoner Add Command",
            description=f"{summoner_riot_id} was successfully added to {guild_name}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoner Add Command",
            description=f"Failed to add {summoner_riot_id} to {guild_name}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


# Displays a summoner's formatted daily stats
@bot.group(invoke_without_command=True)
async def stats(ctx, *, summoner_riot_id: str):
    await process_stats_by_day_range(ctx, summoner_riot_id, range=1)

# Displays a summoner's formatted weekly stats
@stats.command(name="weekly")
async def stats_weekly(ctx, *, summoner_riot_id: str):
    await process_stats_by_day_range(ctx, summoner_riot_id, range=7)


# Displays a summoner's formatted monthly stats
@stats.command(name="monthly")
async def stats_monthly(ctx, *, summoner_riot_id: str):
    await process_stats_by_day_range(ctx, summoner_riot_id, range=30)


# Displays discord server's formatted overall stats for all summoners for the past week
@bot.group(invoke_without_command=True)
async def report(ctx):
    await process_report_by_day_range(ctx=ctx, range=7)


# Displays discord server's formatted overall stats for all summoners for the past month
@report.command(name="monthly")
async def report_monthly(ctx):
    await process_report_by_day_range(ctx=ctx, range=30)


# Automatic task that fetches and displays a weekly report every Sunday at 8:00 pm
@tasks.loop(minutes=1)
async def report_automatic():
    now = datetime.now()

    # check if it is 8:00 pm on a Sunday
    if now.weekday() == 6 and now.hour == 20 and now.minute == 00:
        all_guilds = bot.guilds
        for guild in all_guilds:
            guild_id = guild.id
            channel_id = await mongo_db.get_main_channel(guild_id)

            print(f"\nGetting automatic report for Guild with ID: {guild_id}")

            if channel_id:
                channel = bot.get_channel(channel_id)

                if channel:
                    await channel.send(
                        f"*Loading automatic report, this may take a few minutes ...*"
                    )

                    stats = await mongo_db.fetch_report_by_day_range(guild_id, range=7)

                    if stats:
                        summoners = await mongo_db.get_summoners(guild_id)
                        summoners_names = [summoner["name"] for summoner in summoners]
                        embed = discord.Embed(
                            title=f"📈 Server {guild.name}'s stats for the past 7 days.",
                            description=f"This is a general overview showing which summoner had the highest value for each stat in the past 7 days for Ranked Solo Queue.",
                            color=discord.Color.green(),
                        )
                        for stat in stats:
                            embed.add_field(name=f"✅ {stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)
                            
                        embed.add_field(name="🏆 Summoners Compared:", value="", inline=False) 
                        for name in summoners_names:
                            embed.add_field(name="", value=name, inline=True)

                        await channel.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title=f"❌ Automatic Weekly Report",
                            description=f"Error fetching automatic weekly report.",
                            color=discord.Color.green(),
                        )

                        await channel.send(embed=embed)
                else:
                    print("Channel not found.")
            else:
                print(f"Guild with id {guild_id} does not have a main channel set.")


# Reusable function for getting stats data based on day range
async def process_stats_by_day_range(ctx, summoner_riot_id, range):
    await ctx.send(f"*Loading ranked solo queue stats for **{summoner_riot_id}** ...*")

    # Make sure riot id exists
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        stats = await mongo_db.fetch_summoner_stats_by_day_range(puuid, range=range)
        embed = discord.Embed(
            title=f"📈 Summoner {summoner_riot_id}'s stats for the past {range} day(s).",
            description=f"This is a general overview of the collected stats for {summoner_riot_id} 's Ranked Solo Queue matches over the past {range} day(s).",
            color=discord.Color.green(),
        )
        for key, value in stats.items():
            embed.add_field(name=f"✅ {key}", value=value)

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Stats Command",
            description=f"Error getting stats for summoner {summoner_riot_id}. Make sure this user exists.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


# Resuable function for getting report data based on day range
async def process_report_by_day_range(ctx, range):
    # Ensure the command is being called from a discord server
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_name = ctx.guild.name
    guild_id = ctx.guild.id

    await ctx.send(
        f"*Loading {range} day report for **{guild_name}**, this may take a few minutes ...*"
    )

    stats = await mongo_db.fetch_report_by_day_range(guild_id, range=range)

    if stats:
        summoners = await mongo_db.get_summoners(guild_id)
        summoners_names = [summoner["name"] for summoner in summoners]
        embed = discord.Embed(
            title=f"📈 Server {guild_name}'s stats for the past {range} days.",
            description=f"This is a general overview showing which summoner had the highest value for each stat in the past {range} days for Ranked Solo Queue.",
            color=discord.Color.green(),
        )
        for stat in stats:
            embed.add_field(name=f"✅ {stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)
            
        embed.add_field(name="🏆 Summoners Compared:", value="", inline=False) 
        for name in summoners_names:
            embed.add_field(name="", value=name, inline=True)

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Weekly Report Command",
            description=f"Error fetching weekly report. Make sure you have added summoners to your server with !summoner add Name #Tag",
            color=discord.Color.green(),
        )

        await ctx.send(embed=embed)


bot.run(os.getenv("DISCORD_TOKEN"))
