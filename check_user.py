from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement, StockPick, StockUpdate

app = create_app(config_class=Config)

with app.app_context():
    users = User.query.all()
    for x in users:
        print(x.id, x.user_name, x.total_investment)
