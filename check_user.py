from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement, StockPick, StockUpdate

app = create_app(config_class=Config)
ids = [158, 78]

with app.app_context():
    preds = Prediction.query.filter(Prediction.id.in_(ids)).all()
    for x in preds:
        print(x.id, x.title, x.author)
