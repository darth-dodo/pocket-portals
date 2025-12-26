"""Enemy templates database for Pocket Portals."""

from src.state.models import Enemy

# Enemy templates for common encounters
ENEMY_TEMPLATES = {
    "goblin": Enemy(
        name="Goblin Raider",
        description="A small, green-skinned creature with a wicked grin and sharp teeth",
        max_hp=7,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6+2",
    ),
    "bandit": Enemy(
        name="Bandit Outlaw",
        description="A rough-looking human with a scarred face and tattered leather armor",
        max_hp=11,
        armor_class=12,
        attack_bonus=3,
        damage_dice="1d6+1",
    ),
    "skeleton": Enemy(
        name="Skeleton Warrior",
        description="An animated skeleton wielding a rusty sword and wearing tattered armor",
        max_hp=13,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6+2",
    ),
    "wolf": Enemy(
        name="Dire Wolf",
        description="A large, fierce wolf with matted gray fur and glowing yellow eyes",
        max_hp=11,
        armor_class=13,
        attack_bonus=5,
        damage_dice="2d4+3",
    ),
    "orc": Enemy(
        name="Orc Warrior",
        description="A muscular, gray-skinned humanoid with tusks and a battle-scarred face",
        max_hp=15,
        armor_class=13,
        attack_bonus=5,
        damage_dice="1d12+3",
    ),
}
