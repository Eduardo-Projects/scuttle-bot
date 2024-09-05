import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_DISCORD_ID"))
ENVIRONMENT = os.getenv("ENVIRONMENT")

GUILD_JOIN_CHANNEL_ID=os.getenv("GUILD_JOIN_CHANNEL_ID")
GUILD_LEAVE_CHANNEL_ID=os.getenv("GUILD_LEAVE_CHANNEL_ID")
GUILD_ERROR_CHANNEL_ID=os.getenv("GUILD_ERROR_CHANNEL_ID")
GUILD_LOGS_CHANNEL_ID=os.getenv("GUILD_LOGS_CHANNEL_ID")

SUPPORT_GUILD_LINK=os.getenv("SUPPORT_GUILD_LINK")

TOPGG_TOKEN=os.getenv("TOPGG_TOKEN")
TOPGG_ID=os.getenv("TOPGG_ID")

RIOT_API_KEY=os.getenv("RIOT_API_KEY")
MONGO_DB_URI=os.getenv("MONGO_DB_URI")