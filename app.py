from app import create_app, db, socketio
from app.models import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'socketio': socketio}

if __name__ == '__main__':
    # Use socketio.run instead of app.run
    socketio.run(app, debug=True)
