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
    bets = db.relationship("Bet", back_populates="author")
    debit_entries = db.relationship(
        "BeerLedger", 
        foreign_keys="[BeerLedger.debtor_id]", 
        back_populates="debtor"
    )
    credit_entries = db.relationship(
        "BeerLedger", 
        foreign_keys="[BeerLedger.creditor_id]", 
        back_populates="creditor"
    )
    @hybrid_property
    def total_beer_debit(self) -> float:
        return sum(p.amount for p in self.debit_entries)

    @total_beer_debit.expression
    def total_beer_debit(cls):
        return (
            select(func.coalesce(func.sum(BeerLedger.amount), 0))
            .where(BeerLedger.debtor_id == cls.id)
            .label("total_debit")
        )

    @hybrid_property
    def total_beer_credit(self) -> float:
        return sum(p.amount for p in self.credit_entries)

    @total_beer_credit.expression
    def total_beer_credit(cls):
        return (
            select(func.coalesce(func.sum(BeerLedger.amount), 0))
            .where(BeerLedger.creditor_id == cls.id)
            .label("total_credit")
        )

    @hybrid_property
    def total_beer_balance(self) -> float:
        return self.total_beer_credit - self.total_beer_debit

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

class BetVote(db.Model):
    __tablename__ = "bet_vote"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    bet_id = db.Column(db.Integer, db.ForeignKey("bet.id"), nullable=False)
    vote = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))

    bet = db.relationship("Bet", back_populates="votes")

class Bet(db.Model):
    __tablename__ = "bet"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))
    vote_until = db.Column(db.DateTime)
    status = db.Column(db.Enum(PredictionStatus), default=PredictionStatus.PENDING)

    author = db.relationship("User", back_populates="bets")
    conclusions = db.relationship("BetConclusion", back_populates="bet", cascade="all, delete-orphan")
    votes = db.relationship("BetVote", back_populates="bet", cascade="all, delete-orphan")
    settlement = db.relationship("BeerLedger", back_populates="bet", cascade="all, delete-orphan")

    def to_dict(self):
        formatted_date = self.created_at.isoformat() if self.created_at else None
        formatted_open_date = self.vote_until.isoformat() if self.vote_until else None
        content = {"title": self.title,
                   "id": self.id,
                   "description": self.description,
                   "user_id": self.user_id,
                   "author": self.author.user_name,
                   "created_at": formatted_date,
                   "vote_until": formatted_open_date}
        return content

    @hybrid_property
    def total_votes(self) -> int:
        return len(self.votes)

    @total_votes.expression
    def total_votes(cls):
        return (
            select(func.count(BetVote.id))
            .where(BetVote.bet_id == cls.id)
            .label("total_votes")
        )

    @hybrid_property
    def total_in_favour(self) -> int:
        return sum(1 for v in self.votes if v.vote is True)

    @total_in_favour.expression
    def total_in_favour(cls):
        return (
            select(func.coalesce(func.sum(cast(BetVote.vote, Integer)), 0))
            .where(BetVote.bet_id == cls.id)
            .label("total_favour")
        )

    @hybrid_property
    def total_against(self) -> int:
        return (self.total_votes - self.total_in_favour)

    @hybrid_property
    def odds_favour(self) -> float:
        if self.total_against == 0:
            return float(self.total_in_favour)
        return round(self.total_in_favour / self.total_against, 2)

    @hybrid_property
    def odds_against(self) -> float:
        if self.total_in_favour == 0:
            return float(self.total_against)
        return round(self.total_against / self.total_in_favour, 2)

    @hybrid_property
    def odds_favour(self) -> int:
        return (self.total_in_favour / self.total_against)

    @hybrid_property
    def odds_against(self) -> int:
        return (self.total_against / self.total_in_favour)

    def get_user_vote(self, user_id) -> BetVote | None:
        return BetVote.query.filter_by(
            bet_id=self.id, user_id=user_id
        ).first()

class BetConclusionVote(db.Model):
    __tablename__ = "bet_conclusion_vote"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    bet_conclusion_id = db.Column(db.Integer, db.ForeignKey("bet_conclusion.id"), nullable=False)
    vote = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))

    conclusion = db.relationship("BetConclusion", back_populates="votes")

    __table_args__ = (
            db.UniqueConstraint('user_id', 'bet_conclusion_id', name='_user_bet_conclusion_uc'),
        )

class BetConclusion(db.Model):
    __tablename__ = "bet_conclusion"
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey("bet.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Enum(ConclusionOutcome))
    status = db.Column(db.Enum(ConclusionStatus), nullable=False, default=ConclusionStatus.ACTIVE)

    votes = db.relationship("BetConclusionVote", back_populates="conclusion", cascade="all, delete-orphan")
    bet = db.relationship("Bet", back_populates="conclusions")

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

    def get_user_vote(self, user_id) -> BetConclusionVote | None:
        return BetConclusionVote.query.filter_by(
            bet_conclusion_id=self.id, user_id=user_id
        ).first()

class BeerLedger(db.Model):
    __tablename__ = "beer_ledger"
    id = db.Column(db.Integer, primary_key=True)
    debtor_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_beer_ledger_debtor"), nullable=False)
    creditor_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_beer_ledger_creditor"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    bet_id = db.Column(db.Integer, db.ForeignKey("bet.id"), nullable=True)
    reason = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bet = db.relationship("Bet", back_populates="settlement")
    debtor = db.relationship(
        "User", 
        foreign_keys=[debtor_id], 
        back_populates="debit_entries"
    )
    creditor = db.relationship(
        "User", 
        foreign_keys=[creditor_id], 
        back_populates="credit_entries"
    )

    def to_dict(self):
        formatted_date = self.created_at.isoformat() if self.created_at else None
        content = {"amount": self.amount,
                   "id": self.id,
                   "bet": self.bet_id,
                   "reason": self.reason,
                   "debitor": self.debtor.user_name,
                   "creditor": self.creditor.user_name,
                   "created_at": formatted_date}
        return content

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
