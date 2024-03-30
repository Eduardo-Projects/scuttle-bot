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

# Fetches match data for all matches played in the last {range} days
# queue_id is set to 420 by default for ranked solo queue
async def fetch_matches_data_by_day_range(summoner_puuid, range=7, queue_id=420):
    today = datetime.today()
    start = today - timedelta(days=range)
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

# Fetches all match data for all summoners on all discord servers and stores in database
# Range is defaulted to one to search for the matches played in the past day
async def fetch_all_summoner_match_data(guilds, range=1):
    start_time = datetime.now()
    formatted_start_time = start_time.strftime("%m/%d/%y %H:%M:%S")

    print(f"\nFetching all summoner match data. Started at {formatted_start_time}")
    for guild in guilds:
        await fetch_all_summoner_match_data_by_guild(guild.id, range)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    total_seconds = int(elapsed_time.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    formatted_elapsed_time = f"{hours:02}:{minutes:02}:{seconds:02}"
    print(f"\nDone fetching all summoner match data. Took {formatted_elapsed_time}")

# Fetch all match data for all summoners on one discord server and store it in database
# Range is defaulted to 7 to search for the matches played in the last 7 days
async def fetch_all_summoner_match_data_by_guild(guild_id, range=7):
    print(f"\nFetching all summoner match data for guild {guild_id}.")

    summoners = await mongo_db.get_summoners(guild_id)
    if summoners:
        for summoner in summoners:
            print(f"\nFetching summoner match data for summoner {summoner["name"]}")  
            puuid = summoner["puuid"]
            name = summoner["name"]

            await mongo_db.handle_summoner_in_match_data_collection(summoner_puuid=puuid, summoner_name=name)
            todays_match_data = await fetch_matches_data_by_day_range(summoner_puuid=puuid, range=range)

            if todays_match_data:
                for match in todays_match_data:
                    await mongo_db.add_match_data(summoner_puuid=puuid, match_data=match)
    else:
        print(f"No summoners in guild {guild_id} to fetch data for")

    print(f"\nDone fetching all summoner match data for guild {guild_id}")


# Checks to make sure provided riot id follows format: 'String1 #String2'
# Keep in mind there can be any number of strings before the #
def check_riot_id_format(riot_id):
    pattern = r'^[\w]+(?:\s[\w]+)*\s#[\w]+$'

    if re.match(pattern, riot_id):
        return True
    else:
        return False
