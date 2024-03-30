import os
import aiohttp
from dotenv import load_dotenv
import datetime
import re
import asyncio
import utils

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

# Fetches match data for all matches played in the last {range} days
# queue_id is set to 420 by default for ranked solo queue
async def fetch_matches_data_by_day_range(summoner_puuid, range=7, queue_id=420):
    today = datetime.datetime.today()
    start = today - datetime.timedelta(days=range)
    today_formatted = int(today.timestamp())
    start_formatted = int(start.timestamp())
    matches_data = []

    print(f"Fetching matches data for summoner with puuid {summoner_puuid} for the last {range} days")
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?startTime={start_formatted}&endTime={today_formatted}&queue={queue_id}&start=0&count=100&api_key={os.getenv("RIOT_API_KEY")}"
    match_ids =  await handle_api_call(url)

    if match_ids:
        for id in match_ids:
            url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{id}?api_key={os.getenv("RIOT_API_KEY")}"
            single_match_data = await handle_api_call(url)

            if single_match_data:
                matches_data.append(single_match_data)
    
    if matches_data == []:
        print(f"No matches were found for summoner with puuid {summoner_puuid} in the last {range} days.")
        return None
    else:
        print(f"{len(matches_data)} matches were found for summoner with puuid {summoner_puuid} in the last {range} days")
        return matches_data

# Fetches stats for all matches played in the last {range} days
async def fetch_summoner_stats_by_day_range(summoner_puuid, range=7):
    matches_data = await fetch_matches_data_by_day_range(summoner_puuid, range)
    stats = utils.calculate_stats(summoner_puuid, matches_data)
    return stats


# Checks to make sure provided riot id follows format: 'String1 #String2'
# Keep in mind there can be any number of strings before the #
def check_riot_id_format(riot_id):
    pattern = r'^[\w]+(?:\s[\w]+)*\s#[\w]+$'

    if re.match(pattern, riot_id):
        return True
    else:
        return False
