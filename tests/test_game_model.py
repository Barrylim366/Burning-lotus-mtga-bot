from mtga_bot.game_model import GameState, MatchPhase
from mtga_bot.log_parser import EventType, LogEvent


def test_apply_quest_update():
    state = GameState()
    event = LogEvent(
        EventType.QUEST_UPDATE,
        {"quest_id": "q123", "progress": 2, "goal": 5, "description": "Play 5 games", "kind": "play_games"},
    )
    state.apply_event(event)

    assert "q123" in state.quests
    quest = state.quests["q123"]
    assert quest.progress == 2
    assert quest.goal == 5
    assert not quest.is_complete()


def test_match_state_transitions():
    state = GameState()
    state.apply_event(LogEvent(EventType.QUEUE_ENTERED, {"message": ""}))
    assert state.phase == MatchPhase.QUEUED

    state.apply_event(LogEvent(EventType.MATCH_START, {"match_id": "abc"}))
    assert state.phase == MatchPhase.IN_MATCH
    assert state.match_id == "abc"
    assert not state.hand_kept

    # Duplicate match start should not reset keep flag once set.
    state.hand_kept = True
    state.apply_event(LogEvent(EventType.MATCH_START, {"match_id": "abc"}))
    assert state.hand_kept

    state.apply_event(LogEvent(EventType.MATCH_END, {"match_id": "abc"}))
    assert state.phase == MatchPhase.IDLE
    assert state.match_id is None


def test_hand_kept_resets_on_turn_start_without_match_start():
    state = GameState()
    state.hand_kept = True  # stale flag from previous match

    # If the client emits turn events before a match start event, the flag should reset.
    state.apply_event(LogEvent(EventType.TURN_START, {"turn": 1}))
    assert state.phase == MatchPhase.IN_MATCH
    assert not state.hand_kept


def test_hand_kept_persists_during_match_turns():
    state = GameState(phase=MatchPhase.IN_MATCH, hand_kept=True, turn=1)
    state.apply_event(LogEvent(EventType.TURN_START, {"turn": 2}))

    assert state.phase == MatchPhase.IN_MATCH
    assert state.hand_kept


def test_available_actions_update_and_reset():
    state = GameState()
    actions = [{"actionType": "ActionType_Cast", "instanceId": 111, "objectId": 222}]

    state.apply_event(LogEvent(EventType.ACTIONS_UPDATE, {"actions": actions}))

    assert state.available_actions
    action = state.available_actions[0]
    assert action.action_type == "ActionType_Cast"
    assert action.instance_id == 111
    assert action.object_id == 222

    state.apply_event(LogEvent(EventType.MATCH_END, {"match_id": "abc"}))
    assert state.available_actions == []


def test_land_play_turn_updates_when_action_disappears():
    state = GameState(phase=MatchPhase.IN_MATCH, turn=1, player_seat_id=1)
    # Land available to play for us
    actions = [{"actionType": "ActionType_Play", "instanceId": 200, "seatId": 1}]
    state.apply_event(LogEvent(EventType.ACTIONS_UPDATE, {"actions": actions}))
    assert state.last_play_land_turn == -1

    # After action disappears, assume it was played
    state.apply_event(LogEvent(EventType.ACTIONS_UPDATE, {"actions": []}))
    assert state.last_play_land_turn == 1
