import json

from mtga_bot.log_parser import EventType, LogParser


def test_parse_quest_update():
    parser = LogParser("Player.log")
    events = parser.parse_line("Quest q123 updated 3/10 - Cast 10 red spells")

    assert events
    event = events[0]
    assert event.event_type == EventType.QUEST_UPDATE
    assert event.payload["quest_id"] == "q123"
    assert event.payload["progress"] == 3
    assert event.payload["goal"] == 10
    assert event.payload["kind"] == "cast_spells"


def test_parse_match_transitions():
    parser = LogParser("Player.log")
    start = parser.parse_line("Match abc started")[0]
    end = parser.parse_line("Match abc ended")[0]
    queue = parser.parse_line("Entering queue for Play")[0]

    assert start and start.event_type == EventType.MATCH_START
    assert end and end.event_type == EventType.MATCH_END
    assert queue and queue.event_type == EventType.QUEUE_ENTERED


def test_parse_multiline_gre_game_state():
    parser = LogParser("Player.log")
    lines = [
        '{ "transactionId": "abc", "greToClientEvent": { "greToClientMessages": [ { "type": "GREMessageType_GameStateMessage", "gameStateMessage": { "gameInfo": { "matchID": "match-123" }, "turnInfo": { "decisionPlayer": 2 } } } ] } }',
    ]
    events: list = []
    for line in lines:
        events.extend(parser.parse_line(line))

    assert events
    evt = events[0]
    assert evt.event_type == EventType.MATCH_START
    assert evt.payload["match_id"] == "match-123"
    assert evt.payload["decision_player"] == 2


def test_parse_actions_from_game_state_message():
    parser = LogParser("Player.log")
    blob = {
        "greToClientEvent": {
            "greToClientMessages": [
                {
                    "type": "GREMessageType_GameStateMessage",
                    "gameStateMessage": {
                        "gameInfo": {"matchID": "match-42"},
                        "actions": [
                            {"actionType": "ActionType_Cast", "instanceId": 123, "controllerSeatId": 1},
                            {"actionType": "ActionType_PlayLand", "objectId": 456},
                        ],
                    },
                }
            ]
        }
    }
    events = parser.parse_line(json.dumps(blob))

    action_events = [evt for evt in events if evt.event_type == EventType.ACTIONS_UPDATE]
    assert action_events
    actions = action_events[0].payload["actions"]
    assert len(actions) == 2
    assert actions[0]["actionType"] == "ActionType_Cast"
    assert actions[0]["instanceId"] == 123
    assert actions[1]["objectId"] == 456


def test_parse_actions_with_seat_and_actions_available_req():
    parser = LogParser("Player.log")
    blob = {
        "greToClientEvent": {
            "greToClientMessages": [
                {
                    "type": "GREMessageType_GameStateMessage",
                    "gameStateMessage": {
                        "type": "GameStateType_Diff",
                        "turnInfo": {"phase": "Phase_Main1", "turnNumber": 2, "activePlayer": 1, "priorityPlayer": 1},
                        "actions": [
                            {"seatId": 1, "action": {"actionType": "ActionType_Play", "instanceId": 162}},
                            {"seatId": 1, "action": {"actionType": "ActionType_Cast", "instanceId": 160, "objectId": 999}},
                        ],
                        "actionsAvailableReq": {
                            "actions": [
                                {"actionType": "ActionType_Pass"},
                                {"actionType": "ActionType_Play", "instanceId": 163, "grpId": 75555},
                            ]
                        },
                    },
                }
            ]
        }
    }
    events = parser.parse_line(json.dumps(blob))
    actions_evt = [evt for evt in events if evt.event_type == EventType.ACTIONS_UPDATE][0]
    actions = actions_evt.payload["actions"]
    assert len(actions) == 4
    play_with_seat = next(a for a in actions if a["actionType"] == "ActionType_Play" and a.get("instanceId") == 162)
    assert play_with_seat.get("seatId") == 1
    cast_action = next(a for a in actions if a["actionType"] == "ActionType_Cast")
    assert cast_action.get("objectId") == 999
    pass_action = next(a for a in actions if a["actionType"] == "ActionType_Pass")
    assert pass_action
    phase_evt = [evt for evt in events if evt.event_type == EventType.MATCH_START][0]
    assert phase_evt.payload["phase"] == "Phase_Main1"
