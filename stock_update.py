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
        old_ranking = {}
        user1 = User.query.all()
        sorted_user1 = sorted(user1, key=lambda g: g.total_investment, reverse=True)

        for i, gentleboy in enumerate(user1, 1):
            old_ranking[gentleboy.user_name] = {"name": gentleboy.user_name, "rank": i, "total": gentleboy.total_investment, "stocks":{}}
            for stock in gentleboy.stockpicks:
                old_ranking[gentleboy.user_name]["stocks"][stock.symbol] = stock.current_price



        stockpicks = StockPick.query.all()

        for stock in stockpicks:
            try:
                stock_info = get_stock_info(stock.symbol)
                if not stock_info:
                    db.session.rollback()
                    print("Failed API calls")
                    sys.exit()

                print(stock.initial_price, stock_info[0]["price"])
                stock.name=stock_info[0]["companyName"]
                stock.currency=stock_info[0]["currency"]
                stock.country=stock_info[0]["country"]
                stock.ceo=stock_info[0]["ceo"]
                stock.exchange_full_name=stock_info[0]["exchangeFullName"]
                stock.exchange=stock_info[0]["exchange"]
                stock.sector=stock_info[0]["sector"]
                stock.industry=stock_info[0]["industry"]
                stock.employees=stock_info[0]["fullTimeEmployees"]
                stock.description=stock_info[0]["description"]
                stock.website=stock_info[0]["website"]
                stock.image=stock_info[0]["image"]
                stock.current_price=stock_info[0]["price"]

                update = StockUpdate(
                    stock_id=stock.id,
                    price=stock_info[0]["price"],
                    change=stock_info[0]["change"],
                    change_percentage=stock_info[0]["changePercentage"],
                    beta=stock_info[0]["beta"],
                    market_cap=stock_info[0]["marketCap"],
                    volume=stock_info[0]["volume"],
                    average_volume=stock_info[0]["averageVolume"]
                )
                db.session.add(update)

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        user2 = User.query.all()
        sorted_user2 = sorted(user2, key=lambda g: g.total_investment, reverse=True)
        for i, gentleboy in enumerate(sorted_user2, 1):
            all_up = True
            all_down = True
            if gentleboy.total_investment >= 10000:
                set_achievement(15, gentleboy.user_name, socketio)

            for stock in gentleboy.stockpicks:
                if stock.current_price > old_ranking[gentleboy.user_name]["stocks"][stock.symbol]:
                    all_down = False
                elif stock.current_price < old_ranking[gentleboy.user_name]["stocks"][stock.symbol]:
                    all_up = False
                else:
                    all_up = False
                    all_down = False

            if all_up and (i == 1):
                set_achievement(19, gentleboy.user_name, socketio)

            if all_down and (i == len(sorted_user2)):
                set_achievement(20, gentleboy.user_name, socketio)


            if (i == 1) and (old_ranking[gentleboy.user_name]["rank"] != 1) and (gentleboy.total_investment < old_ranking[gentleboy.user_name]["total"]):
                set_achievement(21, gentleboy.user_name, socketio)
        
        if sorted_user1[0].user_name != sorted_user2[0].user_name:
            message = f'Congrats {sorted_user2[0].user_name} you have dethroned {sorted_user1[0].user_name} and are now the best investor in this group with an investment of € {sorted_user2[0].total_investment}! Go make fun of all the poor people in this group.'
            send_signal_message(Config.PHONE_NUMBER, Config.SIGNAL_GROUP, message)


        best_stock = StockPick.highest_return()
        worst_stock = StockPick.lowest_return()

        if best_stock.user_id == worst_stock.user_id:
            set_achievement(22, best_stock.user.user_name, socketio)

