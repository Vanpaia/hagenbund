from app import db, login
from flask_login import UserMixin
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from enum import Enum

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Prediction(UserMixin, db.Model):
    __tablename__ = "prediction"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.Enum(Category), nullable=False)
    created_at = db.Column(db.Date, default= lambda: datetime.now(timezone.utc))

    def to_dict(self):
        content = {"title": self.title,
         "description": self.description,
         "category": self.category.value,
         "created_at": self.created_at}
        return content


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
