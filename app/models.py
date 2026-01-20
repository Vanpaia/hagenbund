from app import db, login
from flask_login import UserMixin
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from enum import Enum
import uuid

class Category(Enum):
    POL = "World Politics"
    EUR = "European Union"
    ENT = "Entertainment/Sport"
    SCI = "Science/Technology"
    ECO = "Economy/Business"


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64))
    email = db.Column(db.String(256))
    password_hash = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)

    achievements = db.relationship("UserAchievement", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Achievement(db.Model):
    __tablename__ = "achievement"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    logo = db.Column(db.String(64), nullable=True)

    users = db.relationship("UserAchievement", back_populates="achievement")

class UserAchievement(db.Model):
    __tablename__ = 'user_achievement'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='_user_achievement_uc'),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_notified = db.Column(db.Boolean, default=False)

    # Relationships to make querying easier
    user = db.relationship("User", back_populates="achievements")
    achievement = db.relationship("Achievement", back_populates="users")

user_achievements = db.Table('user_achievements', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),  
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievement.id'), primary_key=True),
    db.Column('created_at', db.Date, default= lambda: datetime.now(timezone.utc))
)

class Prediction(db.Model):
    __tablename__ = "prediction"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    uuid_key = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.Enum(Category), nullable=False)
    created_at = db.Column(db.Date, default= lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        formatted_date = self.created_at.isoformat() if self.created_at else None
        content = {"title": self.title,
                   "uuid": self.uuid_key,
                   "description": self.description,
                   "category": self.category.value,
                   "user_id": self.user_id,
                   "created_at": formatted_date}
        return content

class StockPick(db.Model):
    __tablename__ = "stockpick"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True, nullable=False)
    symbol = db.Column(db.String(12), index=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    currency = db.Column(db.String(12), nullable=False)
    country = db.Column(db.String(12), nullable=False)
    ceo = db.Column(db.String(64), nullable=False)
    exchange_full_name = db.Column(db.String(128), nullable=False)
    exchange = db.Column(db.String(12), nullable=False)
    sector = db.Column(db.String(64), nullable=False)
    industry = db.Column(db.String(128), nullable=False)
    employees = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(128), nullable=False)
    image = db.Column(db.String(128), nullable=False)
    last_checked = db.Column(db.Date, default= lambda: datetime.now(timezone.utc))
    initial_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)

    __table_args__ = (
            db.UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),
        )

    def to_dict(self):
        content = {"name": self.name,
         "symbol": self.symbol,
         "description": self.description,
         "sector": self.sector,
         "industry": self.industry,
         "price": self.current_price,
         "last_checked": self.last_checked}
        return content

    @property
    def total_return(self):
        return ((self.current_price - self.initial_price) / self.initial_price) * 100

class StockUpdate(db.Model):
    __tablename__ = "stockupdate"
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey("stockpick.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float, nullable=False)
    change_percentage = db.Column(db.Float, nullable=False)
    beta = db.Column(db.Float, nullable=False)
    market_cap = db.Column(db.BigInteger, nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    average_volume = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
