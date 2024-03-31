# Calculates stats for a summoner with a given set of matches data
def calculate_stats(summoner_puuid, matches_data):
    data_keys = [
        "Total Matches",
        "Average Assists",
        "Ability Uses",
        "Average Damage Per Minute",
        "Average Gold Per Minute",
        "Average KDA",
        "Average Kill Participation",
        "Skillshots Hit",
        "Average Solo Kills",
        "Average Team Damage Percentage",
        "Average Damage To Champions",
        "Average Enemy Missing Pings",
    ]
    # Initialize the dictionary with keys set to 0
    data = {key: 0 for key in data_keys}

    if matches_data:
        print(
            f"Calculating stats for summoner with puuid {summoner_puuid} for the last {len(matches_data)} matches"
        )
        data["Total Matches"] = len(matches_data)
        for match in matches_data:
            participants = match["info"]["participants"]
            stats = next(
                (obj for obj in participants if obj.get("puuid") == summoner_puuid),
                None,
            )
            challenges = stats.get("challenges", {})

            data["Average Assists"] += stats.get("assists", 0)
            data["Ability Uses"] += challenges.get("abilityUses", 0)
            data["Skillshots Hit"] += challenges.get("skillshotsHit", 0)
            data["Average Solo Kills"] += challenges.get("soloKills", 0)
            data["Average Enemy Missing Pings"] += stats.get("enemyMissingPings", 0)
            data["Average Damage Per Minute"] += challenges.get("damagePerMinute", 0)
            data["Average Gold Per Minute"] += challenges.get("goldPerMinute", 0)
            data["Average KDA"] += challenges.get("kda", 0)
            data["Average Kill Participation"] += challenges.get("killParticipation", 0)
            data["Average Team Damage Percentage"] += challenges.get(
                "teamDamagePercentage", 0
            )
            data["Average Damage To Champions"] += stats.get(
                "totalDamageDealtToChampions", 0
            )

        # calculate averages
        data = {
            key: (value / len(matches_data) if "Average" in key else value)
            for key, value in data.items()
        }
        # Round values to 2 decimal places
        rounded_data = {key: round(value, 2) for key, value in data.items()}

        print(f"Finished calculating stats.")
        return rounded_data
    else:
        print(
            f"Error calculating stats for summoner with puuid {summoner_puuid}. No matches data provided."
        )
        return data
