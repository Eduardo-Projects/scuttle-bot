import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def fetch_summoner_data(summoner_name):
    url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={os.getenv("RIOT_API_KEY")}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
