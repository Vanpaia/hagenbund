from app import db
from app.models import Achievement, UserAchievement, User


def set_achievement(achievement_id, user_name, socketio):
    try:
        achievement = Achievement.query.filter_by(id=achievement_id).first()
        if not achievement:
            return

        user = User.query.filter_by(user_name=user_name).first()
        new_award = UserAchievement(user_id=user.id, achievement_id=achievement.id)
        db.session.add(new_award)
        db.session.commit()

        socketio.emit('achievement_unlocked', {
            'title': achievement.title,
            'description': achievement.description, 
            'id': new_award.id,
            'earned_at': new_award.created_at.isoformat(),
        }, room=f"user_{user.id}")
    except:
        return

def mark_achievement_notified(award_id):
    award = UserAchievement.query.filter_by(
        id=award_id, 
    ).first()

    if award:
        award.is_notified = True
        db.session.commit()

def add_achievement_to_session(achievement_id, user_name):
    """Adds the record to the session but DOES NOT commit."""
    user = User.query.filter_by(user_name=user_name).first()
    achievement = Achievement.query.get(achievement_id)
    
    if not user or not achievement:
        return None

    # Check for existing
    exists = UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement_id).first()
    if exists:
        return None

    new_award = UserAchievement(user_id=user.id, achievement_id=achievement.id)
    db.session.add(new_award)
    return (user.id, achievement.title, achievement.description)

