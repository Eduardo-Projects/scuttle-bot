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

        print(f"Successfully updated top.gg stats. {response.json()}")
    except Exception as e:
        print(f"An error occured updating top.gg stats: {e}")