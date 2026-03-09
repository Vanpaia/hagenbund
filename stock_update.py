from app.utils.stocks import get_stock_info
from app.models import StockPick, StockUpdate, User
from app import create_app, db
from config import Config

from datetime import datetime, timezone

app = create_app(config_class=Config)
if __name__ == "__main__":
    with app.app_context():
        stockpicks = StockPick.query.all()

        for stock in stockpicks:
            try:
                stock_info = get_stock_info(stock.symbol)
                print(stock.initial_price, stock_info[0]["price"])

                stock.name=stock_info[0]["companyName"],
                stock.currency=stock_info[0]["currency"],
                stock.country=stock_info[0]["country"],
                stock.ceo=stock_info[0]["ceo"],
                stock.exchange_full_name=stock_info[0]["exchangeFullName"],
                stock.exchange=stock_info[0]["exchange"],
                stock.sector=stock_info[0]["sector"],
                stock.industry=stock_info[0]["industry"],
                stock.employees=stock_info[0]["fullTimeEmployees"],
                stock.description=stock_info[0]["description"],
                stock.website=stock_info[0]["website"],
                stock.image=stock_info[0]["image"],
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
    with app.app_context():
        stockpicks = StockPick.query.all()

        for stock in stockpicks:
            try:
                stock_info = get_stock_info(stock.symbol)
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
                stock.initial_price=stock_info[0]["price"]
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
