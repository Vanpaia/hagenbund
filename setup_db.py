from app import create_app, db
from app.models import User, Achievement
from config import Config

app = create_app(config_class=Config)

ACHIEVEMENTS = [
    Achievement(id=1,  title="Slow as a snail!",                    description="Having difficulties making up your mind or is your brain not so fast?",                                                                            logo="achievement_slow.png"),
    Achievement(id=2,  title="Fastest fingergun in the west",        description="Those fingers must be smoking by now, careful!",                                                                                                    logo="achievement_fast.png"),
    Achievement(id=3,  title="Glass half-empty",                     description="In this world nothing ever happens, especially for pessimists.",                                                                                    logo="achievement_pessimist.png"),
    Achievement(id=4,  title="Glass half-full",                      description="For an optimist nothing is impossible. Well nothing SEEMS impossible.",                                                                             logo="achievement_optimist.png"),
    Achievement(id=5,  title="Warmonger",                            description="You make money of the suffering of others, but the money is oh so good!",                                                                          logo="achievement_warmonger.png"),
    Achievement(id=6,  title="Mag-7",                                description="You take the easy route, but to be the king you have to associate with royalty!",                                                                  logo="achievement_mag_7.png"),
    Achievement(id=7,  title="Support the Family!",                  description="You can do anything, but never go against the family. — Don Vito Corleone",                                                                        logo="achievement_fn.png"),
    Achievement(id=8,  title="Cutting it close!",                    description="You tell yourself that you want to take into account the latest info, but you are just lazy.",                                                     logo="achievement_late.png"),
    Achievement(id=9,  title="Yeah, duh!",                           description="You like to state the obvious. No points for you, bozo!",                                                                                          logo="achievement_duh.png"),
    Achievement(id=10, title="Zero hesitation",                      description="Your prediction speaks to the people. No explanation necessary!",                                                                                   logo="achievement_quick.png"),
    Achievement(id=11, title="Imma let you finish...",               description="Yo, I'm really happy for you, I'ma let you finish, but someone else had one of the best results of all time. You have an achievement taken away",  logo="achievement_kanye.png"),
    Achievement(id=12, title="First blood",                          description="You are the first to have closed a successful prediction.",                                                                                         logo="achievement_blood.png"),
    Achievement(id=13, title="This is Darksouls",                    description="You are expected to fail a prediction. We'll still laugh at you.",                                                                                 logo="achievement_darksouls.png"),
    Achievement(id=14, title="I TOLD YOU SO",                        description="You did tell us and we didn't believe. Look who is laughing now.",                                                                                  logo="achievement_cassandra.png"),
    Achievement(id=15, title="Double or Nothing",                    description="You doubled your investment. Finally you are at the end of the gambler's fallacy. Only this is virtual...",                                        logo="achievement_double.png"),
    Achievement(id=16, title="Et tu Brute...",                       description="You couldn't wait for them to fail their own prediction. You had to twist the knife in their back.",                                               logo="achievement_brutus.png"),
    Achievement(id=17, title="If you come at the king...",           description="... you best not miss. You, however, did miss in your schemes. Watch your back.",                                                                  logo="achievement_king.png"),
    Achievement(id=18, title="That's a Bingo!",                      description="Honestly, I did not think we would get there.. I have nothing prepared..",                                                                         logo="achievement_bingo.png"),
    Achievement(id=19, title="Warren Buffet",                        description="Financial genius is selling you short. And you know short selling.",                                                                               logo="achievement_buffet.png"),
    Achievement(id=20, title="Cramer Index",                         description="Just like Cramer we should learn to always invest in the opposite of what you propose.",                                                           logo="achievement_cramer.png"),
    Achievement(id=21, title="Pyrrhic Victory",                      description="You took hits too, but you are first and that's what matters.",                                                                                    logo="achievement_beaten.png"),
    Achievement(id=22, title="Perfectly Balanced",                   description="Do you enjoy the chaos or is it you that brings order? Whatever the case, you own the most performant and the least perfomant stock. Perfectly balanced, as all things should be.", logo="achievement_balanced.png"),
]

USERS = [
    {"user_name": "Test",  "email": "test@test.com",  "password": "123", "is_admin": False},
    {"user_name": "Test2", "email": "test2@test.com", "password": "123", "is_admin": False},
    {"user_name": "Admin", "email": "admin@test.com", "password": "123", "is_admin": True},
]

with app.app_context():
    db.create_all()

    existing_achievements = {a.id for a in Achievement.query.all()}
    for achievement in ACHIEVEMENTS:
        if achievement.id not in existing_achievements:
            db.session.add(achievement)

    existing_users = {u.user_name for u in User.query.all()}
    for u in USERS:
        if u["user_name"] not in existing_users:
            user = User(user_name=u["user_name"], email=u["email"], is_admin=u["is_admin"])
            user.set_password(u["password"])
            db.session.add(user)

    db.session.commit()
    print("Setup complete.")
