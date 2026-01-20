from flask_socketio import emit, join_room, leave_room
from .. import socketio, game_instance
from app.live_game import background_timer_task
from flask_login import current_user
from app.registry import online_users
from app.models import Prediction


@socketio.on('connect')
def connect():
    if not current_user.is_authenticated:
        return False
    print('Client connected: ', current_user.user_name)
    emit('my response', {'data': 'Connected'})
    online_users.add_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected: ', current_user.user_name)
    online_users.remove_user(current_user.user_name)
    emit('user_list', online_users.get_all_users(), broadcast=True)
    if current_user.id in game_instance.players:
        game_instance.players.remove((current_user.id, current_user.user_name))
        emit('player_update', list(game_instance.players), to='game_room')

# Chatroom 

@socketio.on('chat_message')
def handle_broadcast_event(message):
    emit('chat_broadcast', {'data': message['data']}, broadcast=True)

# Game

@socketio.on('game_connect')
def game_connect():
    if current_user.is_authenticated:
        print('Client connected to game: ', current_user.user_name)
        join_room('game_room')
        game_instance.players.add((current_user.id, current_user.user_name))
        emit('player_update', list(game_instance.players), to='game_room')
        if game_instance.is_active:
            status = game_instance.get_game_status()
            emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('submit_prediction_vote')
def handle_submission(submission):
    if not game_instance.submissions[submission["round"]]:
        game_instance.submissions[submission["round"]] = {"uuid": submission["uuid"], "votes": {}}
    game_instance.submissions[submission["round"]]["votes"][current_user.id] = int(submission["vote"])
    print(game_instance.submissions)
    if len(game_instance.submissions[submission["round"]]) >= len(game_instance.players):
        if not game_instance.is_processing_round:
            if submission["round"] == game_instance.current_round:
                game_instance.is_processing_round = True
                game_instance.next_round(socketio)

@socketio.on('next_round')
def next_round():
    if game_instance.current_round < game_instance.total_rounds:
        game_instance.is_processing_round = True
        game_instance.next_round(socketio)

@socketio.on('previous_round')
def previous_round():
    game_instance.previous_round(socketio)
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('start_game')
def handle_start(round_length):
    predictions = Prediction.query.all()
    questions = [prediction.to_dict() for prediction in predictions]
    kwargs = {"questions": questions}
    if round_length.get('data'):
        kwargs["round_length"] = int(round_length['data'])
    game_instance.init_game(**kwargs)
    game_instance.start_round(socketio)
    socketio.start_background_task(background_timer_task, socketio, game_instance)
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('stop_game')
def handle_stop():
    game_instance.reset()
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('toggle_pause')
def handle_toggle():
    if game_instance.is_paused:
        game_instance.unpause_round()
    else:
        game_instance.pause_round()

    status = game_instance.get_timer_status()
    emit('timer_status_update', status, broadcast=True, to='game_room')
