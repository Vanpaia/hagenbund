from app import db
from ... import socketio
from app.models import User, StockPick, StockUpdate
from app.achievements import set_achievement


def create_stockpick(stock_info: dict, user: User, stock_symbol: str) -> StockPick:

    pick = StockPick(
        user_id=user.id,
        symbol=stock_symbol,
        name=stock_info[0]["companyName"],
        currency=stock_info[0]["currency"],
        country=stock_info[0]["country"],
        ceo=stock_info[0]["ceo"],
        exchange_full_name=stock_info[0]["exchangeFullName"],
        exchange=stock_info[0]["exchange"],
        sector=stock_info[0]["sector"],
        industry=stock_info[0]["industry"],
        employees=stock_info[0]["fullTimeEmployees"],
        description=stock_info[0]["description"],
        website=stock_info[0]["website"],
        image=stock_info[0]["image"],
        initial_price=stock_info[0]["price"],
        current_price=stock_info[0]["price"]
    )
    db.session.add(pick)
    db.session.flush()
    update = StockUpdate(
        stock_id=pick.id,
        price=stock_info[0]["price"],
        change=stock_info[0]["change"],
        change_percentage=stock_info[0]["changePercentage"],
        beta=stock_info[0]["beta"],
        market_cap=stock_info[0]["marketCap"],
        volume=stock_info[0]["volume"],
        average_volume=stock_info[0]["averageVolume"]
    )
    db.session.add(update)
    db.session.commit()

    # Set achievements if necessary
    mag_7 = ['Alphabet Inc.', 'Microsoft Corporation', 'Apple Inc.', 'Amazon.com, Inc.', 'Meta Platforms, Inc.', 'NVIDIA Corporation', 'Tesla, Inc.']
    if pick.industry == "Aerospace & Defense":
        set_achievement(5, user.user_name, socketio)
    elif pick.name == 'FiscalNote Holdings, Inc.':
        set_achievement(7, user.user_name, socketio)
    elif pick.name in mag_7:
        set_achievement(6, user.user_name, socketio)

    return pick

def fetch_stockpicks(user: User) -> list:
    """Fetch stockpicks"""

    picks = StockPick.query.filter_by(user_id=user.id).all()
    data = []
    for x in picks:
        data.append(x.to_dict())

    return data

def delete_stockpick(stock_id: int) -> StockPick:
    """Delete a prediction"""
    pick = StockPick.query.get_or_404(stock_id)
    db.session.delete(pick)
    db.session.commit()
    
    return pick
