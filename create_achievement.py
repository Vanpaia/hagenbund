from app import create_app, db
from config import Config

from app.models import Achievement

app = create_app(config_class=Config)

with app.app_context():
    slowest = Achievement(id=1, title="Slow as a snail!", description="Having difficulties making up your mind or is your brain not so fast?", logo="achievement_slow.png")
    fastest = Achievement(id=2, title="Fastest fingergun in the west", description="Those fingers must be smoking by now, careful!", logo="achievement_fast.png")
    pessimist = Achievement(id=3, title="Glass half-empty", description="In this world nothing ever happens, especially for pessimists.", logo="achievement_pessimist.png")
    optimist = Achievement(id=4, title="Glass half-full", description="For an optimist nothing is impossible. Well nothing SEEMS impossible.", logo="achievement_optimist.png")
    db.session.add(slowest)
    db.session.add(fastest)
    db.session.add(pessimist)
    db.session.add(optimist)
    db.session.commit()
