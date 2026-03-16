from app import create_app, db
from config import Config

from app.models import UserAchievement

app = create_app(config_class=Config)

with app.app_context():
    db.session.query(UserAchievement).update({UserAchievement.is_notified: True})
    db.session.commit()

    wrong_achievement = UserAchievement.query.filter_by(user_id=5, achievement_id=4).first()
    db.session.delete(wrong_achievement)
    db.session.commit()
