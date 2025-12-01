from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Generator, List, Optional


class EventType(Enum):
    QUEST_UPDATE = auto()
    QUEST_COMPLETE = auto()
    TURN_START = auto()
    MATCH_START = auto()
    MATCH_END = auto()
    QUEUE_ENTERED = auto()
    QUEUE_EXITED = auto()
    ERROR = auto()
    HAND_UPDATE = auto()
    PRIORITY_UPDATE = auto()
    GRE_INFO = auto()
    ACTIONS_UPDATE = auto()


@dataclass
class LogEvent:
    event_type: EventType
    payload: Dict[str, object]


class LogParser:
    """Small helper to tail the MTGA Player.log and surface structured events."""

    def __init__(self, log_path: str) -> None:
        self.log_path = Path(log_path).expanduser()
        self._json_buffer: List[str] = []
        self._brace_depth = 0
        # MTGA log lines change often; keep patterns permissive but specific enough to test.
        self._quest_pattern = re.compile(
            r"Quest\s+(?P<quest_id>[\w-]+).*?(?P<progress>\d+)\s*/\s*(?P<goal>\d+)(?:\s*-\s*(?P<description>.+))?",
            re.IGNORECASE,
        )
        self._quest_complete_pattern = re.compile(
            r"Quest\s+(?P<quest_id>[\w-]+).*(complete|completed)", re.IGNORECASE
        )
        self._turn_pattern = re.compile(r"Turn\s+(?P<turn>\d+)\s+(begin|start)", re.IGNORECASE)
        self._queue_pattern = re.compile(r"(Entering|Joined)\s+queue", re.IGNORECASE)
        self._queue_exit_pattern = re.compile(r"(Queue\s+canceled|Match\s+canceled)", re.IGNORECASE)
        self._match_start_pattern = re.compile(
            r"Match\s+(?P<match_id>[\w-]+)\s+(started|start)", re.IGNORECASE
        )
        self._match_end_pattern = re.compile(
            r"Match\s+(?P<match_id>[\w-]+)\s+(ended|complete)", re.IGNORECASE
        )
        self._state_change_pattern = re.compile(
            r"STATE CHANGED.*\"new\":\"(?P<new_state>[^\"]+)\"", re.IGNORECASE
        )
        self._scene_loaded_pattern = re.compile(r"OnSceneLoaded for (?P<scene>\w+)", re.IGNORECASE)
        self._hand_zone_pattern = re.compile(
            r"(Zone_Hand|\"zone\"\\?\":\\?\"hand\\?\"|\"zoneType\"\\?\":\\?\"ZoneType_Hand\\?\"|\"hand\"\\?:)",
            re.IGNORECASE,
        )
        self._grp_id_pattern = re.compile(r'"grpId"\\?":\\?(\d+)')
        self._priority_pattern = re.compile(r'"?priorityPlayer"?\s*:\s*(\d+)', re.IGNORECASE)
        self._active_pattern = re.compile(r'"?activePlayer"?\s*:\s*(\d+)', re.IGNORECASE)
        # Turn info with phase/step, tolerant to long JSON blobs.
        self._turn_info_pattern = re.compile(
            r'"turnInfo"\s*:\s*\{[^}]*?"turnNumber"\s*:\s*(?P<turn>\d+)[^}]*?'
            r'"activePlayer"\s*:\s*(?P<active>\d+)[^}]*?'
            r'"priorityPlayer"\s*:\s*(?P<prio>\d+)?',
            re.IGNORECASE | re.DOTALL,
        )
        # Capture a hand zone for a given owner seat.
        self._hand_zone_full_pattern = re.compile(
            r'"type"\s*:\s*"ZoneType_Hand"[^}]*?'
            r'"ownerSeatId"\s*:\s*(?P<owner>\d+)[^}]*?'
            r'"objectInstanceIds"\s*:\s*\[(?P<ids>[^\]]*)\]',
            re.IGNORECASE,
        )

    def follow(self, poll_interval: float = 1.0, yield_unparsed: bool = False) -> Generator[LogEvent, None, None]:
        """
        Tail the log file and yield LogEvent objects as new lines arrive.

        The generator never ends unless the file is removed. It is intentionally
        lightweight so it can run alongside UI automation without blocking.
        """
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a+", encoding="utf-8", errors="ignore") as handle:
            handle.seek(0, os.SEEK_END)
            while True:
                line = handle.readline()
                if not line:
                    time.sleep(poll_interval)
                    continue

                events = self.parse_line(line)
                if events:
                    for event in events:
                        yield event
                elif self._json_buffer:
                    # Midway through a multi-line GRE JSON blob; wait for completion.
                    continue
                elif yield_unparsed:
                    yield LogEvent(EventType.ERROR, {"message": line.strip(), "unparsed": True})

    def parse_line(self, line: str) -> List[LogEvent]:
        """Convert a raw log line into one or more LogEvents (empty list if nothing matched)."""
        text = line.strip()
        if not text:
            return []

        buffered = self._process_json_buffer(text)
        if buffered is not None:
            return buffered

        # Priority / turn info first, to avoid short-circuit by other patterns.
        if "priority" in text.lower() or "activeplayer" in text.lower() or "turninfo" in text.lower():
            active_match = self._active_pattern.search(text)
            prio_match = self._priority_pattern.search(text)
            turn_match = self._turn_info_pattern.search(text)
            if active_match or prio_match or turn_match:
                payload: Dict[str, object] = {}
                if turn_match:
                    payload["turn"] = int(turn_match.group("turn"))
                    payload["active_player"] = int(turn_match.group("active"))
                    prio = turn_match.group("prio")
                    if prio:
                        payload["priority_player"] = int(prio)
                else:
                    if active_match:
                        payload["active_player"] = int(active_match.group(1))
                    if prio_match:
                        payload["priority_player"] = int(prio_match.group(1))
                return [LogEvent(EventType.PRIORITY_UPDATE, payload)]

        quest_match = self._quest_pattern.search(text)
        if quest_match:
            payload = {
                "quest_id": quest_match.group("quest_id"),
                "progress": int(quest_match.group("progress")),
                "goal": int(quest_match.group("goal")),
                "description": (quest_match.group("description") or "").strip(),
            }
            payload["kind"] = self._infer_quest_kind(payload["description"])
            return [LogEvent(EventType.QUEST_UPDATE, payload)]

        quest_complete_match = self._quest_complete_pattern.search(text)
        if quest_complete_match:
            payload = {"quest_id": quest_complete_match.group("quest_id")}
            return [LogEvent(EventType.QUEST_COMPLETE, payload)]

        # Capture hand composition updates (grpIds inside hand zone payloads).
        if self._hand_zone_pattern.search(text):
            grp_ids = [int(g) for g in self._grp_id_pattern.findall(text)]
            if grp_ids:
                return [LogEvent(EventType.HAND_UPDATE, {"grp_ids": grp_ids})]

        turn_match = self._turn_pattern.search(text)
        if turn_match:
            payload = {"turn": int(turn_match.group("turn"))}
            return [LogEvent(EventType.TURN_START, payload)]

        if self._queue_pattern.search(text):
            return [LogEvent(EventType.QUEUE_ENTERED, {"message": text})]

        if self._queue_exit_pattern.search(text):
            return [LogEvent(EventType.QUEUE_EXITED, {"message": text})]

        match_start = self._match_start_pattern.search(text)
        if match_start:
            return [LogEvent(EventType.MATCH_START, {"match_id": match_start.group("match_id")})]

        match_end = self._match_end_pattern.search(text)
        if match_end:
            return [LogEvent(EventType.MATCH_END, {"match_id": match_end.group("match_id")})]

        state_change = self._state_change_pattern.search(text)
        if state_change:
            new_state = state_change.group("new_state")
            lowered = new_state.lower()
            if "connectedtomatchdoor_connectingtogre" in lowered:
                return [LogEvent(EventType.QUEUE_ENTERED, {"state": new_state})]
            if "playing" in lowered or "duel" in lowered or "battlefield" in lowered:
                return [LogEvent(EventType.MATCH_START, {"state": new_state})]
            if "queue" in lowered or "connectingtomatchdoor" in lowered or "waiting" in lowered:
                return [LogEvent(EventType.QUEUE_ENTERED, {"state": new_state})]
            if "matchcompleted" in lowered or "postmatch" in lowered or "home" in lowered:
                return [LogEvent(EventType.MATCH_END, {"state": new_state})]

        scene_loaded = self._scene_loaded_pattern.search(text)
        if scene_loaded:
            scene = scene_loaded.group("scene").lower()
            if "duel" in scene or "battlefield" in scene:
                return [LogEvent(EventType.MATCH_START, {"scene": scene})]
            if "home" in scene or "mainmenu" in scene:
                return [LogEvent(EventType.QUEUE_EXITED, {"scene": scene})]

        # Priority / active player hints (requires detailed logs).
        if "priority" in text.lower() or "activeplayer" in text.lower():
            active_match = self._active_pattern.search(text)
            prio_match = self._priority_pattern.search(text)
            if active_match or prio_match:
                payload: Dict[str, object] = {}
                if active_match:
                    payload["active_player"] = int(active_match.group(1))
                if prio_match:
                    payload["priority_player"] = int(prio_match.group(1))
                return [LogEvent(EventType.PRIORITY_UPDATE, payload)]

        # Turn info and priority embedded in turnInfo blocks.
        turn_match = self._turn_info_pattern.search(text)
        if turn_match:
            payload = {
                "turn": int(turn_match.group("turn")),
                "active_player": int(turn_match.group("active")),
            }
            prio = turn_match.group("prio")
            if prio:
                payload["priority_player"] = int(prio)
            return [LogEvent(EventType.PRIORITY_UPDATE, payload)]

        # Full hand zone update (Detailed logs).
        if "ZoneType_Hand" in text:
            hand_match = self._hand_zone_full_pattern.search(text)
            if hand_match:
                ids_raw = hand_match.group("ids")
                grp_ids = []
                try:
                    for part in ids_raw.split(","):
                        part = part.strip()
                        if part:
                            grp_ids.append(int(part))
                except Exception:
                    grp_ids = []
                return [LogEvent(EventType.HAND_UPDATE, {"grp_ids": grp_ids})]

        if "error" in text.lower():
            return [LogEvent(EventType.ERROR, {"message": text})]

        return []

    def _process_json_buffer(self, text: str) -> Optional[List[LogEvent]]:
        """
        Collect GRE JSON blobs that are often split across multiple lines.
        Returns a list of events when a blob is complete, an empty list to keep buffering,
        or None when the line is not part of a GRE JSON blob.
        """
        # If we are buffering, keep collecting until braces balance.
        if self._json_buffer:
            self._json_buffer.append(text)
            self._brace_depth += text.count("{") - text.count("}")
            if self._brace_depth <= 0:
                blob = " ".join(self._json_buffer)
                self._json_buffer = []
                self._brace_depth = 0
                return self._parse_gre_json_blob(blob)
            return []

        if self._looks_like_gre_json_start(text):
            self._json_buffer = [text]
            self._brace_depth = text.count("{") - text.count("}")
            if self._brace_depth <= 0:
                blob = " ".join(self._json_buffer)
                self._json_buffer = []
                self._brace_depth = 0
                return self._parse_gre_json_blob(blob)
            return []

        return None

    @staticmethod
    def _looks_like_gre_json_start(text: str) -> bool:
        if not text.startswith("{"):
            return False
        markers = (
            "greToClientEvent",
            "matchGameRoomStateChangedEvent",
            "gameStateMessage",
            "clientToMatchServiceMessageType",
            "dieRollResultsResp",
            "chooseStartingPlayer",
            "setSettingsReq",
            "setSettingsResp",
        )
        # If any marker is present, it's a GRE JSON blob. Otherwise, accept any
        # brace-starting line to allow multi-line GRE messages that begin with just "{".
        return bool(any(marker in text for marker in markers) or text.strip().startswith("{"))

    def _parse_gre_json_blob(self, blob: str) -> List[LogEvent]:
        try:
            data = json.loads(blob)
        except Exception:
            return []

        events: List[LogEvent] = []

        # GRE -> Client messages (GameState, die roll, etc.)
        gre_messages = (data.get("greToClientEvent") or {}).get("greToClientMessages", [])
        for message in gre_messages:
            mtype = message.get("type")
            if mtype == "GREMessageType_ConnectResp":
                connect = message.get("connectResp", {})
                deck_cards = (message.get("deckMessage") or {}).get("deckCards")
                events.append(
                    LogEvent(
                        EventType.GRE_INFO,
                        {
                            "kind": "connect",
                            "settings": connect.get("settings"),
                            "deck_cards": deck_cards,
                        },
                    )
                )
            elif mtype == "GREMessageType_DieRollResultsResp":
                rolls = (message.get("dieRollResultsResp") or {}).get("playerDieRolls", [])
                events.append(LogEvent(EventType.MATCH_START, {"die_rolls": rolls}))
            elif mtype == "GREMessageType_GameStateMessage":
                payload: Dict[str, object] = {}
                game_state = message.get("gameStateMessage") or {}
                game_info = game_state.get("gameInfo") or {}
                match_id = game_info.get("matchID")
                if match_id:
                    payload["match_id"] = match_id
                turn_info = game_state.get("turnInfo") or {}
                if "turnNumber" in turn_info:
                    try:
                        payload["turn"] = int(turn_info.get("turnNumber"))
                    except Exception:
                        pass
                if "activePlayer" in turn_info:
                    try:
                        payload["active_player"] = int(turn_info.get("activePlayer"))
                    except Exception:
                        pass
                if "priorityPlayer" in turn_info:
                    try:
                        payload["priority_player"] = int(turn_info.get("priorityPlayer"))
                    except Exception:
                        pass
                if "decisionPlayer" in turn_info:
                    try:
                        payload["decision_player"] = int(turn_info.get("decisionPlayer"))
                    except Exception:
                        pass
                if "phase" in turn_info:
                    payload["phase"] = turn_info.get("phase")
                if "step" in turn_info:
                    payload["step"] = turn_info.get("step")
                choose_req = game_state.get("chooseStartingPlayerReq")
                if choose_req:
                    payload["pending_start_choice"] = True
                    payload["starting_player_options"] = choose_req.get("systemSeatIds")
                pending_type = game_state.get("pendingMessageType")
                if pending_type:
                    payload["pending_message_type"] = pending_type
                actions_present = "actions" in game_state or "actionsAvailableReq" in game_state
                actions_payload = self._extract_actions_from_game_state(game_state)
                events.append(LogEvent(EventType.MATCH_START, payload))
                if actions_payload or actions_present:
                    events.append(LogEvent(EventType.ACTIONS_UPDATE, {"actions": actions_payload}))

        # Client -> GRE messages (e.g., choosing starting player, mulligan)
        if data.get("clientToMatchServiceMessageType") == "ClientToMatchServiceMessageType_ClientToGREMessage":
            payload = data.get("payload") or {}
            msg_type = payload.get("type")
            if msg_type == "ClientMessageType_ChooseStartingPlayerResp":
                resp = payload.get("chooseStartingPlayerResp") or {}
                starting_player = resp.get("systemSeatId")
                updates: Dict[str, object] = {}
                if starting_player is not None:
                    try:
                        updates["starting_player"] = int(starting_player)
                    except Exception:
                        updates["starting_player"] = starting_player
                if updates:
                    events.append(LogEvent(EventType.PRIORITY_UPDATE, updates))
            elif msg_type == "ClientMessageType_MulliganResp":
                resp = payload.get("mulliganResp") or {}
                decision = resp.get("decision")
                if decision:
                    events.append(LogEvent(EventType.HAND_UPDATE, {"mulligan_decision": decision}))

        return events

    @staticmethod
    def _infer_quest_kind(description: str) -> str:
        """
        Lightweight heuristic to classify quests.
        Results are used by the QuestAI to pick strategies.
        """
        lowered = description.lower()
        if "spell" in lowered or "zauber" in lowered:
            return "cast_spells"
        if "creature" in lowered or "angreifen" in lowered or "attack" in lowered:
            return "combat"
        return "play_games"

    @staticmethod
    def _extract_actions_from_game_state(game_state: Dict[str, object]) -> List[Dict[str, object]]:
        """
        Pull a simplified list of available GRE actions out of the GameState message.
        We keep the fields that are most helpful for UI targeting (type + ids).
        """
        simplified: List[Dict[str, object]] = []

        # Case 1: actions directly on gameStateMessage, but wrapped as {"seatId":..., "action": {...}}
        actions_raw = game_state.get("actions")
        if isinstance(actions_raw, list):
            for entry in actions_raw:
                if not isinstance(entry, dict):
                    continue
                action_obj = entry.get("action") if isinstance(entry.get("action"), dict) else entry
                if not isinstance(action_obj, dict):
                    continue
                action_type = action_obj.get("actionType") or action_obj.get("type")
                if not action_type:
                    continue
                cleaned: Dict[str, object] = {"actionType": action_type}
                for key in ("instanceId", "objectId", "grpId", "sourceId", "controllerSeatId", "requestId"):
                    if key in action_obj:
                        cleaned[key] = action_obj.get(key)
                if "seatId" in entry:
                    cleaned["seatId"] = entry.get("seatId")
                simplified.append(cleaned)

        # Case 2: ActionsAvailableReq -> actionsAvailableReq.actions
        aar = game_state.get("actionsAvailableReq") or {}
        aar_actions = aar.get("actions")
        if isinstance(aar_actions, list):
            for action_obj in aar_actions:
                if not isinstance(action_obj, dict):
                    continue
                action_type = action_obj.get("actionType") or action_obj.get("type")
                if not action_type:
                    continue
                cleaned: Dict[str, object] = {"actionType": action_type}
                for key in ("instanceId", "objectId", "grpId", "sourceId", "controllerSeatId", "requestId"):
                    if key in action_obj:
                        cleaned[key] = action_obj.get(key)
                simplified.append(cleaned)

        return simplified
