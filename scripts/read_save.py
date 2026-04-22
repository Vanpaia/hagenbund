import pickle
from collections import defaultdict

file = './saved_games/game_data_150_2026-03-07_14-56-13.pkl'

with open(file, "rb") as f:
    obj = pickle.load(f)


def update_best_stats(stats_list, name, value, find_max=False):
    """
    Updates a list of records. 
    If value is better, replaces the list. 
    If value is equal, appends to the list.
    
    :param stats_list: The list to update (e.g., game_results["quickest_player"])
    :param name: Player name or ID
    :param value: The numeric score/speed to compare
    :param find_max: Set to True for "Highest", False for "Lowest/Quickest"
    """
    if not stats_list:
        return [{"name": name, "value": value}]

    best_value = stats_list[0]["value"]

    # Check if the new value is "Better"
    is_better = value > best_value if find_max else value < best_value
    is_equal = value == best_value

    if is_better:
        # New record breaker! Replace the whole list
        return [{"name": name, "value": value}]
    elif is_equal:
        # It's a tie! Add to the existing list
        stats_list.append({"name": name, "value": value})
        
    return stats_list


player_results = defaultdict(dict)
prediction_results = defaultdict(dict)
game_results = {"highest_round": {"question": None, "value":None}, "quickest_round": {"id": None, "value":None}, "highest_score": [], "highest_speed": [], "lowest_score":[], "lowest_speed": [],  "quickest_player": []}

# First double loop to get total scores and participated rounds
for round_num, data in obj.items():
    if not prediction_results[round_num]:
        prediction_results[round_num] = {"id": data["id"], "points": 0, "likelihood": 0, "speed": 0, "votes": 0, "average_likelihood": 0, "average_speed": 0}
    for player, result in data["votes"].items():
        prediction_results[round_num]["votes"] += 1
        prediction_results[round_num]["likelihood"] += int(result["vote"])
        prediction_results[round_num]["speed"] += int(result["speed"])
        if not player_results[player]:
            player_results[player] = {"name": result["name"], "total_score": 0, "total_rounds": 0, "average_score": 0, "weighted_score": 0, "votes": [], "speeds": [], "max_speed": 0, "avg_speed": 0}
        player_results[player]["total_score"] += int(result["vote"])
        player_results[player]["votes"].append(int(result["vote"]))
        player_results[player]["speeds"].append(int(result["speed"]))
        player_results[player]["total_rounds"] += 1
        game_results["quickest_player"] = update_best_stats(
            game_results["quickest_player"], 
            result["name"], 
            int(result["speed"]), 
            find_max=False
            )


# Calculating high scores
for round_num, stats in prediction_results.items():
    stats["average_speed"] = stats["speed"] / stats["votes"]
    stats["average_likelihood"] = stats["likelihood"] / stats["votes"]
    if game_results["quickest_round"]["value"] == None: 
        game_results["quickest_round"]["value"] = stats["average_speed"]
        game_results["quickest_round"]["question"] = stats["id"]
    elif game_results["quickest_round"]["value"] > stats["average_speed"]: 
        game_results["quickest_round"]["value"] = stats["average_speed"]
        game_results["quickest_round"]["question"] = stats["id"]
    if game_results["highest_round"]["value"] == None: 
        game_results["highest_round"]["value"]  = stats["average_likelihood"]
        game_results["highest_round"]["question"] = stats["id"]
    elif game_results["highest_round"]["value"] < stats["average_likelihood"]: 
        game_results["highest_round"]["value"]  = stats["average_likelihood"]
        game_results["highest_round"]["question"] = stats["id"]

# Calculating weighted score per player
for player, stats in player_results.items():
    stats["average_score"] = stats["total_score"] / stats["total_rounds"]
    stats["max_speed"] = min(stats["speeds"])
    stats["avg_speed"] = sum(stats["speeds"]) / stats["total_rounds"]
    stats["average_score"] = stats["total_score"] / stats["total_rounds"]
    stats["weighted_score"] = 10000 * stats["total_rounds"] / stats["total_score"]
    game_results["highest_score"] = update_best_stats(
        game_results["highest_score"], 
        stats["name"], 
        stats["average_score"],
        find_max=True
        )
    game_results["lowest_score"] = update_best_stats(
        game_results["lowest_score"], 
        stats["name"], 
        stats["average_score"],
        find_max=False
        )
    game_results["highest_speed"] = update_best_stats(
        game_results["highest_speed"], 
        stats["name"], 
        stats["avg_speed"],
        find_max=True
        )
    game_results["lowest_speed"] = update_best_stats(
        game_results["lowest_speed"], 
        stats["name"], 
        stats["avg_speed"],
        find_max=False
        )



# Second double loop to score using weighted system 
for round_num, data in obj.items():
    prediction_results[round_num]["average_likelihood"] = prediction_results[round_num]["likelihood"] / prediction_results[round_num]["votes"]
    prediction_results[round_num]["average_speed"] = prediction_results[round_num]["speed"] / prediction_results[round_num]["votes"]
    for player, result in data["votes"].items():
        point_contribution = round(100-(int(result["vote"])) * player_results[player]["weighted_score"])
        prediction_results[round_num]["points"] += point_contribution

print(game_results)
