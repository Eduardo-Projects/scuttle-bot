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

# retrive match data for summoner based on date range
async def fetch_match_data_by_range(day_range, summoner_riot_id):
    match_ids = []
    matches_data = []
    ranked_solo_queue_id = 420

    # format dates
    today = datetime.datetime.today()
    start = today - datetime.timedelta(days=day_range)

    today_formatted = int(today.timestamp())
    start_formatted = int(start.timestamp())

    # convert summoner riot id to puuid
    summoner_puuid = await fetch_summoner_puuid_by_riot_id(summoner_riot_id)

    # retrieve match id history
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?startTime={start_formatted}&endTime={today_formatted}&queue={ranked_solo_queue_id}&start=0&count=100&api_key={os.getenv("RIOT_API_KEY")}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            match_id_history_data = await response.json()
            match_ids = match_id_history_data
    
    # convert match ids into match data
    for match_id in match_ids:
        url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={os.getenv("RIOT_API_KEY")}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                 match_data = await response.json()
                 matches_data.append(match_data)
    
    return matches_data

def get_participant_info_by_match(match_info, summoner_riot_id):
    game_name, tag = summoner_riot_id.split(" #")

    # get data for participant
    for participant in match_info["info"]["participants"]:
        if participant["riotIdGameName"] == game_name and participant["riotIdTagline"] == tag:
            return participant
    
    return {}

async def get_stats_by_summoner(matches_data, summoner_riot_id):
    total_matches = len(matches_data)
    data_keys = ['Assists', 'Ability Uses', 'Average Damage Per Minute', 'Average Gold Per Minute',  
                 'Average KDA', 'Average Kill Participation', 'Skillshots Hit', 'Solo Kills',  
                 'Average Team Damage Percentage', 'Average Damage To Champions',  'Enemy Missing Pings']
    
    # Initialize the dictionary with keys set to 0
    data = {key: 0 for key in data_keys}

    # iterate over each match and analyze stats
    total_damage_per_minute = 0
    total_gold_per_minute = 0
    total_kda = 0
    total_kp = 0
    total_team_damage_percentage = 0
    total_damage_to_champions = 0

    for match in matches_data:
        participant_data = get_participant_info_by_match(match, summoner_riot_id)

        # assists
        data["Assists"] += participant_data["assists"]

        # ability uses
        data["Ability Uses"] += participant_data["challenges"]["abilityUses"]

        # damage per minute
        total_damage_per_minute += participant_data["challenges"]["damagePerMinute"]

        # gold per minute
        total_gold_per_minute += participant_data["challenges"]["goldPerMinute"]

        # kda
        total_kda += participant_data["challenges"]["kda"]

        # kill participation
        total_kp += participant_data["challenges"]["killParticipation"]

        # skilshots
        data["Skillshots Hit"] += participant_data["challenges"]["skillshotsHit"]

        # solo kills
        data["Solo Kills"] += participant_data["challenges"]["soloKills"]
        
        # team damage percentage
        total_team_damage_percentage += participant_data["challenges"]["teamDamagePercentage"]

        # damage to champtions
        total_damage_to_champions += participant_data["totalDamageDealtToChampions"]

        # enemy missing pings
        data["Enemy Missing Pings"] += participant_data["enemyMissingPings"]

    data["Average Damage Per Minute"] = total_damage_per_minute/total_matches
    data["Average Gold Per Minute"] = total_gold_per_minute/total_matches
    data["Average KDA"] = total_kda/total_matches
    data["Average Kill Participation"] = total_kp/total_matches
    data["Average Team Damage Percentage"] = total_team_damage_percentage/total_matches
    data["Average Damage To Champions"] = total_damage_to_champions/total_matches

    # Round values to 2 decimal places
    rounded_data = {key: round(value, 2) for key, value in data.items()}

    return rounded_data
