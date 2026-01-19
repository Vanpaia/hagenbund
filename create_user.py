from app import create_app, db
from config import Config

from app.models import User

app = create_app(config_class=Config)

with app.app_context():
    test=User(user_name="Test", email="test@test.com", password_hash="")
    db.session.add(test)
    admin=User(user_name="Admin", email="admin@test.com", password_hash="", is_admin=True)
    db.session.add(admin)
    test.set_password("123")
    admin.set_password("123")
    db.session.commit()
