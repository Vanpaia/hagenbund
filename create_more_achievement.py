from app import create_app, db
from config import Config

from app.models import Achievement

app = create_app(config_class=Config)

with app.app_context():
    kanye = Achievement(id=11, title="Imma let you finish...", description="Yo, I'm really happy for you, I'ma let you finish, but someone else had one of the best results of all time. You have an achievement taken away", logo="achievement_kanye.png")
    blood = Achievement(id=12, title="First blood", description="You are the first to have closed a successful prediction.", logo="achievement_blood.png")
    darksouls = Achievement(id=13, title="This is Darksouls", description="You are expected to fail a prediction. We'll still laugh at you.", logo="achievement_darksouls.png")
    cassandra = Achievement(id=14, title="I TOLD YOU SO", description="You did tell us and we didn't believe. Look who is laughing now.", logo="achievement_cassandra.png")
    double = Achievement(id=15, title="Double or Nothing", description="You doubled your investment. Finally you are at the end of the gambler's fallacy. Only this is virtual...", logo="achievement_double.png")
    brutus = Achievement(id=16, title="Et tu Brute...", description="You couldn't wait for them to fail their own prediction. You had to twist the knife in their back.", logo="achievement_brutus.png")
    king = Achievement(id=17, title="If you come at the king...", description="... you best not miss. You, however, did miss in your schemes. Watch your back.", logo="achievement_king.png")
    bingo = Achievement(id=18, title="That's a Bingo!", description="Honestly, I did not think we would get there.. I have nothing prepared..", logo="achievement_bingo.png")
    buffet = Achievement(id=19, title="Warren Buffet", description="Financial genius is selling you short. And you know short selling.", logo="achievement_buffet.png")
    cramer = Achievement(id=20, title="Cramer Index", description="Just like Cramer we should learn to always invest in the opposite of what you propose.", logo="achievement_cramer.png")
    beaten = Achievement(id=21, title="Pyrrhic Victory", description="You took hits too, but you are first and that's what matters.", logo="achievement_beaten.png")
    balanced = Achievement(id=22, title="Perfectly Balanced", description="Do you enjoy the chaos or is it you that brings order? Whatever the case, you own the most performant and the least perfomant stock. Perfectly balanced, as all things should be.", logo="achievement_balanced.png")
    db.session.add(kanye)
    db.session.add(blood)
    db.session.add(darksouls)
    db.session.add(cassandra)
    db.session.add(double)
    db.session.add(brutus)
    db.session.add(king)
    db.session.add(bingo)
    db.session.add(buffet)
    db.session.add(beaten)
    db.session.add(cramer)
    db.session.add(balanced)
    db.session.commit()
