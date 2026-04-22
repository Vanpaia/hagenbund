import pytest
from unittest.mock import MagicMock, patch

from app.live_game import GameState, update_best_stats


# ---------------------------------------------------------------------------
# update_best_stats (pure function)
# ---------------------------------------------------------------------------

def test_update_best_stats_empty_list_creates_entry():
    result = update_best_stats([], "Alice", 42)
    assert result == [{"name": "Alice", "value": 42}]


def test_update_best_stats_new_low_replaces_list():
    stats = [{"name": "Alice", "value": 50}]
    result = update_best_stats(stats, "Bob", 30, find_max=False)
    assert result == [{"name": "Bob", "value": 30}]


def test_update_best_stats_new_high_replaces_list():
    stats = [{"name": "Alice", "value": 50}]
    result = update_best_stats(stats, "Bob", 80, find_max=True)
    assert result == [{"name": "Bob", "value": 80}]


def test_update_best_stats_worse_value_ignored():
    stats = [{"name": "Alice", "value": 30}]
    result = update_best_stats(stats, "Bob", 50, find_max=False)
    assert result == [{"name": "Alice", "value": 30}]


def test_update_best_stats_tie_appends():
    stats = [{"name": "Alice", "value": 50}]
    result = update_best_stats(stats, "Bob", 50, find_max=False)
    assert len(result) == 2
    assert any(r["name"] == "Bob" for r in result)


def test_update_best_stats_find_max_tie_appends():
    stats = [{"name": "Alice", "value": 80}]
    result = update_best_stats(stats, "Bob", 80, find_max=True)
    assert len(result) == 2


def test_update_best_stats_default_find_min():
    stats = [{"name": "Alice", "value": 30}]
    # Default find_max=False — 40 is worse (higher), should be ignored
    result = update_best_stats(stats, "Bob", 40)
    assert result == [{"name": "Alice", "value": 30}]


# ---------------------------------------------------------------------------
# GameState
# ---------------------------------------------------------------------------

@pytest.fixture
def game():
    return GameState()


@pytest.fixture
def questions():
    return [
        {"id": 1, "title": "Q1", "uuid": "a"},
        {"id": 2, "title": "Q2", "uuid": "b"},
        {"id": 3, "title": "Q3", "uuid": "c"},
    ]


def test_gamestate_initial_state(game):
    assert game.is_active is False
    assert game.is_paused is True
    assert game.current_round == 1
    assert game.total_rounds == 0
    assert game.players == {}


def test_gamestate_init_game(game, questions):
    game.init_game(questions)
    assert game.is_active is True
    assert game.total_rounds == 3
    assert game.questions == questions


def test_gamestate_init_game_custom_round_length(game, questions):
    game.init_game(questions, round_length=60000)
    assert game.round_length == 60000


def test_gamestate_init_game_custom_player_amount(game, questions):
    game.init_game(questions, player_amount=5)
    assert game.total_players == 5


def test_gamestate_reset(game, questions):
    game.init_game(questions)
    game.reset()
    assert game.is_active is False
    assert game.is_paused is True
    assert game.current_round == 1
    assert game.players == {}
    # reset() keeps questions but recalculates total_rounds from them
    assert game.total_rounds == len(questions)


def test_gamestate_get_remaining_ms_before_start(game, questions):
    game.init_game(questions)
    # No clock started yet — returns full round_length
    assert game.get_remaining_ms() == game.round_length


def test_gamestate_start_round_sets_clock(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    assert game.is_paused is False
    remaining = game.get_remaining_ms()
    assert 0 < remaining <= game.round_length


def test_gamestate_pause_reduces_remaining(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    game.pause_round()
    assert game.is_paused is True
    assert game.round_clocks[1]["pause_time_remaining"] > 0


def test_gamestate_unpause_resumes(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    game.pause_round()
    game.unpause_round()
    assert game.is_paused is False


def test_gamestate_get_game_status_keys(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    status = game.get_game_status()
    assert "remaining_ms" in status
    assert "is_paused" in status
    assert "is_active" in status
    assert "current_round" in status
    assert "total_rounds" in status
    assert "round_length" in status
    assert "round_data" in status


def test_gamestate_get_timer_status_keys(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    status = game.get_timer_status()
    assert "remaining_ms" in status
    assert "is_paused" in status


def test_gamestate_next_round_increments(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    game.next_round(mock_socketio)
    assert game.current_round == 2


def test_gamestate_previous_round_decrements(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    game.next_round(mock_socketio)
    game.previous_round(mock_socketio)
    assert game.current_round == 1


def test_gamestate_previous_round_does_not_go_below_one(game, questions):
    mock_socketio = MagicMock()
    game.init_game(questions)
    game.start_round(mock_socketio)
    game.previous_round(mock_socketio)
    assert game.current_round == 1
