from app import create_app, db
from config import Config

from app.models import User, Prediction

app = create_app(config_class=Config)

with app.app_context():
    predictions = User.query.all()

    for x in predictions:
        print(x.user_name, x.id)
