from flask_socketio import emit
from .. import socketio
from flask_login import current_user
from app.registry import online_users


@socketio.on('connect')
def test_connect():
    print('Client connected: ', current_user.user_name)
    emit('my response', {'data': 'Connected'})
    online_users.add_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected: ', current_user.user_name)
    online_users.remove_user(current_user.user_name)
    # Broadcast the updated list to everyone
    emit('user_list', online_users.get_all_users(), broadcast=True)

@socketio.on('chat_message')
def handle_broadcast_event(message):
    emit('chat_broadcast', {'data': message['data']}, broadcast=True)
