from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement

app = create_app(config_class=Config)

with app.app_context():
    user = User.query.all()
    for x in user:
        predictions = Prediction.query.filter_by(user_id = x.id).all()
        print(x.user_name, len(predictions))
