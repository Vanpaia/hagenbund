from app.utils.stocks import get_stock_info
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

        print(sorted_user1)
        print(old_ranking)

        danilo_picks = StockPick.query.filter_by(user_id=7).all()
        hagen_picks = StockPick.query.filter_by(user_id=6).all()
        klaas_picks = StockPick.query.filter_by(user_id=5).all()
        mike_picks = StockPick.query.filter_by(user_id=4).all()
        tom_picks = StockPick.query.filter_by(user_id=3).all()
        vlad_picks = StockPick.query.filter_by(user_id=2).all()

        for stock in danilo_picks:
            try:
                stock.current_price /= 1.5

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in mike_picks:
            try:
                stock.current_price /= 2

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in tom_picks:
            try:
                stock.current_price /= 2

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in tom_picks:
            try:
                stock.current_price /= 2

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in klaas_picks:
            try:
                stock.current_price /= 5

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in vlad_picks:
            try:
                stock.current_price *= 2

            except:
                print("Failed adding update, rolling back")
                db.session.rollback()
        try:
            db.session.commit()
        except:
            print("Failed final commit, rolling back")
            db.session.rollback()

        for stock in hagen_picks:
            try:
                stock.current_price /= 2

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
        print(sorted_user2)
        for i, gentleboy in enumerate(sorted_user2, 1):
            print(gentleboy.user_name, gentleboy.total_investment)
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
            print(message)
