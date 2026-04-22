import pytest
from unittest.mock import MagicMock

from app import create_app, db as _db
from app.models import User, Achievement, Prediction, Category, PredictionStatus
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    VOTE_LIMIT = 1
    SIGNAL_CLI_PATH = "/fake/signal-cli"
    SIGNAL_LOG_PATH = "/tmp/signal_test.log"


@pytest.fixture(scope="session")
def app():
    application = create_app(config_class=TestConfig)
    with application.app_context():
        yield application


@pytest.fixture(autouse=True)
def db(app):
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()


@pytest.fixture(autouse=True)
def mock_signal(monkeypatch):
    monkeypatch.setattr("app.achievements.send_signal_message", MagicMock())
    monkeypatch.setattr("app.main.routes.send_signal_message", MagicMock())
    # Routes read Config.VOTE_LIMIT directly from the class, not from app.config
    monkeypatch.setattr("app.main.routes.Config.VOTE_LIMIT", 1)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(db):
    u = User(user_name="gentleboy", email="gentle@boy.com")
    u.set_password("password")
    _db.session.add(u)
    _db.session.commit()
    return u


@pytest.fixture
def second_user(db):
    u = User(user_name="otherguy", email="other@boy.com")
    u.set_password("password")
    _db.session.add(u)
    _db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    client.post("/login", data={
        "username": user.user_name,
        "password": "password",
        "remember_me": False,
    }, follow_redirects=False)
    return client


@pytest.fixture
def achievement(db):
    a = Achievement(id=1, title="First blood", description="First successful prediction", logo="blood.png")
    _db.session.add(a)
    _db.session.commit()
    return a


@pytest.fixture
def prediction(db, user):
    p = Prediction(
        user_id=user.id,
        title="The world will end",
        description="I have a bad feeling about this",
        category=Category.SCI,
        position=1,
        points=10,
        likelihood=50.0,  # route crashes with None likelihood/points (app bug)
    )
    _db.session.add(p)
    _db.session.commit()
    return p
