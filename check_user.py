from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement, StockPick, StockUpdate

app = create_app(config_class=Config)

with app.app_context():
    users = User.query.all()
    for user in users:
        print(user.user_name)
        print(user.total_prediction_points)
        print(user.total_achieved_points)
