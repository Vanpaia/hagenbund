from app import db, login
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.functions import coalesce
from sqlalchemy import func, select
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

class PredictionStatus(Enum):
    PENDING = "pending"
    VOTING = "voting"
    SUCCESS = "success"
    FAILED = "failed"

    def sentence(self):
        return {
            PredictionStatus.SUCCESS: "came true",
            PredictionStatus.FAILED: "did not come true",
        }[self]

class ConclusionOutcome(Enum):
    SUCCESS = "success"
    FAILED = "failed"

    def sentence(self):
        return {
            ConclusionOutcome.SUCCESS: "successful",
            ConclusionOutcome.FAILED: "failed",
        }[self]

class ConclusionStatus(Enum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64))
    email = db.Column(db.String(256))
    password_hash = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)

    achievements = db.relationship("UserAchievement", back_populates="user")
    stockpicks = db.relationship("StockPick", back_populates="user")
    predictions = db.relationship("Prediction", back_populates="author")

    @hybrid_property
    def total_investment(self) -> int:
        return round(sum(1000/p.initial_price*p.current_price for p in self.stockpicks), 2)

    @total_investment.inplace.expression
    @classmethod
    def _total_investment_expression(cls):
        return (
            select(func.sum((1000 / StockPick.initial_price) * StockPick.current_price))
            .where(StockPick.user_id == cls.id)
            .label("total_portfolio_value")
        )

    @hybrid_property
    def total_prediction_points(self) -> int:
        return sum((p.points or 0) * (p.multiplier or 1) for p in self.predictions if (p.status == PredictionStatus.PENDING or p.status == PredictionStatus.VOTING))

    @total_prediction_points.inplace.expression
    @classmethod
    def _total_prediction_points_expression(cls):
        return (
            select(func.sum(Prediction.points * Prediction.multiplier))
            .where(Prediction.user_id == cls.id)
            .label("total_prediction_points")
        )

    @hybrid_property
    def total_achieved_points(self) -> int:
        # Python logic
        return sum((p.points or 0) * (p.multiplier or 1) for p in self.predictions if p.status == PredictionStatus.SUCCESS)

    @total_achieved_points.inplace.expression
    @classmethod
    def _total_achieved_points_expression(cls):
        # SQL logic
        return (
            select(func.sum(coalesce(Prediction.points, 0) * coalesce(Prediction.multiplier, 1)))
            .where(Prediction.user_id == cls.id)
            .where(Prediction.status == PredictionStatus.SUCCESS)
            .correlate(cls)
            .label("total_achieved_points")
        )

    @hybrid_property
    def total_failed_points(self) -> int:
        # Python logic
        return sum((p.points or 0) * (p.multiplier or 1) for p in self.predictions if p.status == PredictionStatus.FAILED)

    @total_achieved_points.inplace.expression
    @classmethod
    def _total_failed_points_expression(cls):
        # SQL logic
        return (
            select(func.sum(coalesce(Prediction.points, 0) * coalesce(Prediction.multiplier, 1)))
            .where(Prediction.user_id == cls.id)
            .where(Prediction.status == PredictionStatus.FAILED)
            .correlate(cls)
            .label("total_achieved_points")
        )

    @hybrid_property
    def total_outstanding_points(self) -> int:
        # Python logic
        return sum((p.points or 0) * (p.multiplier or 1) for p in self.predictions if p.status in (PredictionStatus.PENDING, PredictionStatus.VOTING))

    @total_achieved_points.inplace.expression
    @classmethod
    def _total_outstanding_points_expression(cls):
        # SQL logic
        return (
            select(func.sum(coalesce(Prediction.points, 0) * coalesce(Prediction.multiplier, 1)))
            .where(Prediction.user_id == cls.id)
            .where(Prediction.status.in_([PredictionStatus.PENDING, PredictionStatus.VOTING]))
            .correlate(cls)
            .label("total_achieved_points")
        )

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

class Prediction(db.Model):
    __tablename__ = "prediction"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    uuid_key = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.Enum(Category), nullable=False)
    created_at = db.Column(db.Date, default= lambda: datetime.now(timezone.utc))
    status = db.Column(db.Enum(PredictionStatus), default=PredictionStatus.PENDING)
    position = db.Column(db.Integer)

    points = db.Column(db.Integer, nullable=True)
    multiplier = db.Column(db.Integer, default=1)
    likelihood = db.Column(db.Float, nullable=True)

    author = db.relationship("User", back_populates="predictions")
    conclusions = db.relationship("PredictionConclusion", back_populates="prediction")
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'position', name='uq_user_category_position'),
    )

    def to_dict(self):
        formatted_date = self.created_at.isoformat() if self.created_at else None
        content = {"title": self.title,
                   "uuid": self.uuid_key,
                   "id": self.id,
                   "description": self.description,
                   "category": self.category.value,
                   "user_id": self.user_id,
                   "author": self.author.user_name,
                   "created_at": formatted_date}
        return content

class PredictionVote(db.Model):
    __tablename__ = "prediction_vote"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey("prediction.id"), nullable=False)
    vote = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Float, nullable=False)

    __table_args__ = (
            db.UniqueConstraint('user_id', 'prediction_id', name='_user_prediction_uc'),
        )

class PredictionConclusionVote(db.Model):
    __tablename__ = "prediction_conclusion_vote"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    prediction_conclusion_id = db.Column(db.Integer, db.ForeignKey("prediction_conclusion.id"), nullable=False)
    vote = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))

    conclusion = db.relationship("PredictionConclusion", back_populates="votes")

    __table_args__ = (
            db.UniqueConstraint('user_id', 'prediction_conclusion_id', name='_user_prediction_conclusion_uc'),
        )

class PredictionConclusion(db.Model):
    __tablename__ = "prediction_conclusion"
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("prediction.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Enum(ConclusionOutcome))
    status = db.Column(db.Enum(ConclusionStatus), nullable=False, default=ConclusionStatus.ACTIVE)

    votes = db.relationship("PredictionConclusionVote", back_populates="conclusion")
    prediction = db.relationship("Prediction", back_populates="conclusions")

    def to_dict(self):
        formatted_date = self.created_at.isoformat() if self.created_at else None
        content = {"id": self.id,
                   "description": self.description,
                   "url": self.url,
                   "user_id": self.user_id,
                   "outcome": self.outcome.value,
                   "status": self.status.value,
                   "created_at": formatted_date}
        return content

    @hybrid_property
    def total_in_favour(self) -> int:
        return sum(1 for v in self.votes if v.vote is True)

    @hybrid_property
    def total_against(self) -> int:
        return sum(1 for v in self.votes if v.vote is False)

    def get_user_vote(self, user_id) -> PredictionConclusionVote | None:
        return PredictionConclusionVote.query.filter_by(
            prediction_conclusion_id=self.id, user_id=user_id
        ).first()

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

    user = db.relationship("User", back_populates="stockpicks")

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

    @classmethod
    def highest_return(cls):
        return db.session.query(cls).order_by((((cls.current_price / cls.initial_price) - 1) * 100).desc()).first()

    @classmethod
    def lowest_return(cls):
        return db.session.query(cls).order_by((((cls.current_price / cls.initial_price) - 1) * 100).asc()).first()

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

    @property
    def formatted_date(self):
        return self.created_at.strftime('%a %d %b %Y, %I:%M%p')


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
