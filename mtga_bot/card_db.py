from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class CardDatabase:
    """Lightweight lookup for MTGA card data loaded from cards.json."""

    def __init__(self, cards_path: Path) -> None:
        path = Path(cards_path).expanduser()
        with path.open("r", encoding="utf-8") as handle:
            raw_cards = json.load(handle)
        # Build fast lookup by grpId.
        self._cards: Dict[int, Dict[str, object]] = {int(card["grpId"]): card for card in raw_cards}

    def get(self, grp_id: int) -> Optional[Dict[str, object]]:
        return self._cards.get(int(grp_id))

    def is_land(self, grp_id: int) -> bool:
        card = self.get(grp_id)
        if not card:
            return False
        types = card.get("types") or []
        return any(str(t).lower() == "land" for t in types)

    def mana_value(self, grp_id: int) -> Optional[int]:
        card = self.get(grp_id)
        if not card:
            return None
        cost = card.get("manaCost")
        if not cost:
            return 0 if self.is_land(grp_id) else None
        return _parse_mana_cost(str(cost))

    def summarize_hand(self, grp_ids: List[int]) -> Dict[str, object]:
        """
        Return a small summary about a list of grpIds currently in hand.
        Keys: lands, spells, cheapest_spell, total_cards.
        """
        lands = 0
        spell_costs: List[int] = []
        for grp_id in grp_ids:
            if self.is_land(grp_id):
                lands += 1
                continue
            mana_value = self.mana_value(grp_id)
            if mana_value is not None:
                spell_costs.append(mana_value)
        cheapest = min(spell_costs) if spell_costs else None
        return {
            "total_cards": len(grp_ids),
            "lands": lands,
            "spells": len(grp_ids) - lands,
            "cheapest_spell": cheapest,
        }


def _parse_mana_cost(mana_cost: str) -> int:
    """
    Convert manaCost like "{2}{R}{R}" to a simple integer mana value.
    We treat each symbol as 1, numbers as their value, X as 0 (unknown).
    """
    symbols = mana_cost.replace("}{", " ").replace("{", "").replace("}", "").split()
    total = 0
    for sym in symbols:
        if not sym:
            continue
        if sym.lower() == "x":
            continue
        if sym.isdigit():
            total += int(sym)
        else:
            total += 1
    return total
