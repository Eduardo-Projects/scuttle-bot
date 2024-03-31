import os
import aiohttp
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import asyncio
import utils
import mongo_db

# Load environment variables from .env file
load_dotenv()

# Handler function for all calls made to riot api
async def handle_api_call(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get("Retry-After", 1))
                    print(f"Rate limit exceeded. Retrying in {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    return await handle_api_call(url)  # Retry the request
                response.raise_for_status()  # Raise an exception for non-200 status codes
                data = await response.json()
                return data
        except aiohttp.ClientResponseError as e:
            print(f"Error in API call: {e.status}, message='{e.message}'")
            return None


async def fetch_summoner_puuid_by_riot_id(summoner_riot_id):
    is_proper_format = check_riot_id_format(summoner_riot_id)

    if is_proper_format:
        game_name, tag = summoner_riot_id.split(" #")
        url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}?api_key={os.getenv("RIOT_API_KEY")}"
        data = await handle_api_call(url)
        return data["puuid"] if data is not None else None
    else:
        print(f"Failed to fetch summoner puuid. {summoner_riot_id} is not a valid Riot ID.")
        return None


# Checks to make sure provided riot id follows format: 'String1 #String2'
# Keep in mind there can be any number of strings before the #
def check_riot_id_format(riot_id):
    pattern = r'^[\w]+(?:\s[\w]+)*\s#[\w]+$'

    if re.match(pattern, riot_id):
        return True
    else:
        return False
