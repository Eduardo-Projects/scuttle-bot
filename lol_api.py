import os
import aiohttp
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()

async def handle_api_call(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response.raise_for_status()  # Raise an exception for non-200 status codes
                data = await response.json()
                return data
            except aiohttp.ClientResponseError as e:
                print(f"Error in API call: {e.status}")
                return None

async def fetch_summoner_puuid_by_riot_id(summoner_riot_id):
    game_name, tag = summoner_riot_id.split(" #")
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}?api_key={os.getenv("RIOT_API_KEY")}"
    data = await handle_api_call(url)
    return data['puuid']

# retrive match data for summoner based on date range
async def fetch_matches_data(summoner_puuid, range=7, queue_id=420):
    today = datetime.datetime.today()
    start = today - datetime.timedelta(days=range)
    today_formatted = int(today.timestamp())
    start_formatted = int(start.timestamp())
    matches_data = []

    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?startTime={start_formatted}&endTime={today_formatted}&queue={queue_id}&start=0&count=100&api_key={os.getenv("RIOT_API_KEY")}"
    match_ids =  await handle_api_call(url)

    for id in match_ids:
        url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{id}?api_key={os.getenv("RIOT_API_KEY")}"
        matches_data.append(await handle_api_call(url))
    
    return matches_data

async def get_summoner_stats(summoner_puuid):
    matches_data = await fetch_matches_data(summoner_puuid)
    total_matches = len(matches_data)
    data_keys = ['Total Matches', 'Assists', 'Ability Uses', 'Average Damage Per Minute', 'Average Gold Per Minute',  
                 'Average KDA', 'Average Kill Participation', 'Skillshots Hit', 'Solo Kills',  
                 'Average Team Damage Percentage', 'Average Damage To Champions',  'Enemy Missing Pings']
    
    # Initialize the dictionary with keys set to 0
    data = {key: 0 for key in data_keys}
    total_damage_per_minute=total_gold_per_minute=total_kda=total_kp=total_team_damage_percentage=total_damage_to_champions=0

    data["Total Matches"] = total_matches

    for match in matches_data:
        participants = match["info"]["participants"]
        stats = next((obj for obj in participants if obj.get('puuid') == summoner_puuid), None)
        
        data["Assists"] += stats["assists"]
        data["Ability Uses"] += stats["challenges"]["abilityUses"]
        data["Skillshots Hit"] += stats["challenges"]["skillshotsHit"]
        data["Solo Kills"] += stats["challenges"]["soloKills"]
        data["Enemy Missing Pings"] += stats["enemyMissingPings"]

        total_damage_per_minute += stats["challenges"]["damagePerMinute"]
        total_gold_per_minute += stats["challenges"]["goldPerMinute"]
        total_kda += stats["challenges"]["kda"]
        total_kp += stats["challenges"]["killParticipation"]
        total_team_damage_percentage += stats["challenges"]["teamDamagePercentage"]
        total_damage_to_champions += stats["totalDamageDealtToChampions"]

    data["Average Damage Per Minute"] = total_damage_per_minute/total_matches
    data["Average Gold Per Minute"] = total_gold_per_minute/total_matches
    data["Average KDA"] = total_kda/total_matches
    data["Average Kill Participation"] = total_kp/total_matches
    data["Average Team Damage Percentage"] = total_team_damage_percentage/total_matches
    data["Average Damage To Champions"] = total_damage_to_champions/total_matches

    # Round values to 2 decimal places
    rounded_data = {key: round(value, 2) for key, value in data.items()}

    return rounded_data
