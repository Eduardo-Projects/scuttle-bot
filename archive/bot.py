import discord
from discord.ext import commands, tasks
import mongo_db
import lol_api
import topgg_api
import logger
import os
from dotenv import load_dotenv
from datetime import datetime
from discord.ext.commands import AutoShardedBot
from discord import app_commands
import functools
import traceback

# Load environment variables from .env file
load_dotenv()

# Define intents
intents = discord.Intents.none()
intents.messages = True
intents.guilds = True

bot = commands.AutoShardedBot(command_prefix="/", intents=intents)
owner_id = os.getenv("OWNER_DISCORD_ID")
owner_id = int(owner_id)

environment = os.getenv("ENVIRONMENT")

# Function Wrapper


def command_error_handler(func):
    @functools.wraps(func)
    async def wrapper(interaction: discord.Interaction, *args, **kwargs):
        try:
            await logger.command(bot, interaction)
            return await func(interaction, *args, **kwargs)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(bot, interaction, stack_trace, e)
    return wrapper


# EVENTS


@bot.event
async def on_ready():
    print("\n")

    print(f"{bot.user.name} has connected to Discord!")

    report_automatic.start()
    print("Started automatic report job.")

    broadcast_donation_automatic.start()
    print("Started automatic donation broadcast job.")

    num_guilds = len(bot.guilds)
    print(f"Connected to {num_guilds} Guilds.")

    if environment == "prod":
        await mongo_db.update_guild_count(num_guilds)
        await topgg_api.update_stats(bot)

    print("\n")

    # guilds=bot.guilds
    # await mongo_db.update_summoner_region_all(guilds)

    # test_guild = discord.Object(id=1223525030093127741)
    # await bot.tree.sync(guild=test_guild)
    await bot.tree.sync()


@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name} with Guild ID: {guild.id} ")
    await mongo_db.add_guild(guild.name, guild.id)
    await mongo_db.update_guild_count(len(bot.guilds))

    # send message to support server
    await logger.guild_join_channel(bot, guild)


@bot.event
async def on_guild_remove(guild):
    print(f"Left guild: {guild.name} with Guild ID: {guild.id} ")

    # send message to support server
    await logger.guild_leave_channel(bot, guild)


# Event listener for interactions
@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.application_command:
        print(f"\n[{interaction.guild}]  [{interaction.user}]  [/{interaction.command.qualified_name}]")
        command_name = interaction.command.qualified_name.replace(" ", "_")
        await mongo_db.update_command_analytics(command=command_name)


# BASIC COMMANDS


bot.remove_command('help')
@bot.tree.command(name="help",description="Shows list of commands.")
@command_error_handler
async def help(interaction:discord.Interaction):
    embed = discord.Embed(title="🪴 Scuttle is brought to you by Eduardo Alba", description="I am a bot that provides quick and detailed **League of Legends** statistics.", color=discord.Color.green())
    commands = {
        '✅ /enable': 'Sets the main channel to where the bot will send automated messages',
        '📈 /stats daily {RIOT ID}': "Displays daily stats for Riot ID specified\nExample: `/stats Username NA1`",
        '📈 /stats weekly {RIOT ID}': "Displays weekly stats for Riot ID specified\nExample: `/stats weekly Username NA1`",
        '📈 /stats monthly {RIOT ID}': "Displays monthly stats for Riot ID specified\nExample: `/stats monthly Username NA1`",
        '💼 /reports weekly': "Displays weekly stat comparison for all summoners in your Guild",
        '💼 /reports monthly': "Displays monthly stat comparison for all summoners in your Guild",
        '🎮 /summoners list': "Displays all summoners in your Guild",
        '🎮 /summoners add {RIOT ID}': "Adds a summoner to your Guild\nExample: `/summoners add Username NA1`",
        '🎮 /summoners remove {RIOT ID}': "Removes a summoner from your Guild\nExample: `/summoners remove Username NA1`"
    }

    for command, description in commands.items():
        embed.add_field(name=command, value=description, inline=False)

    embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="enable", description="Sets the text channel where automatic messages will be sent, such as reports.")
@command_error_handler
async def enable(interaction: discord.Interaction):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    main_channel_changed = await mongo_db.set_main_channel(guild_id, channel_id)

    if main_channel_changed:
        embed = discord.Embed(
            title=f"✅ Enable Command",
            description=f"Scuttle enabled on this channel",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Enable Command",
            description=f"Scuttle is already enabled on this channel.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)


# SUMMONERS COMMANDS


summoners_group = app_commands.Group(name="summoners", description="Commands related to summoners")


@summoners_group.command(name="list", description="Displays a list of all summoners in your Guild.")
@command_error_handler
async def summoners(interaction: discord.Interaction):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    guild_name = interaction.guild
    guild_id = interaction.guild_id
    summoners = await mongo_db.get_summoners(guild_id)

    if summoners:
        print(f"Summoners in {guild_name}: {[summoner["name"] for summoner in summoners]}")
        embed = discord.Embed(
            title=f"🎮 {guild_name}'s Summoners",
            description=f"This is a list of all the summoners added to this guild.",
            color=discord.Color.green(),
        )

        formatted_summoners = []
        for summoner in summoners:
            formatted_summoners.append(f"🟢 {summoner["name"]}")
        embed.add_field(name="", value='\n'.join(formatted_summoners), inline=False)
        
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoners",
            description=f"{guild_name} does not have any summoners. Add summoners by typing /add_summoner RiotName Tag",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)


@summoners_group.command(name="add", description="Adds a summoner to your Guild.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
@command_error_handler
async def summoners_add(interaction: discord.Interaction, summoner_name: str, tag: str):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    guild_id = interaction.guild_id
    guild_name = interaction.guild
    summoner_riot_id = f"{summoner_name} #{tag}"
    summoner_added = await mongo_db.add_summoner(summoner_riot_id, guild_id)

    if summoner_added:
        embed = discord.Embed(
            title=f"✅ Summoner Add Command",
            description=f"{summoner_riot_id} was successfully added to {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoner Add Command",
            description=f"Failed to add {summoner_riot_id} to {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)


@summoners_group.command(name="remove", description="Removes a summoner from your Guild.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
@command_error_handler
async def summoners_remove(interaction: discord.Interaction, summoner_name: str, tag: str):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return
    
    await interaction.response.defer()

    guild_id = interaction.guild_id
    guild_name = interaction.guild
    summoner_riot_id = f"{summoner_name} #{tag}"
    summoner_removed = await mongo_db.remove_summoner(summoner_riot_id, guild_id)

    if summoner_removed:
        embed = discord.Embed(
            title=f"✅ Summoner Remove Command",
            description=f"{summoner_riot_id} was successfully removed from {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Summoner Remove Command",
            description=f"Failed to remove {summoner_riot_id} from {guild_name}",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)


bot.tree.add_command(summoners_group)

# STATS COMMANDS


stats_group = app_commands.Group(name="stats", description="Commands related to stats")
bot.tree.add_command(stats_group)


@stats_group.command(name="daily", description="Displays a summoner's collective stats for games played in the last 24 hours.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
@command_error_handler
async def stats(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} #{tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=1)


@stats_group.command(name="weekly", description="Displays a summoner's collective stats for games played in the last 7 Days.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
@command_error_handler
async def stats_weekly(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} #{tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=7)


@stats_group.command(name="monthly", description="Displays a summoner's collective stats for games played in the last 30 Days.")
@app_commands.describe(
    summoner_name="The name of the summoner",
    tag="Riot Tag"
)
@command_error_handler
async def stats_monthly(interaction: discord.Interaction, summoner_name: str, tag:str):
    summoner_riot_id = f"{summoner_name} #{tag}"
    await process_stats_by_day_range(interaction, summoner_riot_id, range=30)


# REPORT COMMANDS


reports_group = app_commands.Group(name="reports", description="Commands related to reports")
bot.tree.add_command(reports_group)


@reports_group.command(name="weekly", description="Display a weekly report comparing the stats of all summoners in your Guild.")
@command_error_handler
async def report(interaction: discord.Interaction):
    await process_report_by_day_range(interaction, range=7)


@reports_group.command(name="monthly", description="Display a monthly report comparing the stats of all summoners in your Guild.")
@command_error_handler
async def report(interaction: discord.Interaction):
    await process_report_by_day_range(interaction, range=30)

@reports_group.command(name="admin", description="This command is only for the bot admin.")
@app_commands.describe(
    guild_id="The id of the guild.",
)
@command_error_handler
async def report(interaction: discord.Interaction, guild_id: str):
    guild_id = int(guild_id)
    await process_report_by_day_range_admin(interaction, guild_id, range=30)


@tasks.loop(minutes=1)
async def report_automatic():
    now = datetime.now()

    # check if it is 4:00 pm EST on a Sunday
    if now.weekday() == 6 and now.hour == 20 and now.minute == 00:
        for guild in bot.guilds:
            channel_id = await mongo_db.get_main_channel(guild.id)

            print(f"\n[{guild.name}]  [Automated Report]  [Weekly]")

            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(f"*Loading automated weekly report...*")
                        stats = await mongo_db.fetch_report_by_day_range(guild.id, range=7)
                        if stats:
                            summoners_not_cached = []
                            summoners = await mongo_db.get_summoners(guild.id)
                            
                            if summoners is not None:
                                for summoner in summoners:
                                    is_cached = await mongo_db.is_summoner_cached(puuid=summoner["puuid"])
                                    if not is_cached:
                                        summoners_not_cached.append(summoner["name"])

                                summoners_names = [summoner["name"] for summoner in summoners]
                                embed = discord.Embed(
                                    title=f"📈 Server {guild.name}'s stats for the past 7 days.",
                                    description=f"This is a general overview showing which summoner had the highest value for each stat in the past 7 days for Ranked Solo Queue.",
                                    color=discord.Color.green(),
                                )
                                for stat in stats:
                                    embed.add_field(name=f"{stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)

                                # Summoners
                                summoners_embed = discord.Embed(
                                    title=f"🏆 Summoners Compared:",
                                    description=f"This is a list of all the summoners in your Guild whose stats have been compared.",
                                    color=discord.Color.green(),
                                )
                                for name in summoners_names:
                                    if name not in summoners_not_cached:
                                        summoners_embed.add_field(name="", value=name, inline=True)

                                embeds_arr=[embed, summoners_embed]

                                await channel.send(embeds=embeds_arr)
                        else:
                            embed = discord.Embed(
                                title=f"❌ Automatic Weekly Report",
                                description=f"Error fetching automatic weekly report.",
                                color=discord.Color.green(),
                            )

                            await channel.send(embed=embed)
                    except:
                        print("Can't send message to this channel.")
                else:
                    print("Channel not found.")
            else:
                print(f"{guild.name} does not have a main channel set.")


# BROADCAST MESSAGES


@tasks.loop(minutes=1)
async def broadcast_donation_automatic():
    now = datetime.now()

    # broadcast donation message at 5:00 pm EST on the 28th of every month.
    if now.day == 28 and now.hour == 21 and now.minute == 00:
        for guild in bot.guilds:
            channel_id = await mongo_db.get_main_channel(guild.id)
            print(f"\n[{guild.name}]  [Automated Donation Broadcast]  [Monthly]")

            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(title="🌟 Support Scuttle 🌟", 
                                          description=f"I hope you're enjoying using Scuttle to enhance your League of Legends experience!\n\nRunning and maintaining this bot takes a lot of time and resources. If you like what we do and want to help us keep the bot running smoothly, consider making a small donation. Every little bit helps us continue to develop and improve this service for you!\n\n🪴 [**Support Us Here!**](https://buymeacoffee.com/eduardoalba) \n\nThank you for your support, and happy gaming! 🎮", color=discord.Color.green())
                    try:
                        await channel.send(embed=embed)
                    except:
                        print("Can't send message to this channel.")
                else:
                    print("Channel not found.")
            else:
                print(f"{guild.name} does not have a main channel set.")


@bot.tree.command(name="broadcast",description="This command is only for the bot admin.")
@command_error_handler
async def broadcast(interaction: discord.Interaction):
    # Ensure the command is being called from a discord server
    if interaction.guild is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    if interaction.user.id != owner_id:
        print(f"User {interaction.user} in guild {interaction.guild} tried to use Admin broadcast command.")
        error_embed = discord.Embed(
            title=f"❌ Broadcast Command",
            description=f"This command is only for the bot admin.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=error_embed)
    else:
        for guild in bot.guilds:
            channel_id = await mongo_db.get_main_channel(guild.id)
            print(f"\n[{guild.name}]  [Admin Broadcast]")

            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="🌟 Join Scuttle's Discord Server 🌟",
                        description=(
                            "If you're enjoying Scuttle and want to stay updated, get help, or connect with other users, join our Discord support server! It's the best place to get assistance, share feedback, and stay in the loop with all things Scuttle.\n\n"
                            "[**Join the Support Server Here!**](https://discord.gg/temu6Xt9Dv)\n\n"
                            "We look forward to seeing you there! 🚀✨"
                        ),
                        color=discord.Color.green()
                    )

                    try:
                        await channel.send(embed=embed)
                    except:
                        print("Can't send message to this channel.")
                else:
                    print("Channel not found.")
            else:
                print(f"{guild.name} does not have a main channel set.")
    
    await interaction.followup.send("Done sending donation broadcast.")


# HELPER FUNCTIONS


async def process_stats_by_day_range(interaction: discord.Interaction, summoner_riot_id, range):
    # Ensure the command is being called from a discord server
    if interaction.guild_id is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    guild_name = interaction.guild
    guild_id = interaction.guild_id

    # Make sure riot id exists
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    if puuid:
        summoners_in_guild = await mongo_db.get_summoners(guild_id)
        if summoners_in_guild is not None:
            is_summoner_in_guild = any(summoner['puuid'] == puuid for summoner in summoners_in_guild)

            if not is_summoner_in_guild:
                print(f"Summoner {summoner_riot_id} is not a part of {guild_name}")
                embed = discord.Embed(
                    title=f"❌ Summoner {summoner_riot_id} is not part of your guild.",
                    description=f"",
                    color=discord.Color.green(),
                )
                embed.add_field(name=f"📈 Viewing Stats", value=f"If you want to view stats for `{summoner_riot_id}`, please add them to your guild by typing `/summoners add {summoner_riot_id.replace("#", "")}`.", inline=True)
                embed.add_field(name=f"👁 View Summoners in Your Guild", value="To view which summoners are part of your guild, type `/summoners list`.", inline=True)
                embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")
                await interaction.followup.send(embed=embed)
            else:
                is_summoner_cached = await mongo_db.is_summoner_cached(puuid)

                if not is_summoner_cached:
                    embed = discord.Embed(
                        title=f"⏱️ Stats Command",
                        description=f"Summoner **{summoner_riot_id}** has been added recently and therefore does not have any match data yet. Please allow about 1 hour to be able to display your stats. After this, you wont have to wait again!",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=embed)
                    return

                stats = await mongo_db.fetch_summoner_stats_by_day_range(puuid, range=range)
                embed = discord.Embed(
                    title=f"📈 Summoner {summoner_riot_id}'s stats for the past {range} day(s).",
                    description=f"This is a general overview of the collected stats for {summoner_riot_id} 's Ranked Solo Queue matches over the past {range} day(s).",
                    color=discord.Color.green(),
                )
                for key, value in stats.items():
                    embed.add_field(name=f"{key}", value=value)

                embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")

                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"❌ Summoner {summoner_riot_id} is not part of your guild.",
                description=f"",
                color=discord.Color.green(),
            )
            embed.add_field(name=f"📈 Viewing Stats", value=f"If you want to view stats for `{summoner_riot_id}`, please add them to your guild by typing `/summoners add {summoner_riot_id}`.", inline=True)
            embed.add_field(name=f"👁 View Summoners in Your Guild", value="To view which summoners are part of your guild, type `/summoners list`.", inline=True)
            embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")
            await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f"❌ Stats Command",
            description=f"Error getting stats for summoner {summoner_riot_id}. Make sure this user exists.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)


async def process_report_by_day_range(interaction: discord.Interaction, range):
    # Ensure the command is being called from a discord server
    if interaction.guild is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    guild_name = interaction.guild
    guild_id = interaction.guild_id
    
    await interaction.response.defer()

    stats = await mongo_db.fetch_report_by_day_range(guild_id, range=range)

    if stats:
        summoners_not_cached = []
        summoners = await mongo_db.get_summoners(guild_id)
        summoners_names = [summoner["name"] for summoner in summoners]

        for summoner in summoners:
            is_cached = await mongo_db.is_summoner_cached(puuid=summoner["puuid"])
            if not is_cached:
                summoners_not_cached.append(summoner["name"])

        embed = discord.Embed(
            title=f"📈 Server {guild_name}'s report for the past {range} days.",
            description=f"This is a general overview showing which summoner had the highest value for each stat in the past {range} days for Ranked Solo Queue.",
            color=discord.Color.green(),
        )
        for stat in stats:
            embed.add_field(name=f"{stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)
        

        # Summoners
        summoners_embed = discord.Embed(
            title=f"🏆 Summoners Compared:",
            description=f"This is a list of all the summoners in your Guild whose stats have been compared.",
            color=discord.Color.green(),
        )

        formatted_summoners_names = []
        for name in summoners_names:
            if name not in summoners_not_cached:
                formatted_summoners_names.append(f"🟢 {name}")
        summoners_embed.add_field(name="Summoners", value='\n'.join(formatted_summoners_names), inline=False)

        embeds_arr=[embed, summoners_embed]

        # Summoners not Cached
        if len(summoners_not_cached) > 0:
            summoners_not_cached_embed = discord.Embed(
                title=f"⏱️ Summoners Not Compared:",
                description=f"This is a list of all the summoners in your Guild who have been added recently and are waiting for their data to update.",
                color=discord.Color.green(),
            )
            for name in summoners_not_cached:
                summoners_not_cached_embed.add_field(name="", value=name, inline=True)
            embeds_arr.append(summoners_not_cached_embed)

        embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")

        await interaction.followup.send(embeds=embeds_arr)
    else:
        embed = discord.Embed(
            title=f"❌ Reports Command",
            description=f"Error fetching report. Make sure you have added summoners to your server with /summoner add Name Tag",
            color=discord.Color.green(),
        )

        await interaction.followup.send(embed=embed)


async def process_report_by_day_range_admin(interaction: discord.Interaction, guild_id, range):
    # Ensure the command is being called from a discord server
    if interaction.guild is None:
        await interaction.response.send_message("This command must be used in a server.")
        return

    await interaction.response.defer()

    if interaction.user.id != owner_id:
        print(f"User {interaction.user} in guild {interaction.guild} tried to use Admin command.")
        error_embed = discord.Embed(
            title=f"❌ Reports Command",
            description=f"This command is only for the bot admin.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=error_embed)
    else:
        guild = await mongo_db.get_guild_by_id(guild_id)

        if not guild:
            print(f"Guild with id {guild_id} does not exist.")
            error_embed = discord.Embed(
                title=f"❌ Reports Command",
                description=f"This guild does not exist",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=error_embed)
        else:
            guild_name = guild["name"]
            stats = await mongo_db.fetch_report_by_day_range(guild_id, range=range)

            if stats:
                summoners_not_cached = []
                summoners = await mongo_db.get_summoners(guild_id)
                summoners_names = [summoner["name"] for summoner in summoners]

                for summoner in summoners:
                    is_cached = await mongo_db.is_summoner_cached(puuid=summoner["puuid"])
                    if not is_cached:
                        summoners_not_cached.append(summoner["name"])

                embed = discord.Embed(
                    title=f"📈 Server {guild_name}'s report for the past {range} days.",
                    description=f"This is a general overview showing which summoner had the highest value for each stat in the past {range} days for Ranked Solo Queue.",
                    color=discord.Color.green(),
                )
                for stat in stats:
                    embed.add_field(name=f"{stat["Key"]}", value=f"{stat["Max Value"]} - {stat["Name"]}", inline=True)
                

                # Summoners
                summoners_embed = discord.Embed(
                    title=f"🏆 Summoners Compared:",
                    description=f"This is a list of all the summoners in your Guild whose stats have been compared.",
                    color=discord.Color.green(),
                )

                formatted_summoners_names = []
                for name in summoners_names:
                    if name not in summoners_not_cached:
                        formatted_summoners_names.append(f"🟢 {name}")
                summoners_embed.add_field(name="Summoners", value='\n'.join(formatted_summoners_names), inline=False)

                embeds_arr=[embed, summoners_embed]

                # Summoners not Cached
                if len(summoners_not_cached) > 0:
                    summoners_not_cached_embed = discord.Embed(
                        title=f"⏱️ Summoners Not Compared:",
                        description=f"This is a list of all the summoners in your Guild who have been added recently and are waiting for their data to update.",
                        color=discord.Color.green(),
                    )
                    for name in summoners_not_cached:
                        summoners_not_cached_embed.add_field(name="", value=name, inline=True)
                    embeds_arr.append(summoners_not_cached_embed)

                embed.set_footer(text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour.")

                await interaction.followup.send(embeds=embeds_arr)
            else:
                embed = discord.Embed(
                    title=f"❌ Reports Command",
                    description=f"Error fetching report. Make sure you have added summoners to your server with /summoner add Name Tag",
                    color=discord.Color.green(),
                )

                await interaction.followup.send(embed=embed)


bot.run(os.getenv("DISCORD_TOKEN"))
