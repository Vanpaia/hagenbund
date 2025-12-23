from app import create_app, db
from config import Config

from app.models import User

app = create_app(config_class=Config)

with app.app_context():

    u = User.query.filter_by(user_name="Test").first()
    print(u)
    u.set_password("123")
    db.session.commit()
