"""Session state tracking for the current game."""


PRESETS = {
    "fighter": {
        "name": "Gronk the Fighter",
        "owner_id": "player1",
        "ability_scores": {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 8,
            "wisdom": 10,
            "charisma": 10,
        },
        "max_hp": 30,
        "armor_class": 16,
        "speed": 30,
        "attacks": [
            {
                "name": "Longsword",
                "attack_bonus": 5,
                "damage_dice": "1d8",
                "damage_bonus": 3,
                "damage_type": "slashing",
                "reach": 5,
            }
        ],
    },
    "rogue": {
        "name": "Shadow the Rogue",
        "owner_id": "player2",
        "ability_scores": {
            "strength": 10,
            "dexterity": 16,
            "constitution": 12,
            "intelligence": 14,
            "wisdom": 10,
            "charisma": 12,
        },
        "max_hp": 22,
        "armor_class": 14,
        "speed": 30,
        "attacks": [
            {
                "name": "Dagger",
                "attack_bonus": 5,
                "damage_dice": "1d4",
                "damage_bonus": 3,
                "damage_type": "piercing",
                "reach": 5,
            }
        ],
    },
    "barbarian": {
        "name": "Ragna the Barbarian",
        "owner_id": "player3",
        "ability_scores": {
            "strength": 18,
            "dexterity": 10,
            "constitution": 16,
            "intelligence": 6,
            "wisdom": 10,
            "charisma": 8,
        },
        "max_hp": 38,
        "armor_class": 13,
        "speed": 30,
        "attacks": [
            {
                "name": "Greataxe",
                "attack_bonus": 6,
                "damage_dice": "1d12",
                "damage_bonus": 4,
                "damage_type": "slashing",
                "reach": 5,
            }
        ],
    },
    "monk": {
        "name": "Kira the Monk",
        "owner_id": "player4",
        "ability_scores": {
            "strength": 10,
            "dexterity": 18,
            "constitution": 12,
            "intelligence": 10,
            "wisdom": 16,
            "charisma": 8,
        },
        "max_hp": 20,
        "armor_class": 17,
        "speed": 40,
        "attacks": [
            {
                "name": "Unarmed Strike",
                "attack_bonus": 6,
                "damage_dice": "1d6",
                "damage_bonus": 4,
                "damage_type": "bludgeoning",
                "reach": 5,
            }
        ],
    },
}


class GameSession:
    def __init__(self):
        self.characters: dict[str, dict] = {}  # owner_id -> {character_id, name, owner_id}
        self.active_character: str | None = None  # character_id currently controlled
        self.game_status: str | None = None  # waiting, active, completed

    def reset(self):
        self.characters.clear()
        self.active_character = None
        self.game_status = None

    def add_character(self, owner_id: str, character_id: str, name: str):
        self.characters[owner_id] = {
            "character_id": character_id,
            "name": name,
            "owner_id": owner_id,
        }
        if self.active_character is None:
            self.active_character = character_id

    def get_character_by_id(self, character_id: str) -> dict | None:
        for char in self.characters.values():
            if char["character_id"] == character_id:
                return char
        return None

    def get_all_character_ids(self) -> list[str]:
        return [c["character_id"] for c in self.characters.values()]
