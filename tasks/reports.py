# tasks/reports.py

import discord
from discord.ext import commands, tasks
from datetime import datetime

from data.mongo import get_main_channel, fetch_report_by_day_range, get_summoners, is_summoner_cached

class ReportTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.report_automatic.start()  # Start the task when the cog is loaded

    @tasks.loop(minutes=1)
    async def report_automatic(self):
        now = datetime.now()

        # Check if it is 4:00 pm EST on a Sunday
        if now.weekday() == 6 and now.hour == 20 and now.minute == 00:
            for guild in self.bot.guilds:
                channel_id = await get_main_channel(guild.id)

                print(f"\n[{guild.name}]  [Automated Report]  [Weekly]")

                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send("*Loading automated weekly report...*")
                            stats = await fetch_report_by_day_range(guild.id, range=7)
                            if stats:
                                summoners_not_cached = []
                                summoners = await get_summoners(guild.id)

                                if summoners:
                                    for summoner in summoners:
                                        is_cached = await is_summoner_cached(puuid=summoner["puuid"])
                                        if not is_cached:
                                            summoners_not_cached.append(summoner["name"])

                                    summoners_names = [summoner["name"] for summoner in summoners]
                                    embed = discord.Embed(
                                        title=f"📈 Server {guild.name}'s stats for the past 7 days.",
                                        description="This is a general overview showing which summoner had the highest value for each stat in the past 7 days for Ranked Solo Queue.",
                                        color=discord.Color.green(),
                                    )
                                    for stat in stats:
                                        embed.add_field(name=stat["Key"], value=f"{stat['Max Value']} - {stat['Name']}", inline=True)

                                    # Summoners
                                    summoners_embed = discord.Embed(
                                        title="🏆 Summoners Compared:",
                                        description="This is a list of all the summoners in your Guild whose stats have been compared.",
                                        color=discord.Color.green(),
                                    )
                                    for name in summoners_names:
                                        if name not in summoners_not_cached:
                                            summoners_embed.add_field(name="", value=name, inline=True)

                                    embeds_arr = [embed, summoners_embed]

                                    await channel.send(embeds=embeds_arr)
                            else:
                                embed = discord.Embed(
                                    title="❌ Automatic Weekly Report",
                                    description="Error fetching automatic weekly report.",
                                    color=discord.Color.green(),
                                )
                                await channel.send(embed=embed)
                        except Exception as e:
                            print(f"Error sending message to channel {channel.id}: {e}")
                    else:
                        print("Channel not found.")
                else:
                    print(f"{guild.name} does not have a main channel set.")

    @report_automatic.before_loop
    async def before_report_automatic(self):
        print("Waiting for bot to be ready...")
        await self.bot.wait_until_ready()  # Wait until the bot is ready before starting the loop

async def setup(bot: commands.Bot):
    await bot.add_cog(ReportTasks(bot))
