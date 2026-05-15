import sys
from pathlib import Path

# Get the path to 'my_project' (one level up from this script)
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from app import create_app, db
from config import Config

from app.models import Prediction, User, Achievement, StockPick, StockUpdate, PredictionStatus

app = create_app(config_class=Config)
phone_nos = [
    {"no": "+32456077894", "name": "Hagen"},
    {"no": "+32487025450", "name": "Danilo"},
    {"no": "+32474635830", "name": "Klaas"},
    {"no": "+32466210339", "name": "Mike"},
    {"no": "+393479870436", "name": "Vlad"},
    {"no": "+32468095376", "name": "Tom"}]

with app.app_context():

    for number in phone_nos:
        user = User.query.filter_by(user_name=number["name"]).first()
        user.phone_no = number["no"]
    db.session.commit()


