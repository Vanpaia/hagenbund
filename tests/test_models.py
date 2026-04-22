import pytest
from app import db
from app.models import (
    User, Achievement, UserAchievement, Prediction, PredictionConclusion,
    PredictionConclusionVote, StockPick, Category, PredictionStatus,
    ConclusionOutcome, ConclusionStatus, PredictionVote,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

def test_prediction_status_sentence_success():
    assert PredictionStatus.SUCCESS.sentence() == "came true"


def test_prediction_status_sentence_failed():
    assert PredictionStatus.FAILED.sentence() == "did not come true"


def test_conclusion_outcome_sentence_success():
    assert ConclusionOutcome.SUCCESS.sentence() == "successful"


def test_conclusion_outcome_sentence_failed():
    assert ConclusionOutcome.FAILED.sentence() == "failed"


# ---------------------------------------------------------------------------
# User — password
# ---------------------------------------------------------------------------

def test_set_and_check_password(user):
    assert user.check_password("password") is True


def test_wrong_password_rejected(user):
    assert user.check_password("wrong") is False


# ---------------------------------------------------------------------------
# User — hybrid properties (Python side)
# ---------------------------------------------------------------------------

def _make_stock(user_id, initial, current):
    return StockPick(
        user_id=user_id, symbol="TEST", name="Test Co", currency="USD",
        country="US", ceo="Nobody", exchange_full_name="NYSE", exchange="NYSE",
        sector="Tech", industry="Software", employees=100, website="x.com",
        image="img.png", initial_price=initial, current_price=current,
    )


def test_total_investment_no_stocks(user):
    assert user.total_investment == 0.0


def test_total_investment_with_stock(user):
    stock = _make_stock(user.id, initial=100.0, current=150.0)
    db.session.add(stock)
    db.session.commit()
    db.session.refresh(user)
    # 1000 / 100 * 150 = 1500
    assert user.total_investment == 1500.0


def test_total_investment_multiple_stocks(user):
    db.session.add(_make_stock(user.id, initial=100.0, current=200.0))
    s2 = StockPick(
        user_id=user.id, symbol="MSFT", name="Microsoft", currency="USD",
        country="US", ceo="Satya", exchange_full_name="NASDAQ", exchange="NASDAQ",
        sector="Tech", industry="Software", employees=200000, website="msft.com",
        image="msft.png", initial_price=50.0, current_price=25.0,
    )
    db.session.add(s2)
    db.session.commit()
    db.session.refresh(user)
    # (1000/100*200) + (1000/50*25) = 2000 + 500 = 2500
    assert user.total_investment == 2500.0


def test_total_achieved_points_no_predictions(user):
    assert user.total_achieved_points == 0


def test_total_achieved_points_counts_only_success(user):
    db.session.add(Prediction(user_id=user.id, title="A", category=Category.POL, position=1, points=10, multiplier=2, status=PredictionStatus.SUCCESS))
    db.session.add(Prediction(user_id=user.id, title="B", category=Category.EUR, position=1, points=5,  multiplier=1, status=PredictionStatus.FAILED))
    db.session.add(Prediction(user_id=user.id, title="C", category=Category.SCI, position=1, points=8,  multiplier=1, status=PredictionStatus.PENDING))
    db.session.commit()
    db.session.refresh(user)
    assert user.total_achieved_points == 20  # only prediction A


def test_total_failed_points(user):
    db.session.add(Prediction(user_id=user.id, title="A", category=Category.POL, position=1, points=10, multiplier=3, status=PredictionStatus.FAILED))
    db.session.add(Prediction(user_id=user.id, title="B", category=Category.EUR, position=1, points=5,  multiplier=1, status=PredictionStatus.SUCCESS))
    db.session.commit()
    db.session.refresh(user)
    assert user.total_failed_points == 30  # only prediction A


def test_total_outstanding_points(user):
    db.session.add(Prediction(user_id=user.id, title="A", category=Category.POL, position=1, points=10, multiplier=1, status=PredictionStatus.PENDING))
    db.session.add(Prediction(user_id=user.id, title="B", category=Category.EUR, position=1, points=6,  multiplier=2, status=PredictionStatus.VOTING))
    db.session.add(Prediction(user_id=user.id, title="C", category=Category.SCI, position=1, points=5,  multiplier=1, status=PredictionStatus.SUCCESS))
    db.session.commit()
    db.session.refresh(user)
    assert user.total_outstanding_points == 22  # 10 + 12, not 5


def test_points_defaults_to_zero_when_null(user):
    db.session.add(Prediction(user_id=user.id, title="A", category=Category.POL, position=1, points=None, multiplier=1, status=PredictionStatus.SUCCESS))
    db.session.commit()
    db.session.refresh(user)
    assert user.total_achieved_points == 0


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def test_prediction_to_dict_keys(prediction):
    d = prediction.to_dict()
    assert set(d.keys()) == {"title", "uuid", "id", "description", "category", "user_id", "author", "created_at"}


def test_prediction_to_dict_values(prediction, user):
    d = prediction.to_dict()
    assert d["title"] == prediction.title
    assert d["category"] == Category.SCI.value
    assert d["user_id"] == user.id
    assert d["author"] == user.user_name


# ---------------------------------------------------------------------------
# PredictionConclusion — vote counting
# ---------------------------------------------------------------------------

def _make_conclusion(user, prediction):
    c = PredictionConclusion(
        prediction_id=prediction.id,
        user_id=user.id,
        description="It happened",
        outcome=ConclusionOutcome.SUCCESS,
    )
    db.session.add(c)
    db.session.commit()
    return c


def test_total_in_favour_empty(user, prediction):
    c = _make_conclusion(user, prediction)
    assert c.total_in_favour == 0


def test_total_against_empty(user, prediction):
    c = _make_conclusion(user, prediction)
    assert c.total_against == 0


def test_total_in_favour_counts_true_votes(user, second_user, prediction):
    c = _make_conclusion(user, prediction)
    db.session.add(PredictionConclusionVote(user_id=user.id, prediction_conclusion_id=c.id, vote=True))
    db.session.add(PredictionConclusionVote(user_id=second_user.id, prediction_conclusion_id=c.id, vote=False))
    db.session.commit()
    db.session.refresh(c)
    assert c.total_in_favour == 1
    assert c.total_against == 1


def test_get_user_vote_returns_vote(user, prediction):
    c = _make_conclusion(user, prediction)
    v = PredictionConclusionVote(user_id=user.id, prediction_conclusion_id=c.id, vote=True)
    db.session.add(v)
    db.session.commit()
    result = c.get_user_vote(user.id)
    assert result is not None
    assert result.vote is True


def test_get_user_vote_returns_none_for_non_voter(user, second_user, prediction):
    c = _make_conclusion(user, prediction)
    assert c.get_user_vote(second_user.id) is None


# ---------------------------------------------------------------------------
# StockPick
# ---------------------------------------------------------------------------

def test_total_return_gain(user):
    s = _make_stock(user.id, initial=100.0, current=150.0)
    assert s.total_return == 50.0


def test_total_return_loss(user):
    s = _make_stock(user.id, initial=100.0, current=75.0)
    assert s.total_return == -25.0


def test_total_return_flat(user):
    s = _make_stock(user.id, initial=100.0, current=100.0)
    assert s.total_return == 0.0


def test_highest_return_empty_db():
    assert StockPick.highest_return() is None


def test_lowest_return_empty_db():
    assert StockPick.lowest_return() is None


def test_highest_return(user, second_user):
    good = _make_stock(user.id, initial=100.0, current=200.0)   # +100%
    bad  = StockPick(
        user_id=second_user.id, symbol="BAD", name="Bad Co", currency="USD",
        country="US", ceo="Nobody", exchange_full_name="NYSE", exchange="NYSE",
        sector="Tech", industry="Software", employees=1, website="bad.com",
        image="bad.png", initial_price=100.0, current_price=50.0,           # -50%
    )
    db.session.add_all([good, bad])
    db.session.commit()
    assert StockPick.highest_return().symbol == "TEST"


def test_lowest_return(user, second_user):
    good = _make_stock(user.id, initial=100.0, current=200.0)   # +100%
    bad  = StockPick(
        user_id=second_user.id, symbol="BAD", name="Bad Co", currency="USD",
        country="US", ceo="Nobody", exchange_full_name="NYSE", exchange="NYSE",
        sector="Tech", industry="Software", employees=1, website="bad.com",
        image="bad.png", initial_price=100.0, current_price=50.0,           # -50%
    )
    db.session.add_all([good, bad])
    db.session.commit()
    assert StockPick.lowest_return().symbol == "BAD"
