import discord
from discord.ext import commands
from config import DISCORD_TOKEN

# Define intents for your bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# Initialize the bot with command prefix and intents
bot = commands.AutoShardedBot(command_prefix="/", intents=intents)

# Function to load cogs
async def load_cogs():
    cogs = [
        'extensions.events',
        'cogs.summoners', 'cogs.basic', 'cogs.stats', 'cogs.reports',
        'tasks.reports'
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Successfully loaded {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

@bot.event
async def setup_hook():
    # Load all cogs asynchronously when the bot starts
    await load_cogs()

# Start the bot using bot.run(), which correctly manages event loop and cog loading
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
