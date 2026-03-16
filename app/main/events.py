from flask_socketio import emit, join_room, leave_room
from flask import request
from .. import socketio
from app import db
from app.live_game import game_instance
from app.live_game import background_timer_task
from flask_login import current_user
from app.registry import online_users
from app.models import Prediction, Category, User, UserAchievement


@socketio.on('connect')
def connect():
    if not current_user.is_authenticated:
        return False
    print('Client connected: ', current_user.user_name)
    join_room(f"user_{current_user.id}")
    emit('my response', {'data': 'Connected'})
    online_users.add_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)
    outstanding_achievements = UserAchievement.query.filter_by(user_id=current_user.id, is_notified=False).all()
    if outstanding_achievements:
        for award in outstanding_achievements:
            socketio.emit('achievement_unlocked', {
                'title': award.achievement.title,
                'description': award.achievement.description, 
                'image': award.achievement.logo, 
                'id': award.id,
                'earned_at': award.earned_at.isoformat(),
            }, to=f"user_{current_user.id}")
            award.is_notified = True
        db.session.commit()
    

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected: ', current_user.user_name)
    online_users.remove_user(current_user.user_name)
    emit('user_list', online_users.get_all_users(), broadcast=True)
    if current_user.id in game_instance.players.keys():
        game_instance.players[current_user.id]["sid"].discard(request.sid)
        if not game_instance.players[current_user.id]["sid"]:
            del game_instance.players[current_user.id]
            game_instance.total_players -= 1
            emit('player_update', [{"name": player["name"], "id": player["id"]} for player in game_instance.players.values()], to='game_room')

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
        if not current_user.id in game_instance.players:
            game_instance.players[current_user.id] = {"id": current_user.id, "name":current_user.user_name, "sid":{request.sid}}
            game_instance.total_players += 1
        else:
            game_instance.players[current_user.id]["sid"].add(request.sid)
        print(game_instance.players)
        emit('player_update', [{"name": player["name"], "id": player["id"]} for player in game_instance.players.values()], to='game_room')
        emit('player_info', {"id": current_user.id, "name": current_user.user_name}, to=f"user_{current_user.id}")
        if game_instance.is_active:
            status = game_instance.get_game_status()
            emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('submit_prediction_vote')
def handle_submission(submission):
    if game_instance.total_players > 1:
        round = game_instance.questions[game_instance.current_round-1] if len(game_instance.questions) > 0 else {}
        if round["user_id"] == submission["user_id"]:
            return
    if not game_instance.submissions[submission["round"]]:
        game_instance.submissions[submission["round"]] = {"id": submission["id"], "votes": {}}
    remaining = game_instance.get_remaining_ms(round_num=submission["round"])
    game_instance.submissions[submission["round"]]["votes"][submission["user_id"]] = {"vote": int(submission["vote"]), "speed": game_instance.round_length - remaining, "name": submission["name"]}
    target_votes = max(game_instance.total_players - 1, 1)
    print(submission)
    print("Target: ", target_votes)
    print("Current: ", len(game_instance.submissions[submission["round"]]["votes"]))
    print(game_instance.submissions[submission["round"]]["votes"])
    if len(game_instance.submissions[submission["round"]]["votes"]) >= target_votes:
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
def handle_start(game_config):
    predictions = []
    if game_config.get("test", False):
        for category in Category:
            predictions.extend(
                Prediction.query
                .join(User)
                .filter(
                    User.user_name == "Test", 
                    Prediction.category == category
                )
                .order_by(Prediction.uuid_key)
                .all()
            )
    else:
        for category in Category:
            predictions.extend(Prediction.query.filter_by(
                category=category.name
        ).order_by(Prediction.uuid_key).all())
    questions = [prediction.to_dict() for prediction in predictions]
    kwargs = {"questions": questions}
    if game_config["data"].get('length'):
        kwargs["round_length"] = int(game_config["data"]['length'])
    if game_config["data"].get('player'):
        kwargs["player_amount"] = int(game_config["data"]['player'])
    print(kwargs)
    game_instance.init_game(**kwargs)
    game_instance.start_round(socketio)
    socketio.start_background_task(background_timer_task, socketio, game_instance)
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('stop_game')
def handle_stop():
    emit('clear_game', broadcast=True, to='game_room')
    game_instance.reset()
    status = game_instance.get_game_status()
    emit('game_status_update', status, broadcast=True, to='game_room')

@socketio.on('save_game')
def handle_save():
    game_instance.save_game()

@socketio.on('toggle_pause')
def handle_toggle():
    if game_instance.is_paused:
        game_instance.unpause_round()
    else:
        game_instance.pause_round()

    status = game_instance.get_timer_status()
    emit('timer_status_update', status, broadcast=True, to='game_room')
