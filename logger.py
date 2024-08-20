import os
import discord
from datetime import datetime
import pytz

guild_join_channel_id=os.getenv("GUILD_JOIN_CHANNEL_ID")
guild_leave_channel_id=os.getenv("GUILD_LEAVE_CHANNEL_ID")
guild_error_channel_id=os.getenv("GUILD_ERROR_CHANNEL_ID")

async def guild_join_channel(bot, guild):
    try:
        channel = bot.get_channel(int(guild_join_channel_id))
        if channel:
            embed = discord.Embed(
            title=f"🟢 Scuttle has joined *'{guild.name}'*",
            color=discord.Color.green(),
            )

            # Get the current time in UTC
            utc_now = datetime.now(pytz.utc)

            # Convert the UTC time to Eastern Time (EST/EDT)
            est = pytz.timezone('US/Eastern')
            est_now = utc_now.astimezone(est)
            formatted_date = est_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

            embed.add_field(name="Date/Time", value=formatted_date, inline=False)
            await channel.send(embed=embed)
        else:
            print(f"Failed to get the guild-join channel.")
    except Exception as e:
        print(f"Failed to send guild join message to support server: {e}")


async def guild_leave_channel(bot, guild):
    try:
        channel = bot.get_channel(int(guild_leave_channel_id))
        if channel:
            embed = discord.Embed(
            title=f"🔴 Scuttle has Left *'{guild.name}'*",
            color=discord.Color.green(),
            )

            # Get the current time in UTC
            utc_now = datetime.now(pytz.utc)

            # Convert the UTC time to Eastern Time (EST/EDT)
            est = pytz.timezone('US/Eastern')
            est_now = utc_now.astimezone(est)
            formatted_date = est_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

            embed.add_field(name="Date/Time", value=formatted_date, inline=False)
            await channel.send(embed=embed)
        else:
            print(f"Failed to get the guild-leave channel.")
    except Exception as e:
        print(f"Failed to send guild join message to support server: {e}")


async def log_error(bot, error_message, additional_info=None):
    try:
        channel = bot.get_channel(int(guild_error_channel_id))
        if channel:
            embed = discord.Embed(
                title="⚠️ Error Logged",
                color=discord.Color.red(),
            )

            # Adding the error message
            embed.add_field(name="Error", value=error_message, inline=False)

            # Adding any additional information if provided
            if additional_info:
                embed.add_field(name="Additional Info", value=additional_info, inline=False)

            await channel.send(embed=embed)
        else:
            print(f"Failed to get the error log channel.")
    except Exception as e:
        print(f"Failed to log error to Discord: {e}")