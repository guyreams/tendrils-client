"""Session state tracking for the current game."""


PRESETS = {
    "fighter": {
        "name": "Gronk the Fighter",
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
        self.character_id: str | None = None
        self.character_name: str | None = None
        self.has_character: bool = False
        self.game_status: str | None = None  # waiting, active, completed

    def set_character(self, character_id: str, name: str):
        self.character_id = character_id
        self.character_name = name
        self.has_character = True

    def reset(self):
        self.character_id = None
        self.character_name = None
        self.has_character = False
        self.game_status = None
