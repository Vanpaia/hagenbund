from app import create_app, db
from config import Config

from app.models import Prediction, User, Category

app = create_app(config_class=Config)

with app.app_context():
    users = User.query.all()
    for user in users:
        for category in Category:
            preds = Prediction.query.filter_by(
                user_id=user.id, 
                category=category
            ).order_by(Prediction.uuid_key).all()
            
            for position, pred in enumerate(preds, start=1):
                pred.position = position  # 1-indexed
                pred.multiplier = 1
    db.session.commit()
