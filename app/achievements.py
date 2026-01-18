from app import db
from models import Achievement, UserAchievement


def set_achievement(achievement, user, socketio):
    achievement = Achievement.query.filter_by(title=achievement).first()
    if not achievement:
        return

    new_award = UserAchievement(user_id=user.id, achievement_id=achievement.id)
    db.session.add(new_award)
    db.session.commit()

    socketio.emit('achievement_unlocked', {
        'title': achievement.title,
        'description': achievement.description, 
        'id': new_award.id,
        'earned_at': new_award.created_at.isoformat(),
    }, room=f"user_{user.id}")

def mark_achievement_notified(award_id):
    award = UserAchievement.query.filter_by(
        id=award_id, 
    ).first()

    if award:
        award.is_notified = True
        db.session.commit()
