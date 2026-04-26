from app.models import Bet
from datetime import datetime, timezone
from app import create_app, db
from config import Config


app = create_app(config_class=Config)

with app.app_context():
    # Find all bets and re-save them to force the new format
    for bet in Bet.query.all():
        if bet.vote_until:
            # If it's a date object, SQLAlchemy will now save it as DateTime
            db.session.add(bet) 

    db.session.commit()
