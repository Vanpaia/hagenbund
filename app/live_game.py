from app import db
from app.models import PredictionVote
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
        results = defaultdict(dict)
        for round, data in self.submissions.items():
            for player, result in data["votes"].items():
                if not results[player]:
                    results[player] = {"total": {"number": 0, "rounds": 0}}
                results[player]["total"]["number"] += int(result["vote"])
                results[player]["total"]["rounds"] += 1
        for player in results.values():
            print(player["total"]["number"] / player["total"]["rounds"])
        socketio.emit('end_game')
        self.finalize_game_to_db()

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
        for round in self.submissions.values():
            prediction_id = int(round["id"])
            for player, result in round["votes"].items():
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


def background_timer_task(socketio, state):
    while state.is_active is True:
        socketio.sleep(0.5)
        remaining = state.emit_timer_update(socketio)
        if remaining <= 0:
            state.end_round(socketio)


game_instance = GameState()
