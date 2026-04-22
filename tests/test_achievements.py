import pytest
from unittest.mock import MagicMock

from app import db
from app.models import UserAchievement
from app.achievements import set_achievement, mark_achievement_notified, add_achievement_to_session


def test_set_achievement_creates_record(user, achievement):
    mock_socketio = MagicMock()
    set_achievement(achievement.id, user.user_name, mock_socketio)

    award = UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first()
    assert award is not None


def test_set_achievement_emits_event(user, achievement):
    mock_socketio = MagicMock()
    set_achievement(achievement.id, user.user_name, mock_socketio)

    mock_socketio.emit.assert_called_once()
    call_args = mock_socketio.emit.call_args
    assert call_args[0][0] == "achievement_unlocked"
    assert call_args[1]["room"] == f"user_{user.id}"


def test_set_achievement_duplicate_not_awarded(user, achievement):
    mock_socketio = MagicMock()
    set_achievement(achievement.id, user.user_name, mock_socketio)
    set_achievement(achievement.id, user.user_name, mock_socketio)

    awards = UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).all()
    assert len(awards) == 1
    assert mock_socketio.emit.call_count == 1


def test_set_achievement_unknown_achievement_id(user):
    mock_socketio = MagicMock()
    set_achievement(9999, user.user_name, mock_socketio)

    assert UserAchievement.query.filter_by(user_id=user.id).count() == 0
    mock_socketio.emit.assert_not_called()


def test_set_achievement_unknown_user(achievement):
    mock_socketio = MagicMock()
    # Should not raise — exception is caught internally
    set_achievement(achievement.id, "ghost_user", mock_socketio)
    assert UserAchievement.query.count() == 0


def test_mark_achievement_notified(user, achievement):
    mock_socketio = MagicMock()
    set_achievement(achievement.id, user.user_name, mock_socketio)

    award = UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first()
    assert award.is_notified is False

    mark_achievement_notified(award.id)
    db.session.refresh(award)
    assert award.is_notified is True


def test_mark_achievement_notified_nonexistent_id():
    # Should not raise
    mark_achievement_notified(99999)


def test_add_achievement_to_session_returns_tuple(user, achievement):
    result = add_achievement_to_session(achievement.id, user.user_name)
    db.session.commit()

    assert result is not None
    assert result[0] == user.id
    assert result[1] == achievement.title
    assert UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).count() == 1


def test_add_achievement_to_session_duplicate_returns_none(user, achievement):
    add_achievement_to_session(achievement.id, user.user_name)
    db.session.commit()
    result = add_achievement_to_session(achievement.id, user.user_name)
    assert result is None


def test_add_achievement_to_session_unknown_user(achievement):
    result = add_achievement_to_session(achievement.id, "ghost_user")
    assert result is None


def test_add_achievement_to_session_unknown_achievement(user):
    result = add_achievement_to_session(9999, user.user_name)
    assert result is None
