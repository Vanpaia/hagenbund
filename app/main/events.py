from flask_socketio import emit
from .. import socketio, game_instance
from app.live_game import background_timer_task
from flask_login import current_user
from app.registry import online_users
from app.models import Prediction


@socketio.on('connect')
def connect():
    print('Client connected: ', current_user.user_name)
    emit('my response', {'data': 'Connected'})
    online_users.add_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)
    if game_instance.is_active:
        status = game_instance.get_game_status()
        emit('game_status_update', status, broadcast=True)
        emit('game_status_update', {
            'is_paused': game_instance.is_paused, 
            'is_active': game_instance.is_active, 
            'remaining_ms': game_instance.round_length,
            'current_round': game_instance.current_round,
            'data': game_instance.questions[game_instance.current_round-1],
        }, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected: ', current_user.user_name)
    online_users.remove_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)

# Chatroom 

@socketio.on('chat_message')
def handle_broadcast_event(message):
    emit('chat_broadcast', {'data': message['data']}, broadcast=True)

# Game

@socketio.on('next_round')
def next_round():
    if game_instance.current_round < game_instance.total_rounds:
        game_instance.next_round(socketio)
        status = game_instance.get_game_status()
        emit('game_status_update', status, broadcast=True)

@socketio.on('previous_round')
def previous_round():
    game_instance.previous_round(socketio)
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True)

@socketio.on('start_game')
def handle_start():

    predictions = Prediction.query.all()
    questions = [prediction.to_dict() for prediction in predictions]
    game_instance.init_game(questions)
    game_instance.start_round(socketio)
    socketio.start_background_task(background_timer_task, socketio, game_instance)
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True)

@socketio.on('stop_game')
def handle_stop():
    game_instance.reset()
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True)

@socketio.on('toggle_pause')
def handle_toggle():
    if game_instance.is_paused:
        game_instance.unpause_round()
    else:
        game_instance.pause_round()

    status = game_instance.get_timer_status()
    emit('timer_status_update', status, broadcast=True)
