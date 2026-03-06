from app import create_app, db
from config import Config

from app.models import User, Achievement

app = create_app(config_class=Config)

with app.app_context():
    users = Achievement.query.all()
    for x in users:
        print(x.id)

