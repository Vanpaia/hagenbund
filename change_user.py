import uuid
from app import create_app, db
from app.models import Prediction, User

app = create_app()

with app.app_context():

    all_user = User.query.all()

    for x in all_user:
        print(x.user_name)
    """
    # Find all predictions where uuid_key is missing
    empty_predictions = Prediction.query.filter(Prediction.uuid_key == None).all()
    
    print(f"Found {len(empty_predictions)} predictions needing UUIDs...")
    
    for p in empty_predictions:
        p.uuid_key = str(uuid.uuid4())
    
    db.session.commit()
    print("Backfill complete.")
        """
