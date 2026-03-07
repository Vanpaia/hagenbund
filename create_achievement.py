from app import create_app, db
from config import Config

from app.models import Achievement

app = create_app(config_class=Config)

with app.app_context():
    slowest = Achievement(id=1, title="Slow as a snail!", description="Having difficulties making up your mind or is your brain not so fast?", logo="achievement_slow.png")
    fastest = Achievement(id=2, title="Fastest fingergun in the west", description="Those fingers must be smoking by now, careful!", logo="achievement_fast.png")
    pessimist = Achievement(id=3, title="Glass half-empty", description="In this world nothing ever happens, especially for pessimists.", logo="achievement_pessimist.png")
    optimist = Achievement(id=4, title="Glass half-full", description="For an optimist nothing is impossible. Well nothing SEEMS impossible.", logo="achievement_optimist.png")
    warmonger = Achievement(id=5, title="Warmonger", description="You make money of the suffering of others, but the money is oh so good!", logo="achievement_warmonger.png")
    mag_7 = Achievement(id=6, title="Mag-7", description="You take the easy route, but to be the king you have to associate with royalty!", logo="achievement_mag_7.png")
    fn = Achievement(id=7, title="Support the Family!", description="You can do anything, but never go against the family. — Don Vito Corleone", logo="achievement_fn.png")
    late = Achievement(id=8, title="Cutting it close!", description="You tell yourself that you want to take into account the latest info, but you are just lazy.", logo="achievement_late.png")
    high_round = Achievement(id=9, title="Yeah, duh!", description="You like to state the obvious. No points for you, bozo!", logo="achievement_duh.png")
    fast_round = Achievement(id=10, title="Zero hesitation", description="Your prediction speaks to the people. No explanation necessary!", logo="achievement_quick.png")
    db.session.add(slowest)
    db.session.add(fastest)
    db.session.add(pessimist)
    db.session.add(optimist)
    db.session.add(warmonger)
    db.session.add(mag_7)
    db.session.add(fn)
    db.session.add(late)
    db.session.commit()
