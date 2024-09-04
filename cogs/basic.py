# cogs/basic.py

import discord
from discord import app_commands
from discord.ext import commands

import utils.logger as logger
from data.mongo import set_main_channel

class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows a list of commands.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🪴 Scuttle is brought to you by Eduardo Alba",
            description="I am a bot that provides quick and detailed **League of Legends** statistics.",
            color=discord.Color.green()
        )
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

        embed.set_footer(
            text="📝 Note: match data is updated hourly on the hour. If you add a new summoner to your Guild, expect to see stats at the next hour."
        )

        await interaction.response.send_message(embed=embed)
        await logger.command(self.bot, interaction, output_embed=embed)

    @app_commands.command(name="enable", description="Sets the text channel where automatic messages will be sent, such as reports.")
    async def enable(self, interaction: discord.Interaction):
        # Ensure the command is being called from a discord server
        if interaction.guild_id is None:
            await interaction.response.send_message("This command must be used in a server.")
            return

        await interaction.response.defer()

        guild_id = interaction.guild_id
        channel_id = interaction.channel_id
        main_channel_changed = await set_main_channel(guild_id, channel_id)

        if main_channel_changed:
            embed = discord.Embed(
                title=f"✅ Enable Command",
                description=f"Scuttle enabled on this channel",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed)
            await logger.command(self.bot, interaction, output_embed=embed)
        else:
            embed = discord.Embed(
                title=f"❌ Enable Command",
                description=f"Scuttle is already enabled on this channel.",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed)
            await logger.command(self.bot, interaction, output_embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Basic(bot))
