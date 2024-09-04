import discord
from discord.ext import commands
from discord import app_commands
import traceback

import utils.logger as logger
from data.mongo import get_summoners, add_summoner, remove_summoner

from config import GUILD_LOGS_CHANNEL_ID

class Summoners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Registering the command group directly
        self.summoners_group = app_commands.Group(name="summoners", description="Commands related to summoners")
        self.summoners_group.command(name="list", description="Displays a list of all summoners in your Guild.")(self.list)
        self.summoners_group.command(name="add", description="Adds a summoner to your Guild.")(self.add)
        self.summoners_group.command(name="remove", description="Removes a summoner from your Guild.")(self.remove)
        self.bot.tree.add_command(self.summoners_group)

    async def list(self, interaction: discord.Interaction):
        try:
            # Ensure the command is being called from a discord server
            if interaction.guild_id is None:
                await interaction.response.send_message("This command must be used in a server.")
                return

            await interaction.response.defer()

            guild_name = interaction.guild
            guild_id = interaction.guild_id


            summoners = await get_summoners(guild_id)

            if summoners:
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
                await logger.command(self.bot, interaction, output_embed=embed)
            else:
                embed = discord.Embed(
                    title=f"❌ Summoners",
                    description=f"{guild_name} does not have any summoners. Add summoners by typing /add_summoner RiotName Tag",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(self.bot, interaction, stack_trace, e)

    @app_commands.describe(
        summoner_name="The name of the summoner",
        tag="Riot Tag"
    )
    async def add(self, interaction: discord.Interaction, summoner_name: str, tag: str):
        try:
            # Ensure the command is being called from a discord server
            if interaction.guild_id is None:
                await interaction.response.send_message("This command must be used in a server.")
                return

            await interaction.response.defer()

            guild_id = interaction.guild_id
            guild_name = interaction.guild
            summoner_riot_id = f"{summoner_name} #{tag}"
            summoner_added = await add_summoner(summoner_riot_id, guild_id)

            if summoner_added:
                embed = discord.Embed(
                    title=f"✅ Summoner Add Command",
                    description=f"{summoner_riot_id} was successfully added to {guild_name}",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
            else:
                embed = discord.Embed(
                    title=f"❌ Summoner Add Command",
                    description=f"Failed to add {summoner_riot_id} to {guild_name}",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(self.bot, interaction, stack_trace, e)

    @app_commands.describe(
        summoner_name="The name of the summoner",
        tag="Riot Tag"
    )
    async def remove(self, interaction: discord.Interaction, summoner_name: str, tag: str):
        try:
            # Ensure the command is being called from a discord server
            if interaction.guild_id is None:
                await interaction.response.send_message("This command must be used in a server.")
                return
            
            await interaction.response.defer()

            guild_id = interaction.guild_id
            guild_name = interaction.guild
            summoner_riot_id = f"{summoner_name} #{tag}"
            summoner_removed = await remove_summoner(summoner_riot_id, guild_id)

            if summoner_removed:
                embed = discord.Embed(
                    title=f"✅ Summoner Remove Command",
                    description=f"{summoner_riot_id} was successfully removed from {guild_name}",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
                
            else:
                embed = discord.Embed(
                    title=f"❌ Summoner Remove Command",
                    description=f"Failed to remove {summoner_riot_id} from {guild_name}",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(self.bot, interaction, stack_trace, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Summoners(bot))
