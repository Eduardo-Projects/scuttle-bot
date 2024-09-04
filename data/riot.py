
import os
import aiohttp
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import asyncio

# Load environment variables from .env file
load_dotenv()

regions = [
    "na1",
    "euw1",
    "eun1",
    "kr",
    "jp1",
    "br1",
    "la1",
    "la2",
    "oc1",
    "ph2",
    "ru",
    "sg2",
    "th2",
    "tr1",
    "tw2",
    "vn2"
]

# Handler function for all API calls made
# Contains error handling and backup rate limit handling
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
        


async def handle_api_call_no_exception(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get("Retry-After", 1))
                    print(f"Rate limit exceeded. Retrying in {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    return await handle_api_call_no_exception(url)  #
                else:
                    # Log or handle unsuccessful API call (e.g., response status not 200)
                    print(f"API call failed with status code: {response.status}")
                    return None
        except Exception as e:
            # Log or handle any exceptions raised during the API call
            print(f"An error occurred during API call to {url}: {str(e)}")
            return None


# Fetches a summoner's puuid from their riot id
# Checks if riot id is in proper format
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


# Returns the Region a Summoner is from
async def get_summoner_region(summoner_puuid):
    for region in regions:
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{summoner_puuid}?api_key={os.getenv("RIOT_API_KEY")}"
        data = await handle_api_call_no_exception(url)
        if data:
            return region
    
    return None

# Checks to make sure provided riot id follows format: 'String1 #String2'
# Keep in mind there can be any number of strings before the #
def check_riot_id_format(riot_id):
    pattern = r'^[\w]+(?:\s[\w]+)*\s#[\w]+(?:\s[\w]+)*$'

    if re.match(pattern, riot_id):
        return True
    else:
        print("Failed match.")
        return False
