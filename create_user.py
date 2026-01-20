from app import create_app, db
from config import Config

from app.models import User

app = create_app(config_class=Config)

with app.app_context():
    test=User(user_name="Test", email="test@test.com", password_hash="")
    db.session.add(test)
    admin=User(user_name="Admin", email="admin@test.com", password_hash="", is_admin=True)
    db.session.add(admin)
    mike=User(user_name="Mike", email="mikelittlehale@pm.me", password_hash="")
    db.session.add(mike)
    vlad=User(user_name="Vlad", email="vita.vlad.florin@gmail.com", password_hash="")
    db.session.add(vlad)
    tom=User(user_name="Tom", email="thomas.adlam92@gmail.com", password_hash="")
    db.session.add(tom)
    klaas=User(user_name="Klaas", email="klaas.portier@gmail.com", password_hash="")
    db.session.add(klaas)
    hagen=User(user_name="Hagen", email="h.schlotzhauer@gmail.com", password_hash="")
    db.session.add(hagen)
    danilo=User(user_name="Danilo", email="gattullo@insuranceeurope.eu", password_hash="")
    db.session.add(danilo)
    db.session.commit()

    test.set_password("123")
    admin.set_password("123")
    mike.set_password("Zinne Bir")
    vlad.set_password("Geuze Boon")
    tom.set_password("Tripel Karmeliet")
    klaas.set_password("Brugse Zot")
    hagen.set_password("Taras Boulba")
    danilo.set_password("Leffe Blond")
    db.session.commit()
