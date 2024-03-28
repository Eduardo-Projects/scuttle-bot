import os
import aiohttp
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()

async def fetch_summoner_puuid_by_riot_id(summoner_riot_id):
    game_name, tag = summoner_riot_id.split(" #")
    
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}?api_key={os.getenv("RIOT_API_KEY")}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data['puuid']

async def fetch_summoner_match_history_this_week(summoner_riot_id):
    today = datetime.datetime.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    today_epoch = int(today.timestamp())
    seven_days_ago_epoch = int(seven_days_ago.timestamp())

    # Convert riot id to puuid
    summoner_puuid = await fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?startTime={seven_days_ago_epoch}&endTime={today_epoch}&start=0&count=100&api_key={os.getenv("RIOT_API_KEY")}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def fetch_match_info(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={os.getenv("RIOT_API_KEY")}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

def get_participant_info_by_match(match_info, summoner_riot_id):
    game_name, tag = summoner_riot_id.split(" #")

    # get data for participant
    for participant in match_info["info"]["participants"]:
        if participant["riotIdGameName"] == game_name and participant["riotIdTagline"] == tag:
            return participant
    
    return {}

async def get_death_count_by_summoner(summoner_riot_id):
    match_history = await fetch_summoner_match_history_this_week(summoner_riot_id)
    matches_info = []
    deaths = 0

    for match in match_history:
        match_info = await fetch_match_info(match)
        matches_info.append(match_info)
    
    for match in matches_info:
        participant_data = get_participant_info_by_match(match, summoner_riot_id)
        deaths += participant_data["deaths"]

    return deaths

