import time
from collections import defaultdict

class GameState:
    def __init__(self, round_length = 30000):
        self.round_length = round_length
        self.end_time = 0
        self.is_paused = True
        self.is_active = False 
        self.pause_time_remaining = round_length
        self.players = set()
        self.questions = []
        self.current_round = 1 
        self.total_rounds = len(self.questions)
        self.submissions = defaultdict(dict)
        self.is_processing_round = False

    def init_game(self, questions, round_length=30000):
        self.is_active = True
        self.round_length = round_length
        self.questions = questions
        self.total_rounds = len(questions)

    def start_round(self, socketio):
        self.is_paused = False
        self.is_active = True
        now = time.time() * 1000
        self.end_time = now + self.round_length
        self.pause_time_remaining = self.round_length

        status = self.get_game_status()
        socketio.emit('game_status_update', status, to='game_room')

    def reset(self):
        self.is_paused = True
        self.is_active = False
        self.pause_time_remaining = self.round_length
        self.players = set()
        self.questions = []
        self.current_round = 1
        self.total_rounds = len(self.questions)
        self.submissions = defaultdict(dict)
        self.is_processing_round = False

    def pause_round(self):
        self.is_paused = True
        now = time.time() * 1000
        self.pause_time_remaining = max(0, self.end_time - now)

    def unpause_round(self):
        self.is_paused = False
        now = time.time() * 1000
        self.end_time = now + self.pause_time_remaining 

    def next_round(self, socketio):
        try:
            if self.current_round < self.total_rounds:
                self.current_round += 1
                self.start_round(socketio)
        finally:
            self.is_processing_round = False

    def previous_round(self, socketio):
        if self.current_round > 1:
            self.current_round -= 1
        self.start_round(socketio)

    def end_round(self, socketio):
        round_data = self.questions[self.current_round-1] if len(self.questions) > 0 else {}
        socketio.emit('end_round', {"uuid": round_data["uuid"], "round": self.current_round})
        self.is_processing_round = True
        socketio.sleep(0.5) 
        self.next_round(socketio)

    def get_remaining_ms(self):
        if self.is_paused:
            return self.pause_time_remaining
        
        now = time.time() * 1000
        remaining = self.end_time - now
        return max(0, int(remaining))

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


def background_timer_task(socketio, state):
    while state.is_active is True:
        socketio.sleep(0.5)
        remaining = state.emit_timer_update(socketio)
        if remaining <= 0:
            state.end_round(socketio)
