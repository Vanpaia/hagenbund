from app import db
from app.models import Prediction, PredictionVote
import time
from collections import defaultdict

class GameState:
    def __init__(self, round_length = 30000):
        self.round_length = round_length
        self.round_clocks = {}
        self.is_paused = True
        self.is_active = False 
        self.players = set()
        self.total_players = len(self.players)
        self.questions = []
        self.current_round = 1 
        self.total_rounds = len(self.questions)
        self.submissions = defaultdict(dict)
        self.is_processing_round = False

    def init_game(self, questions, player_amount=None, round_length=30000):
        self.is_active = True
        self.round_length = round_length
        if player_amount:
            self.total_players = player_amount
        self.questions = questions
        self.total_rounds = len(questions)

    def start_round(self, socketio):
        self.is_paused = False
        self.is_active = True
        now = time.time() * 1000
        self.end_time = now + self.round_length
        self.pause_time_remaining = self.round_length
        round_id = self.questions[self.current_round-1]["id"]
        self.round_clocks[round_id] = {"end_time": now + self.round_length, "pause_time_remaining": self.round_length}

        status = self.get_game_status()
        socketio.emit('game_status_update', status, to='game_room')

    def reset(self):
        self.is_paused = True
        self.is_active = False
        self.round_clocks = {}
        self.players = set()
        self.total_players = len(self.players)
        self.current_round = 1
        self.total_rounds = len(self.questions)
        self.submissions = defaultdict(dict)
        self.is_processing_round = False

    def pause_round(self):
        self.is_paused = True
        now = time.time() * 1000
        round_id = self.questions[self.current_round-1]["id"]
        self.round_clocks[round_id]["pause_time_remaining"] = max(0, self.end_time - now)

    def unpause_round(self):
        self.is_paused = False
        now = time.time() * 1000
        round_id = self.questions[self.current_round-1]["id"]
        self.round_clocks[round_id]["end_time"] = now + self.pause_time_remaining 

    def next_round(self, socketio):
        try:
            if self.current_round < self.total_rounds:
                self.current_round += 1
                self.start_round(socketio)
            else:
                self.end_game(socketio)
        finally:
            self.is_processing_round = False

    def previous_round(self, socketio):
        if self.current_round > 1:
            self.current_round -= 1
        self.start_round(socketio)

    def end_round(self, socketio):
        round_data = self.questions[self.current_round-1] if len(self.questions) > 0 else {}
        socketio.emit('end_round', {"id": round_data["id"], "round": self.current_round})
        self.is_processing_round = True
        socketio.sleep(0.5) 
        self.next_round(socketio)

    def end_game(self, socketio):
        self.is_active = False
        player_results = defaultdict(dict)
        prediction_results = defaultdict(dict)

        # First double loop to get total scores and participated rounds
        for round_num, data in self.submissions.items():
            if not prediction_results[round_num]:
                prediction_results[round_num] = {"points": 0, "likelihood": 0, "speed": 0, "votes": 0, "average_likelihood": 0, "average_speed": 0}
            for player, result in data["votes"].items():
                prediction_results[round_num]["votes"] += 1
                prediction_results[round_num]["likelihood"] += int(result["vote"])
                prediction_results[round_num]["speed"] += int(result["speed"])
                if not player_results[player]:
                    player_results[player] = {"total_score": 0, "total_rounds": 0, "average_score": 0, "weighted_score": 0}
                player_results[player]["total_score"] += int(result["vote"])
                player_results[player]["total_rounds"] += 1
        
        # Calculating weighted score per player
        for player, stats in player_results.items():
            stats["average_score"] = stats["total_score"] / stats["total_rounds"]
            stats["weighted_score"] = 10000 * stats["total_rounds"] / stats["total_score"]

        # Second double loop to score using weighted system 
        for round_num, data in self.submissions.items():
            prediction_results[round_num]["average_likelihood"] = prediction_results[round_num]["likelihood"] / prediction_results[round_num]["votes"]
            prediction_results[round_num]["average_speed"] = prediction_results[round_num]["speed"] / prediction_results[round_num]["votes"]
            for player, result in data["votes"].items():
                point_contribution = round(int(result["vote"]) * player_results[player]["weighted_score"])
                prediction_results[round_num]["points"] += point_contribution
        print(prediction_results)
        socketio.emit('end_game')
        self.finalize_game_to_db()
        self.bulk_update_predictions(prediction_results)

    def get_remaining_ms(self, round_num=None):
        if round_num is None:
            round_num = self.current_round
        
        if not self.questions or round_num < 1 or round_num > len(self.questions):
            return 0
        try:
            round_id = self.questions[round_num - 1]["id"]
            clock = self.round_clocks.get(round_id)
            
            if not clock:
                return self.round_length

            if self.is_paused:
                return clock["pause_time_remaining"]
            
            now = time.time() * 1000
            remaining = clock["end_time"] - now
            return max(0, int(remaining))
            
        except (IndexError, KeyError):
            return 0

    def get_game_status(self):
        remaining = self.get_remaining_ms()
        round_data = self.questions[self.current_round-1] if len(self.questions) > 0 else {}
        status = {
            'remaining_ms': remaining,
            'is_paused': self.is_paused,
            'is_active': self.is_active,
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'round_length': self.round_length,
            'round_data': round_data,
        }
        return status

    def get_timer_status(self):
        remaining = self.get_remaining_ms()
        status = {
            'remaining_ms': remaining,
            'is_paused': self.is_paused,
        }
        return status

    def emit_timer_update(self, socketio):
        status = self.get_timer_status()
        socketio.emit('timer_status_update', status, to='game_room')

        return status["remaining_ms"]

    def finalize_game_to_db(self):
        vote_entries = []
        for round_num in self.submissions.values():
            prediction_id = int(round_num["id"])
            for player, result in round_num["votes"].items():
                user_id = int(player)
                vote = int(result["vote"])
                speed = float(result["speed"])
                vote_entries.append({
                    "user_id": user_id,
                    "prediction_id": prediction_id,
                    "vote": vote,
                    "speed": speed,
                })
        print(len(vote_entries))
        # Bulk save votes
        db.session.bulk_insert_mappings(PredictionVote, vote_entries)
        db.session.commit()

    def bulk_update_predictions(self, prediction_results):
        update_data = []
        
        for pred_id, stats in prediction_results.items():
            # Ensure points is an integer if your DB column requires it
            final_points = round(stats["points"])
            
            # likelihood is the "average_likelihood" we calculated earlier
            avg_likelihood = stats["likelihood"] / stats["votes"] if stats["votes"] > 0 else 0
            
            update_data.append({
                "id": pred_id,
                "points": final_points,
                "likelihood": avg_likelihood
            })

        try:
            # This generates a single efficient SQL statement (e.g., using a CASE statement or temp table)
            db.session.bulk_update_mappings(Prediction, update_data)
            db.session.commit()
            print(f"Successfully updated {len(update_data)} predictions.")
        except Exception as e:
            db.session.rollback()
            print(f"Bulk update failed: {e}")
            raise e


def background_timer_task(socketio, state):
    while state.is_active is True:
        socketio.sleep(0.5)
        remaining = state.emit_timer_update(socketio)
        if remaining <= 0:
            state.end_round(socketio)


game_instance = GameState()
