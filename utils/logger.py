import discord
from datetime import datetime
import pytz
from typing import List

from config import GUILD_ERROR_CHANNEL_ID, GUILD_JOIN_CHANNEL_ID, GUILD_LEAVE_CHANNEL_ID, GUILD_LOGS_CHANNEL_ID

async def guild_join(bot, guild):
    try:
        channel = bot.get_channel(int(GUILD_JOIN_CHANNEL_ID))
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


async def guild_leave(bot, guild):
    try:
        channel = bot.get_channel(int(GUILD_LEAVE_CHANNEL_ID))
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


async def error(bot, interaction: discord.Interaction, error_stack, error_message ):
    try:
        log_channel = bot.get_channel(int(GUILD_ERROR_CHANNEL_ID))
        if log_channel:
            embed = discord.Embed(
                title="⚠️Flagged Error!",
                description="An error has been flagged while using a slash command.",
                color=discord.Color.red(),
            )

            # Get the current time in UTC
            utc_now = datetime.now(pytz.utc)

            # Convert the UTC time to Eastern Time (EST/EDT)
            est = pytz.timezone('US/Eastern')
            est_now = utc_now.astimezone(est)
            formatted_date = est_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

            embed.add_field(name="Error Command", value=f"`{interaction.command.qualified_name}`", inline=False)
            embed.add_field(name="Error Stack", value=f"`{error_stack}`", inline=False)
            embed.add_field(name="Error Message", value=f"`{error_message}`", inline=False)
            embed.add_field(name="Error Timestamp", value=f"`{formatted_date}`", inline=False)
            embed.add_field(name="Error Guild", value=f"`{interaction.guild}` ({interaction.guild_id})", inline=False)
            embed.add_field(name="Error User", value=f"`{interaction.user}` ({interaction.user.id})", inline=False)
            embed.add_field(name="Error Command Channel", value=f"`{interaction.channel}` ({interaction.channel_id})", inline=False)


            await log_channel.send(embed=embed)
        else:
            print(f"Failed to get the error log channel.")
    except Exception as e:
        print(f"Failed to log error to Discord: {e}")


async def command(bot, interaction: discord.Interaction, output_embed: discord.Embed = None, output_embeds: List[discord.Embed] = None):
    try:
        log_channel = bot.get_channel(int(GUILD_LOGS_CHANNEL_ID))
        if log_channel:
            embed = discord.Embed(
                title="🍀Command Used",
                description="An interaction command has been used.",
                color=discord.Color.green(),
            )

            embed.add_field(name="Command", value=f"`{interaction.command.qualified_name}`", inline=False)
            embed.add_field(name="Guild of Use", value=f"`{interaction.guild}` ({interaction.guild_id})", inline=False)
            embed.add_field(name="Channel of Use", value=f"`{interaction.channel}` ({interaction.channel_id})", inline=False)
            embed.add_field(name="Command User", value=f"`{interaction.user}` ({interaction.user.id})", inline=False)

            await log_channel.send(embed=embed)

            if output_embed:
                await log_channel.send(embed=output_embed)

            if output_embeds:
                await log_channel.send(embeds=output_embeds)
        else:
            print(f"Failed to get the log channel.")
    except Exception as e:
        print(f"Failed to log command to Discord: {e}")