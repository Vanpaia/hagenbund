from app import create_app, db
from config import Config

from app.models import User

app = create_app(config_class=Config)

with app.app_context():
    users = User.query.all()

    for user in users:
        print(user.id, user.user_name)
        for achievement in user.achievements:
            print(achievement.achievement_id, achievement.achievement.title)

    """
    test=User(user_name="Test", email="test@test.com", password_hash="")
    test2=User(user_name="Test2", email="test@test.com", password_hash="")
    admin=User(user_name="Admin", email="admin@test.com", password_hash="", is_admin=True)
    db.session.add(test)
    db.session.add(test2)
    db.session.add(admin)
    test.set_password("123")
    test2.set_password("123")
    admin.set_password("123")
    db.session.commit()
    """
