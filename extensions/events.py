# extensions/events.py
from config import ENVIRONMENT
import discord
from discord.ext import commands

from data.mongo import update_guild_count, add_guild, update_command_analytics
from data.topgg import update_stats
from utils.logger import guild_join, guild_leave

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")
        print(f"{self.bot.user.name} is connected to {len(self.bot.guilds)} guilds ")
        await self.bot.tree.sync()
        print("Bot tree commands synced.")
        if ENVIRONMENT == "prod":
            await update_guild_count(len(self.bot.guilds))
            await update_stats(self.bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined new guild: {guild.name} with Guild ID: {guild.id}")
        await add_guild(guild.name, guild.id)
        await update_guild_count(len(self.bot.guilds))
        await guild_join(self.bot, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"Left guild: {guild.name} with Guild ID: {guild.id}")
        await guild_leave(self.bot, guild)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            print(f"\n[{interaction.guild}]  [{interaction.user}]  [/{interaction.command.qualified_name}]")
            command_name = interaction.command.qualified_name.replace(" ", "_")
            await update_command_analytics(command=command_name)

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
