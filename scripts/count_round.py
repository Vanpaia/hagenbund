import pickle
from collections import defaultdict
from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement

app = create_app(config_class=Config)

file = './saved_games/game_data_150_2026-03-07_14-56-13.pkl'

with open(file, "rb") as f:
    obj = pickle.load(f)



player_results = defaultdict(dict)

# First double loop to get total scores and participated rounds
for round_num, data in obj.items():
    for player, result in data["votes"].items():
        if not player_results[player]:
            player_results[player] = {"name": result["name"], "total_score": 0, "total_rounds": 0, "average_score": 0, "weighted_score": 0, "votes": [], "speeds": [], "max_speed": 0, "avg_speed": 0}
        player_results[player]["total_score"] += int(result["vote"])
        player_results[player]["votes"].append(int(result["vote"]))
        player_results[player]["speeds"].append(int(result["speed"]))
        player_results[player]["total_rounds"] += 1

# Calculating weighted score per player
for player, stats in player_results.items():
    stats["average_score"] = stats["total_score"] / stats["total_rounds"]
    stats["max_speed"] = min(stats["speeds"])
    stats["avg_speed"] = sum(stats["speeds"]) / stats["total_rounds"]
    stats["average_score"] = stats["total_score"] / stats["total_rounds"]
    stats["weighted_score"] = 10000 * stats["total_rounds"] / stats["total_score"]


for index, data in player_results.items():
    print(data["name"])
    print("Average Score: ", data["average_score"])
    print("Weighted Score: ", data["weighted_score"])
    print("Max Speed: ", data["max_speed"])
    print("Average Speed: ", data["avg_speed"])
