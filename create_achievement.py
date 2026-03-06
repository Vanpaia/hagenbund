from app import create_app, db
from config import Config

from app.models import Achievement

app = create_app(config_class=Config)

with app.app_context():
    slowest = Achievement(id=1, title="Slow as a snail!", description="You slow", logo="test_logo.png")
    fastest = Achievement(id=2, title="Fastest fingergun in the west", description="You fast", logo="test_logo.png")
    pessimist = Achievement(id=3, title="Glass half-empty", description="You pessimist", logo="test_logo.png")
    optimist = Achievement(id=4, title="Glass half-full", description="You optimist", logo="test_logo.png")
    beta = Achievement(title="Beta Tester", description="You helped creating this app by testing, you soy beta boy.", logo="labs")
    db.session.add(slowest)
    db.session.add(fastest)
    db.session.add(pessimist)
    db.session.add(optimist)
    db.session.add(beta)
    db.session.commit()
