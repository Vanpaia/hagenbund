from app import create_app, db
from app.models import StockPick, StockUpdate
from datetime import datetime, date
from config import Config


app = create_app(config_class=Config)

with app.app_context():
    # 1. Define the target date (March 8th, 2026)
    target_date = date(2026, 3, 8)

    # 2. Get all stock picks that need fixing
    picks = StockPick.query.all()

    for pick in picks:
        # 3. Find the update for THIS specific pick on THAT specific date
        # We filter by the pick's symbol and the date of created_at
        original_update = StockUpdate.query.filter(
            StockUpdate.stock_id == pick.id,
            db.func.date(StockUpdate.created_at) == target_date
        ).first()

        if original_update:
            print(original_update.created_at)
            # 4. Restore the initial_price from the update's price
            # (Assuming your StockUpdate model has a 'price' or 'close' column)
            pick.initial_price = original_update.price
            print(f"Restored {pick.symbol}: {pick.initial_price} should be {original_update.price}")
        else:
            print(f"Warning: No update found for {pick.symbol} on {target_date}")

    # 5. Save the corrections to the database
    db.session.commit()
    print("Repair complete.")
