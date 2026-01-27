from app import create_app, db
from config import Config

from app.models import User

app = create_app(config_class=Config)

with app.app_context():
    test=User(user_name="Test2", email="test@test.com", password_hash="")
    db.session.add(test)
    test.set_password("123")
    db.session.commit()
