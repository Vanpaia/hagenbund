from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement, StockPick, StockUpdate, PredictionStatus

app = create_app(config_class=Config)

with app.app_context():
    db.session.query(Prediction).update({Prediction.status: PredictionStatus.PENDING})
    db.session.commit()
