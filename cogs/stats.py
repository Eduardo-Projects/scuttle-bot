# cogs/stats.py

import discord
from discord.ext import commands
from discord import app_commands
import traceback

import utils.logger as logger
from data.mongo import get_summoners, is_summoner_cached, fetch_summoner_stats_by_day_range
from data.riot import fetch_summoner_puuid_by_riot_id

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Registering the command group directly
        self.stats_group = app_commands.Group(name="stats", description="Commands related to stats")
        self.stats_group.command(name="daily", description="Displays a summoner's stats for games played in the last 24 hours.")(self.daily)
        self.stats_group.command(name="weekly", description="Displays a summoner's stats for games played in the last 7 days.")(self.weekly)
        self.stats_group.command(name="monthly", description="Displays a summoner's stats for games played in the last 30 days.")(self.monthly)
        self.bot.tree.add_command(self.stats_group)

    @app_commands.describe(
        summoner_name="The name of the summoner",
        tag="Riot Tag"
    )
    async def daily(self, interaction: discord.Interaction, summoner_name: str, tag: str):
        await self._fetch_and_send_stats(interaction, summoner_name, tag, day_range=1)

    @app_commands.describe(
        summoner_name="The name of the summoner",
        tag="Riot Tag"
    )
    async def weekly(self, interaction: discord.Interaction, summoner_name: str, tag: str):
        await self._fetch_and_send_stats(interaction, summoner_name, tag, day_range=7)

    @app_commands.describe(
        summoner_name="The name of the summoner",
        tag="Riot Tag"
    )
    async def monthly(self, interaction: discord.Interaction, summoner_name: str, tag: str):
        await self._fetch_and_send_stats(interaction, summoner_name, tag, day_range=30)

    async def _fetch_and_send_stats(self, interaction: discord.Interaction, summoner_name: str, tag: str, day_range: int):
        try:
            # Ensure the command is being called from a discord server
            if interaction.guild_id is None:
                await interaction.response.send_message("This command must be used in a server.")
                return

            await interaction.response.defer()

            guild_id = interaction.guild_id
            summoner_riot_id = f"{summoner_name} #{tag}"

            # Make sure riot id exists
            puuid = await fetch_summoner_puuid_by_riot_id(summoner_riot_id)

            if puuid:
                summoners_in_guild = await get_summoners(guild_id)
                is_summoner_in_guild = any(summoner['puuid'] == puuid for summoner in summoners_in_guild)

                if not is_summoner_in_guild:
                    embed = discord.Embed(
                        title=f"❌ Summoner {summoner_riot_id} is not part of your guild.",
                        description="Add them with `/summoners add {RIOT ID}` to view their stats.",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=embed)
                    await logger.command(self.bot, interaction, output_embed=embed)
                    return

                summoner_cached = await is_summoner_cached(puuid)

                if not summoner_cached:
                    embed = discord.Embed(
                        title=f"⏱️ Stats Command",
                        description=f"Summoner **{summoner_riot_id}** has been added recently and does not have match data yet. Please allow about 1 hour.",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=embed)
                    await logger.command(self.bot, interaction, output_embed=embed)
                    return

                stats = await fetch_summoner_stats_by_day_range(puuid, range=day_range)
                embed = discord.Embed(
                    title=f"📈 Summoner {summoner_riot_id}'s stats for the past {day_range} day(s).",
                    description=f"Collected stats for {summoner_riot_id}'s Ranked Solo Queue matches over the past {day_range} day(s).",
                    color=discord.Color.green(),
                )
                for key, value in stats.items():
                    embed.add_field(name=key, value=value)

                embed.set_footer(text="📝 Note: match data is updated hourly on the hour.")

                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
            else:
                embed = discord.Embed(
                    title=f"❌ Stats Command",
                    description=f"Error getting stats for summoner {summoner_riot_id}. Make sure this user exists.",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(self.bot, interaction, stack_trace, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
