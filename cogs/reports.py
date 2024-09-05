from config import OWNER_ID

import discord
from discord.ext import commands
from discord import app_commands
import traceback

import utils.logger as logger
from data.mongo import get_summoners, fetch_report_by_day_range,is_summoner_cached, get_guild_by_id

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Registering the command group directly
        self.reports_group = app_commands.Group(name="reports", description="Commands related to reports")
        self.reports_group.command(name="weekly", description="Displays a weekly report comparing the stats of all summoners in your Guild.")(self.weekly)
        self.reports_group.command(name="monthly", description="Displays a monthly report comparing the stats of all summoners in your Guild.")(self.monthly)
        self.reports_group.command(name="admin", description="This command is only for the bot admin.")(self.admin)
        self.bot.tree.add_command(self.reports_group)

    async def weekly(self, interaction: discord.Interaction):
        await self._generate_and_send_report(interaction, day_range=7)

    async def monthly(self, interaction: discord.Interaction):
        await self._generate_and_send_report(interaction, day_range=30)

    @app_commands.describe(
        guild_id="The ID of the guild."
    )
    async def admin(self, interaction: discord.Interaction, guild_id: str):
        # Admin commands should use a specific guild ID and require admin permissions
        await self._generate_and_send_report(interaction, day_range=30, guild_id=int(guild_id), is_admin=True)

    async def _generate_and_send_report(self, interaction: discord.Interaction, day_range: int, guild_id: int = None, is_admin: bool = False):
        try:
            # Ensure the command is being called from a discord server
            if interaction.guild_id is None:
                await interaction.response.send_message("This command must be used in a server.")
                return

            await interaction.response.defer()

            # Determine the guild for the report
            if is_admin:
                # Check if the user is the bot admin
                if interaction.user.id != OWNER_ID:
                    error_embed = discord.Embed(
                        title=f"❌ Reports Command",
                        description="This command is only for the bot admin.",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=error_embed)
                    await logger.command(self.bot, interaction, output_embed=error_embed)
                    return

                # Fetch the guild by ID provided in the admin command
                guild = await get_guild_by_id(guild_id)
                if not guild:
                    error_embed = discord.Embed(
                        title=f"❌ Reports Command",
                        description="The specified guild does not exist.",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=error_embed)
                    await logger.command(self.bot, interaction, output_embed=error_embed)
                    return

                guild_name = guild.get("name", "None")
            else:
                # Use the guild of the interaction for non-admin commands
                guild_name = interaction.guild or "None"
                guild_id = interaction.guild_id

            # Fetch the report stats
            stats = await fetch_report_by_day_range(guild_id, range=day_range)

            if stats:
                summoners_not_cached = []
                summoners = await get_summoners(guild_id)
                summoners_names = [summoner["name"] for summoner in summoners]

                # Check for cached summoners
                for summoner in summoners:
                    is_cached = await is_summoner_cached(puuid=summoner["puuid"])
                    if not is_cached:
                        summoners_not_cached.append(summoner["name"])

                embed = discord.Embed(
                    title=f"📈 Server {guild_name}'s report for the past {day_range} days.",
                    description=f"This overview shows which summoner had the highest value for each stat in the past {day_range} days for Ranked Solo Queue.",
                    color=discord.Color.green(),
                )
                for stat in stats:
                    embed.add_field(name=stat["Key"], value=f"{stat['Max Value']} - {stat['Name']}", inline=True)

                # Summoners
                summoners_embed = discord.Embed(
                    title=f"🏆 Summoners Compared:",
                    description="A list of all the summoners in your Guild whose stats have been compared.",
                    color=discord.Color.green(),
                )

                formatted_summoners_names = [f"🟢 {name}" for name in summoners_names if name not in summoners_not_cached]
                summoners_embed.add_field(name="Summoners", value='\n'.join(formatted_summoners_names), inline=False)

                embeds_arr = [embed, summoners_embed]

                # Summoners not Cached
                if summoners_not_cached:
                    summoners_not_cached_embed = discord.Embed(
                        title=f"⏱️ Summoners Not Compared:",
                        description="These summoners have been added recently and are waiting for their data to update.",
                        color=discord.Color.green(),
                    )
                    for name in summoners_not_cached:
                        summoners_not_cached_embed.add_field(name="", value=name, inline=True)
                    embeds_arr.append(summoners_not_cached_embed)

                embed.set_footer(text="📝 Note: match data is updated hourly on the hour.")

                await interaction.followup.send(embeds=embeds_arr)
                await logger.command(self.bot, interaction, output_embeds=embeds_arr)
            else:
                embed = discord.Embed(
                    title=f"❌ Reports Command",
                    description="Error fetching report. Ensure summoners are added to your server with `/summoners add Name Tag`.",
                    color=discord.Color.green(),
                )

                await interaction.followup.send(embed=embed)
                await logger.command(self.bot, interaction, output_embed=embed)
        except Exception as e:
            stack_trace = traceback.format_exc()
            await logger.error(self.bot, interaction, stack_trace, e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reports(bot))
