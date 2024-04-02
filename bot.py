import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import os
from dotenv import load_dotenv
from datetime import datetime
from discord.ext.commands import AutoShardedBot
from discord import app_commands
from typing import Literal, Optional

# Load environment variables from .env file
load_dotenv()

# Define intents
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)


# EVENTS


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

    report_automatic.start()
    print("Started automatic report job.")

    await bot.tree.sync()

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name} with Guild ID: {guild.id} ")
    await mongo_db.add_guild(guild.name, guild.id)


# BASIC COMMANDS


bot.remove_command('help')
@bot.tree.command(name="help",description="Shows list of commands.")
async def help(interaction:discord.Interaction):
    embed = discord.Embed(title="🪴 Scuttle is brought to you by Eduardo Alba", description="I am a bot that provides quick and detailed **League of Legends** statistics.", color=discord.Color.green())

    commands = {
        '✅ /enable': 'Sets the main channel to where the bot will send automated messages',
        '📈 /stats daily {RIOT ID}': "Displays daily stats for Riot ID specified\nExample: `/stats Username #NA1`",
        '📈 /stats weekly {RIOT ID}': "Displays weekly stats for Riot ID specified\nExample: `/stats weekly Username #NA1`",
        '📈 /stats monthly {RIOT ID}}': "Displays monthly stats for Riot ID specified\nExample: `/stats monthly Username #NA1`",
        '💼 /report weekly': "Displays weekly stat comparison for all summoners in your Guild",
        '💼 /report monthly': "Displays monthly stat comparison for all summoners in your Guild",
        '🎮 /summoners list': "Displays all summoners in your Guild",
        '🎮 /summoners add {RIOT ID}': "Adds a summoner to your Guild\nExample: `/summoners add Username #NA1`"
    }

    for command, description in commands.items():
        embed.add_field(name=command, value=description, inline=False)

    embed.set_footer(text="📝 Note: match data is updated hourly. If you add a new summoner to your Guild, expect to see stats within 1-2 hours.")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="enable", description="Sets the text channel where automatic messages will be sent, such as reports.")
async def enable(interaction: discord.Interaction):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    main_channel_changed = await mongo_db.set_main_channel(guild_id, channel_id)

    if main_channel_changed:
        embed = discord.Embed(
            title=f"✅ Enable Command",
            description=f"Scuttle enabled on this channel",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Enable Command",
            description=f"Scuttle is already enabled on this channel.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


# SUMMONERS COMMANDS


summoners_group = app_commands.Group(name="summoners", description="Commands related to summoners")
bot.tree.add_command(summoners_group)


@summoners_group.command(name="list", description="Displays a list of all summoners in your Guild.")
async def summoners(interaction: discord.Interaction):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_name = interaction.guild
    guild_id = interaction.guild_id
    summoners = await mongo_db.get_summoners(guild_id)

    if summoners:
        embed = discord.Embed(
            title=f"🎮 {guild_name}'s Summoners",
            description=f"This is a list of all the summoners added to this guild.",
            color=discord.Color.green(),
        )
        for summoner in summoners:
            embed.add_field(name="", value=f"🟢 {summoner["name"]}", inline=False)

        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoners",
            description=f"{guild_name} does not have any summoners. Add summoners by typing /add_summoner RiotName #Tag",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


@summoners_group.command(name="add", description="Adds a summoner to your Guild.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
async def summoners_add(interaction: discord.Interaction, summoner_name: str, tag: str):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_id = interaction.guild_id
    guild_name = interaction.guild
    summoner_riot_id = f"{summoner_name} {tag}"
    summoner_added = await mongo_db.add_summoner(summoner_riot_id, guild_id)

    if summoner_added:
        embed = discord.Embed(
            title=f"✅ Summoner Add Command",
            description=f"{summoner_riot_id} was successfully added to {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoner Add Command",
            description=f"Failed to add {summoner_riot_id} to {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


# STATS COMMANDS


stats_group = app_commands.Group(name="stats", description="Commands related to stats")
bot.tree.add_command(stats_group)


@stats_group.command(name="daily", description="Displays a summoner's collective stats for games played in the last 24 hours.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
async def stats(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} {tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=1)


@stats_group.command(name="weekly", description="Displays a summoner's collective stats for games played in the last 7 Days.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
async def stats_weekly(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} {tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=7)


@stats_group.command(name="monthly", description="Displays a summoner's collective stats for games played in the last 30 Days.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
async def stats_monthly(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} {tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=30)


# REPORT COMMANDS


reports_group = app_commands.Group(name="reports", description="Commands related to reports")
bot.tree.add_command(reports_group)


@reports_group.command(name="weekly", description="Display a weekly report comparing the stats of all summoners in your Guild.")
async def report(interaction: discord.Interaction):
    await process_report_by_day_range(interaction, range=7)


@reports_group.command(name="monthly", description="Display a monthly report comparing the stats of all summoners in your Guild.")
async def report(interaction: discord.Interaction):
    await process_report_by_day_range(interaction, range=30)


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


# HELPER FUNCTIONS


async def process_stats_by_day_range(interaction: discord.Interaction, summoner_riot_id, range):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_name = interaction.guild
    guild_id = interaction.guild_id

    # Make sure riot id exists
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        summoners_in_guild = await mongo_db.get_summoners(guild_id)
        is_summoner_in_guild = any(summoner['puuid'] == puuid for summoner in summoners_in_guild)

        if not is_summoner_in_guild:
            embed = discord.Embed(
                title=f"❌ Summoner {summoner_riot_id} is not part of your guild.",
                description=f"",
                color=discord.Color.green(),
            )
            embed.add_field(name=f"📈 Viewing Stats", value=f"If you want to view stats for `{summoner_riot_id}`, please add them to your guild by typing `/summoners add {summoner_riot_id}`.", inline=True)
            embed.add_field(name=f"👁 View Summoners in Your Guild", value="To view which summoners are part of your guild, type `/summoners`.", inline=True)
            embed.set_footer(text="📝 Note: match data is updated hourly. If you are adding a new summoner, expect to see stats within 1-2 hours.")
            await interaction.response.send_message(embed=embed)
        else:
            stats = await mongo_db.fetch_summoner_stats_by_day_range(puuid, range=range)
            embed = discord.Embed(
                title=f"📈 Summoner {summoner_riot_id}'s stats for the past {range} day(s).",
                description=f"This is a general overview of the collected stats for {summoner_riot_id} 's Ranked Solo Queue matches over the past {range} day(s).",
                color=discord.Color.green(),
            )
            for key, value in stats.items():
                embed.add_field(name=f"✅ {key}", value=value)

            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Stats Command",
            description=f"Error getting stats for summoner {summoner_riot_id}. Make sure this user exists.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


async def process_report_by_day_range(interaction: discord.Interaction, range):
    # Ensure the command is being called from a discord server
    if interaction.guild is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_name = interaction.guild
    guild_id = interaction.guild_id

    stats = await mongo_db.fetch_report_by_day_range(guild_id, range=range)

    if stats:
        summoners = await mongo_db.get_summoners(guild_id)
        summoners_names = [summoner["name"] for summoner in summoners]
        embed = discord.Embed(
            title=f"📈 Server {guild_name}'s report for the past {range} days.",
            description=f"This is a general overview showing which summoner had the highest value for each stat in the past {range} days for Ranked Solo Queue.",
            color=discord.Color.green(),
        )
        for stat in stats:
            embed.add_field(name=f"✅ {stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)
        

        # Summoners
        summoners_embed = discord.Embed(
            title=f"🏆 Summoners Compared:",
            description=f"This is a list of all the summoners in your Guild. Each of their stats have been compared.",
            color=discord.Color.green(),
        )
        for name in summoners_names:
            summoners_embed.add_field(name="", value=name, inline=True)


        await interaction.response.send_message(embeds=[embed, summoners_embed])
    else:
        embed = discord.Embed(
            title=f"❌ Reports Command",
            description=f"Error fetching report. Make sure you have added summoners to your server with /summoner add Name #Tag",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)



bot.run(os.getenv("DISCORD_TOKEN"))
