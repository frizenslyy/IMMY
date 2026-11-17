"""IMMY — артефакты: 30 крафтов из эссенций (фрагментов) и самоцветов.

Природа артефакта, совпавшая с природой бойца, усиливает все его баффы на +7%.
На бойца надевается до ART_SLOTS артефактов.
"""

from .config import ART_SLOTS, NATURE_MATCH_BONUS
from .heroes import HEROES

NATURES = ("light", "dark", "fire", "earth", "water", "wind")

NATURE_LABEL = {"light": "СВЕТ", "dark": "ТЬМА", "fire": "ОГОНЬ",
                "earth": "ЗЕМЛЯ", "water": "ВОДА", "wind": "ВЕТЕР"}

NATURE_COLOR = {"light": "#fff2b0", "dark": "#b08aff", "fire": "#ff8c1a",
                "earth": "#c9a15a", "water": "#5ab4ff", "wind": "#bfe9d0"}

NATURE_BY_STYLE = {"flame": "fire", "glow": "light", "hood": "dark",
                   "spike": "earth", "spider": "dark"}

BUFF_LABEL = {"dmg": "СИЛА", "armor": "БРОНЯ", "blast": "СТОЙК. К ВЗРЫВУ", "hp": "ЗДОРОВЬЕ",
              "spd": "СКОРОСТЬ", "crit": "КРИТ", "energy": "ЭНЕРГИЯ", "vamp": "ВАМПИРИЗМ",
              "parry": "ПАРИРОВАНИЕ"}


def hero_nature(key):
    st = HEROES[key].get("style", "plain")
    if st in NATURE_BY_STYLE:
        return NATURE_BY_STYLE[st]
    return "water" if sum(ord(c) for c in key) % 2 == 0 else "wind"


ARTIFACTS = [
    {"id": "ember_charm", "name": "ОБЕРЕГ УГЛЕЙ", "tier": 1, "nature": "fire",
     "buff": {"dmg": 0.04}, "cost": {"fire": 2}, "gems": 0,
     "desc": "Слабый, но верный талисман бойцов огня."},
    {"id": "stone_palm", "name": "КАМЕННАЯ ЛАДОНЬ", "tier": 1, "nature": "earth",
     "buff": {"dmg": 0.04}, "cost": {"earth": 2}, "gems": 0,
     "desc": "Тяжёлый удар, выбитый в скале."},
    {"id": "light_shard", "name": "ОСКОЛОК СВЕТА", "tier": 1, "nature": "light",
     "buff": {"energy": 0.08}, "cost": {"light": 2}, "gems": 0,
     "desc": "Энергия копится чуть быстрее."},
    {"id": "dusk_veil", "name": "ПОКРОВ СУМЕРЕК", "tier": 1, "nature": "dark",
     "buff": {"crit": 0.03}, "cost": {"dark": 2}, "gems": 0,
     "desc": "Тень скрывает уязвимые точки врага."},
    {"id": "drop_pendant", "name": "КУЛОН КАПЛИ", "tier": 1, "nature": "water",
     "buff": {"hp": 0.04}, "cost": {"water": 2}, "gems": 0,
     "desc": "Вода восполняет силы."},
    {"id": "breath_wind", "name": "ДЫХАНИЕ ВЕТРА", "tier": 1, "nature": "wind",
     "buff": {"spd": 0.04}, "cost": {"wind": 2}, "gems": 0,
     "desc": "Ноги становятся легче."},
    {"id": "molten_plate", "name": "ПЛАВЛЕНЫЙ ПАНЦИРЬ", "tier": 2, "nature": "fire",
     "buff": {"armor": 0.05, "dmg": 0.05}, "cost": {"fire": 3, "earth": 1}, "gems": 3,
     "desc": "Броня, закалённая в магме."},
    {"id": "quake_fist", "name": "КУЛАК ЗЕМЛЕТРЯСЕНИЯ", "tier": 2, "nature": "earth",
     "buff": {"dmg": 0.08}, "cost": {"earth": 3, "fire": 1}, "gems": 3,
     "desc": "Каждый удар сотрясает арену."},
    {"id": "aegis_dawn", "name": "ЭГИДА РАССВЕТА", "tier": 2, "nature": "light",
     "buff": {"armor": 0.06}, "cost": {"light": 3, "wind": 1}, "gems": 3,
     "desc": "Свет гасит часть входящего урона."},
    {"id": "night_fang", "name": "КЛЫК НОЧИ", "tier": 2, "nature": "dark",
     "buff": {"crit": 0.05, "dmg": 0.04}, "cost": {"dark": 3, "water": 1}, "gems": 3,
     "desc": "Удары из тени рвут глубже."},
    {"id": "tide_heart", "name": "СЕРДЦЕ ПРИЛИВА", "tier": 2, "nature": "water",
     "buff": {"hp": 0.08}, "cost": {"water": 3, "light": 1}, "gems": 3,
     "desc": "Запас здоровья моря."},
    {"id": "gale_steps", "name": "СТУПЕНИ БУРИ", "tier": 2, "nature": "wind",
     "buff": {"spd": 0.08}, "cost": {"wind": 3, "light": 1}, "gems": 3,
     "desc": "Движение подобно урагану."},
    {"id": "blast_ward", "name": "ОБЕРЕГ ВЗРЫВА", "tier": 2, "nature": "earth",
     "buff": {"blast": 0.15}, "cost": {"earth": 2, "water": 2}, "gems": 4,
     "desc": "Взрывной урон ослаблен на 15%."},
    {"id": "leech_sigil", "name": "ЗНАК ПИЯВКИ", "tier": 2, "nature": "dark",
     "buff": {"vamp": 0.06}, "cost": {"dark": 2, "fire": 2}, "gems": 4,
     "desc": "Часть урона возвращается здоровьем."},
    {"id": "parry_rune", "name": "РУНА ОТРАЖЕНИЯ", "tier": 2, "nature": "light",
     "buff": {"parry": 0.05}, "cost": {"light": 2, "wind": 2}, "gems": 4,
     "desc": "Окно парирования шире."},
    {"id": "phoenix_ash", "name": "ПЕПЕЛ ФЕНИКСА", "tier": 3, "nature": "fire",
     "buff": {"dmg": 0.12, "hp": 0.06}, "cost": {"fire": 5, "light": 2, "earth": 1}, "gems": 10,
     "desc": "Сила возрождения в каждом ударе."},
    {"id": "titan_core", "name": "ЯДРО ТИТАНА", "tier": 3, "nature": "earth",
     "buff": {"armor": 0.10, "hp": 0.08}, "cost": {"earth": 5, "fire": 2, "water": 1}, "gems": 10,
     "desc": "Тело крепче крепости."},
    {"id": "sun_crown", "name": "ВЕНЕЦ СОЛНЦА", "tier": 3, "nature": "light",
     "buff": {"energy": 0.15, "parry": 0.04}, "cost": {"light": 5, "wind": 2, "fire": 1}, "gems": 10,
     "desc": "Энергия льётся рекой."},
    {"id": "void_mark", "name": "ЗНАК ПУСТОТЫ", "tier": 3, "nature": "dark",
     "buff": {"crit": 0.08, "vamp": 0.05}, "cost": {"dark": 5, "water": 2, "earth": 1}, "gems": 10,
     "desc": "Пустота жаждет крови."},
    {"id": "abyss_pearl", "name": "ЖЕМЧУГ БЕЗДНЫ", "tier": 3, "nature": "water",
     "buff": {"hp": 0.12, "armor": 0.05}, "cost": {"water": 5, "light": 2, "wind": 1}, "gems": 10,
     "desc": "Глубина терпит и хранит."},
    {"id": "storm_engine", "name": "ДВИГАТЕЛЬ ШТОРМА", "tier": 3, "nature": "wind",
     "buff": {"spd": 0.12, "crit": 0.04}, "cost": {"wind": 5, "light": 2, "water": 1}, "gems": 10,
     "desc": "Скорость, недоступная глазу."},
    {"id": "warlord_seal", "name": "ПЕЧАТЬ ВОЕНАЧАЛЬНИКА", "tier": 3, "nature": "fire",
     "buff": {"dmg": 0.10, "armor": 0.05, "blast": 0.10}, "cost": {"fire": 4, "earth": 3}, "gems": 12,
     "desc": "Печать полководца: баланс атаки и защиты."},
    {"id": "blood_pact", "name": "КРОВАВЫЙ ПАКТ", "tier": 3, "nature": "dark",
     "buff": {"dmg": 0.09, "vamp": 0.08}, "cost": {"dark": 4, "water": 3}, "gems": 12,
     "desc": "Сила за счёт чужой крови."},
    {"id": "saint_aegis", "name": "ЭГИДА СВЯТОГО", "tier": 3, "nature": "light",
     "buff": {"armor": 0.09, "blast": 0.12}, "cost": {"light": 4, "earth": 3}, "gems": 12,
     "desc": "Щит от взрывов и клинков."},
    {"id": "colossus_shard", "name": "ОСКОЛОК КОЛОССА", "tier": 3, "nature": "earth",
     "buff": {"hp": 0.10, "dmg": 0.06, "spd": -0.03}, "cost": {"earth": 6, "fire": 2}, "gems": 14,
     "desc": "Огромная мощь ценой прыти."},
    {"id": "mirror_soul", "name": "ЗЕРКАЛО ДУШИ", "tier": 3, "nature": "water",
     "buff": {"parry": 0.06, "energy": 0.10}, "cost": {"water": 4, "light": 3}, "gems": 14,
     "desc": "Отражай всё — от удара до заклятия."},
    {"id": "chaos_orb", "name": "СФЕРА ХАОСА", "tier": 3, "nature": "dark",
     "buff": {"dmg": 0.07, "crit": 0.06, "spd": 0.05}, "cost": {"dark": 4, "fire": 3, "wind": 1},
     "gems": 16, "desc": "Хаос усиливает всё — немного."},
    {"id": "dragon_heart", "name": "СЕРДЦЕ ДРАКОНА", "tier": 3, "nature": "fire",
     "buff": {"dmg": 0.14, "hp": 0.05, "blast": 0.08}, "cost": {"fire": 6, "earth": 2, "light": 1},
     "gems": 18, "desc": "Артефакт древних крылатых владык."},
    {"id": "god_frame", "name": "ОБРАЗ БОГА", "tier": 3, "nature": "light",
     "buff": {"armor": 0.08, "hp": 0.08, "energy": 0.08}, "cost": {"light": 6, "wind": 2, "water": 1},
     "gems": 18, "desc": "Совершенная форма бойца."},
    {"id": "world_edge", "name": "КРАЙ МИРА", "tier": 3, "nature": "wind",
     "buff": {"spd": 0.10, "dmg": 0.08, "crit": 0.05}, "cost": {"wind": 6, "dark": 2, "fire": 1},
     "gems": 20, "desc": "Осколок границы реальности."},
]

ART_BY_ID = {a["id"]: a for a in ARTIFACTS}


def can_craft(art, frags, gems):
    for nat, n in art["cost"].items():
        if frags.get(nat, 0) < n:
            return False
    return gems >= art["gems"]


def craft_cost_label(art):
    parts = ["%d×%s" % (n, NATURE_LABEL[nat]) for nat, n in sorted(art["cost"].items())]
    if art["gems"]:
        parts.append("%d СЦ" % art["gems"])
    return " + ".join(parts)


def artifact_buffs(hero_key, equip_ids):
    """Суммарные баффы экипировки. Совпадение природы даёт +7% к каждому баффу."""
    out = {}
    if not equip_ids:
        return out
    nat = hero_nature(hero_key)
    for aid in list(equip_ids)[:ART_SLOTS]:
        art = ART_BY_ID.get(aid)
        if art is None:
            continue
        mult = 1.0 + NATURE_MATCH_BONUS if art["nature"] == nat else 1.0
        for bk, bv in art["buff"].items():
            out[bk] = out.get(bk, 0.0) + bv * mult
    return out
