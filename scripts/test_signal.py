from app.utils.stocks import get_stock_info
from app.utils.signal import send_signal_message
from app.achievements import set_achievement
from app.models import StockPick, StockUpdate, User
from app import create_app, db, socketio
from config import Config

from datetime import datetime, timezone
import sys

app = create_app(config_class=Config)
if __name__ == "__main__":
    with app.app_context():
        user2 = User.query.all()
        sorted_user2 = sorted(user2, key=lambda g: g.total_investment, reverse=True)
        message = f'Please ignore, this is just a test message before finishing the predictions... Congrats, {sorted_user2[0].user_name}! You are now the best investor in this group with an investment of € {sorted_user2[0].total_investment}! Everyone else clearly sucks.'
        send_signal_message(Config.PHONE_NUMBER, Config.SIGNAL_GROUP, message)

