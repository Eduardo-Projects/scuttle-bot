import os
import requests

topgg_token = os.getenv("TOPGG_TOKEN")
topgg_id = os.getenv("TOPGG_ID")

async def update_stats(bot):
    try:
        url=f"https://top.gg/api/bots/{topgg_id}/stats"
        data = {
            'server_count': len(bot.guilds),
            'shard_count': bot.shard_count
        }
        headers = {
            'Authorization': topgg_token
        }
        response = requests.post(url, json=data, headers=headers)

        response.raise_for_status()

        print(f"Successfully updated top.gg stats. Server count={len(bot.guilds)} and Shard count={bot.shard_count}")
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"An error occured updating top.gg stats: {e}")