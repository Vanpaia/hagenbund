from app import create_app, db
from config import Config

from app.models import UserAchievement

app = create_app(config_class=Config)

with app.app_context():
    db.session.query(UserAchievement).update({UserAchievement.is_notified: True})
    db.session.commit()

    wrong_achievement_klaas = UserAchievement.query.filter_by(user_id=5, achievement_id=4).first()
    wrong_achievement_vlad = UserAchievement.query.filter_by(user_id=3, achievement_id=4).first()
    wrong_achievement_tom = UserAchievement.query.filter_by(user_id=4, achievement_id=3).first()
    db.session.delete(wrong_achievement_klaas)
    db.session.delete(wrong_achievement_vlad)
    db.session.delete(wrong_achievement_tom)

    new_award_vlad = UserAchievement(user_id=3, achievement_id=3)
    new_award_tom = UserAchievement(user_id=4, achievement_id=4)
    db.session.add(new_award_vlad)
    db.session.add(new_award_tom)
    new_oops_vlad = UserAchievement(user_id=3, achievement_id=11)
    new_oops_tom = UserAchievement(user_id=4, achievement_id=11)
    new_oops_klaas = UserAchievement(user_id=5, achievement_id=11)
    db.session.add(new_oops_klaas)
    db.session.add(new_oops_tom)
    db.session.add(new_oops_vlad)
    db.session.commit()
