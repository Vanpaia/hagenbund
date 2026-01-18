from app import create_app, db
from config import Config

from app.models import Achievement

app = create_app(config_class=Config)

with app.app_context():
    test_achievement = Achievement(title="Test Achievement", description="This is the description of what you did to get the achievement", logo="test_logo.png")
    db.session.add(test_achievement)
    db.session.commit()
