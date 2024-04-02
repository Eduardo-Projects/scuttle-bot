# Calculates stats for a summoner with a given set of matches data
def calculate_stats(summoner_puuid, matches_data):
    data_keys = [
        "Total Matches",
        "Avg. Kills",
        "Avg. Deaths",
        "Avg. Assists",
        "Avg. Damage Per Minute",
        "Avg. Gold Per Minute",
        "Avg. KDA",
        "Avg. Kill Participation",
        "Avg. Solo Kills",
        "Avg. Team Damage Percentage",
        "Avg. Damage To Champions",
        "Avg. Vision Score",
        "Avg. Assist Me Pings",
        "Avg. Enemy Missing Pings",
        "Avg. Control Wards Placed",
        "Ability Uses",
        "Games Surrendered",
        "Scuttle Crab Kills",
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

            if stats.get("gameEndedInSurrender"):
                data["Games Surrendered"] += 1

            data["Avg. Kills"] += stats.get("kills")
            data["Avg. Deaths"] += stats.get("deaths")
            data["Avg. Vision Score"] += stats.get("visionScore")
            data["Avg. Control Wards Placed"] += challenges.get("controlWardsPlaced")
            data["Avg. Assist Me Pings"] += stats.get("assistMePings")
            data["Scuttle Crab Kills"] += challenges.get("scuttleCrabKills")
            data["Avg. Damage To Champions"] += stats.get(
                "totalDamageDealtToChampions", 0
            )
            data["Avg. Assists"] += stats.get("assists", 0)
            data["Ability Uses"] += challenges.get("abilityUses", 0)
            data["Avg. Solo Kills"] += challenges.get("soloKills", 0)
            data["Avg. Enemy Missing Pings"] += stats.get("enemyMissingPings", 0)
            data["Avg. Damage Per Minute"] += challenges.get("damagePerMinute", 0)
            data["Avg. Gold Per Minute"] += challenges.get("goldPerMinute", 0)
            data["Avg. KDA"] += challenges.get("kda", 0)
            data["Avg. Kill Participation"] += challenges.get("killParticipation", 0)
            data["Avg. Team Damage Percentage"] += challenges.get(
                "teamDamagePercentage", 0
            )

        # calculate averages
        data = {
            key: (value / len(matches_data) if "Avg." in key else value)
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
