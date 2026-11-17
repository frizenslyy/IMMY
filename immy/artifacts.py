"""IMMY — артефакты: 75 крафтов из эссенций (фрагментов) и самоцветов.

Природа артефакта, совпавшая с природой бойца, усиливает все его баффы на +7%.
На бойца надевается до ART_SLOTS артефактов.
"""

from .config import ART_SLOTS, NATURE_MATCH_BONUS
from .heroes import HEROES

NATURES = ("light", "dark", "fire", "earth", "water", "wind",
           "blood", "ice", "metal", "poison", "soul")

NATURE_LABEL = {"light": "СВЕТ", "dark": "ТЬМА", "fire": "ОГОНЬ",
                "earth": "ЗЕМЛЯ", "water": "ВОДА", "wind": "ВЕТЕР"}

NATURE_COLOR = {"light": "#fff2b0", "dark": "#b08aff", "fire": "#ff8c1a",
                "earth": "#c9a15a", "water": "#5ab4ff", "wind": "#bfe9d0"}

NATURE_BY_STYLE = {"flame": "fire", "glow": "light", "hood": "dark",
                   "spike": "earth", "spider": "dark"}

NATURE_LABEL.update({"blood": "КРОВЬ", "ice": "ЛЕД", "metal": "МЕТАЛЛ",
                     "poison": "ЯД", "soul": "ДУША"})
NATURE_COLOR.update({"blood": "#e03328", "ice": "#9fe8ff", "metal": "#b0b0bb",
                     "poison": "#a4f24a", "soul": "#c98aff"})

BPS_LABEL = "РИСУНОК"

BUFF_LABEL = {"dmg": "СИЛА", "armor": "БРОНЯ", "blast": "СТОЙК. К ВЗРЫВУ", "hp": "ЗДОРОВЬЕ",
              "spd": "СКОРОСТЬ", "crit": "КРИТ", "energy": "ЭНЕРГИЯ", "vamp": "ВАМПИРИЗМ",
              "parry": "ПАРИРОВАНИЕ"}


def hero_nature(key):
    st = HEROES[key].get("style", "plain")
    if st in NATURE_BY_STYLE:
        return NATURE_BY_STYLE[st]
    pool = ("water", "wind", "blood", "ice", "metal", "poison", "soul")
    return pool[sum(ord(c) for c in key) % len(pool)]


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


# ===== 8.0: +45 artifacts =====
ARTIFACTS += [
    {"id": "ice_needle", "name": "ЛЕДЯНАЯ ИГЛА", "tier": 1, "nature": "ice",
     "buff": {"spd": 0.03, "crit": 0.02}, "cost": {"ice": 2}, "gems": 0,
     "desc": "Осколок вечной мерзлоты."},
    {"id": "blood_drop", "name": "КАПЛЯ КРОВИ", "tier": 1, "nature": "blood",
     "buff": {"vamp": 0.03}, "cost": {"blood": 2}, "gems": 0,
     "desc": "Капля павшего врага."},
    {"id": "iron_nail", "name": "ЖЕЛЕЗНЫЙ ГВОЗДЬ", "tier": 1, "nature": "metal",
     "buff": {"armor": 0.03}, "cost": {"metal": 2}, "gems": 0,
     "desc": "Гвоздь из брони титана."},
    {"id": "venom_scale", "name": "ЯДОВИТАЯ ЧЕШУЯ", "tier": 1, "nature": "poison",
     "buff": {"dmg": 0.03}, "cost": {"poison": 2}, "gems": 0,
     "desc": "Чешуя причины боли."},
    {"id": "soul_spark", "name": "ИСКРА ДУШИ", "tier": 1, "nature": "soul",
     "buff": {"energy": 0.06}, "cost": {"soul": 2}, "gems": 0,
     "desc": "Мерцающий остаток души."},
    {"id": "frost_core", "name": "ЛЕДЯНОЕ ЯДРО", "tier": 2, "nature": "ice",
     "buff": {"hp": 0.06, "spd": 0.03}, "cost": {"ice": 3, "water": 1}, "gems": 3,
     "desc": "Холод, что питает жизнь."},
    {"id": "blood_amulet", "name": "АМУЛЕТ КРОВИ", "tier": 2, "nature": "blood",
     "buff": {"vamp": 0.05, "dmg": 0.04}, "cost": {"blood": 3, "dark": 1}, "gems": 3,
     "desc": "Бьётся в такт твоему сердцу."},
    {"id": "steel_rib", "name": "СТАЛЬНОЕ РЕБРО", "tier": 2, "nature": "metal",
     "buff": {"armor": 0.05, "dmg": 0.02}, "cost": {"metal": 3, "earth": 1}, "gems": 3,
     "desc": "Выковано кузнецами бездны."},
    {"id": "toxin_gland", "name": "ЯДОВИТАЯ ЖЕЛЕЗА", "tier": 2, "nature": "poison",
     "buff": {"dmg": 0.05}, "cost": {"poison": 3, "water": 1}, "gems": 3,
     "desc": "Секреция древней твари."},
    {"id": "soul_lantern", "name": "ФОНАРЬ ДУШ", "tier": 2, "nature": "soul",
     "buff": {"energy": 0.1}, "cost": {"soul": 3, "dark": 1}, "gems": 3,
     "desc": "Питается чужими судьбами."},
    {"id": "blizzard_fang", "name": "КЛЫК ВЬЮГИ", "tier": 2, "nature": "ice",
     "buff": {"crit": 0.04, "spd": 0.03}, "cost": {"ice": 2, "wind": 2}, "gems": 4,
     "desc": "Бьёт туда, где больно."},
    {"id": "priest_chalice", "name": "ЧАША ЖРЕЦА", "tier": 2, "nature": "blood",
     "buff": {"dmg": 0.05, "vamp": 0.04}, "cost": {"blood": 2, "metal": 2}, "gems": 4,
     "desc": "Никогда не бывает пустой."},
    {"id": "iron_will", "name": "ЖЕЛЕЗНАЯ ВОЛЯ", "tier": 2, "nature": "metal",
     "buff": {"blast": 0.12, "armor": 0.03}, "cost": {"metal": 2, "fire": 2}, "gems": 4,
     "desc": "Не гнётся под ударом."},
    {"id": "venom_edge", "name": "ЯДОВИТАЯ ГРАНЬ", "tier": 2, "nature": "poison",
     "buff": {"crit": 0.03, "dmg": 0.05}, "cost": {"poison": 2, "dark": 2}, "gems": 4,
     "desc": "Клинок, пропитанный ядом."},
    {"id": "echo_shard", "name": "ОСКОЛОК ЭХО ДУШ", "tier": 2, "nature": "soul",
     "buff": {"parry": 0.04, "energy": 0.05}, "cost": {"soul": 2, "light": 2}, "gems": 4,
     "desc": "Отголосок древнего боя."},
    {"id": "glacier_heart", "name": "СЕРДЦЕ ЛЕДНИКА", "tier": 3, "nature": "ice",
     "buff": {"armor": 0.07, "hp": 0.06}, "cost": {"ice": 4, "water": 2}, "gems": 10,
     "desc": "Пульсирует холодом ночи."},
    {"id": "crimson_reaper", "name": "БАГРОВЫЙ ЖНЕЦ", "tier": 3, "nature": "blood",
     "buff": {"dmg": 0.09, "vamp": 0.06}, "cost": {"blood": 4, "dark": 2}, "gems": 10,
     "desc": "Смерть пахнет ржавчиной."},
    {"id": "adamantine_skin", "name": "АДАМАНТОВАЯ КОЖА", "tier": 3, "nature": "metal",
     "buff": {"armor": 0.1}, "cost": {"metal": 5, "earth": 2}, "gems": 10,
     "desc": "Удары высекают лишь искры."},
    {"id": "serpents_kiss", "name": "ПОЦЕЛУЙ ЗМЕИ", "tier": 3, "nature": "poison",
     "buff": {"dmg": 0.08, "crit": 0.04}, "cost": {"poison": 4, "wind": 2}, "gems": 10,
     "desc": "Яд уже в твоих венах."},
    {"id": "psalm_of_souls", "name": "ПСАЛОМ ДУШ", "tier": 3, "nature": "soul",
     "buff": {"energy": 0.12, "parry": 0.04}, "cost": {"soul": 4, "light": 2}, "gems": 10,
     "desc": "Гимн, что копит духов."},
    {"id": "eternal_frost", "name": "ВЕЧНАЯ МЕРЗЛОТА", "tier": 3, "nature": "ice",
     "buff": {"spd": 0.07, "blast": 0.1}, "cost": {"ice": 5, "wind": 2}, "gems": 12,
     "desc": "Зима, что не кончается."},
    {"id": "vampire_grail", "name": "ГРААЛЬ ВАМПИРА", "tier": 3, "nature": "blood",
     "buff": {"vamp": 0.09, "hp": 0.05}, "cost": {"blood": 5, "soul": 1}, "gems": 12,
     "desc": "Кубок первой крови."},
    {"id": "forge_plate", "name": "БРОНЯ ОГНЕННОЙ КУЗНИ", "tier": 3, "nature": "metal",
     "buff": {"armor": 0.07, "dmg": 0.05}, "cost": {"metal": 4, "fire": 2}, "gems": 12,
     "desc": "Раскалена, но держит."},
    {"id": "venom_censer", "name": "ЯДОВИТОЕ КАДИЛО", "tier": 3, "nature": "poison",
     "buff": {"blast": 0.12, "dmg": 0.06}, "cost": {"poison": 4, "water": 2}, "gems": 12,
     "desc": "Дым морит мгновенно."},
    {"id": "requiem_bell", "name": "КОЛОКОЛ РЕКВИЕМА", "tier": 3, "nature": "soul",
     "buff": {"crit": 0.06, "energy": 0.07}, "cost": {"soul": 5, "dark": 1}, "gems": 12,
     "desc": "Звенит за упокой."},
    {"id": "frozen_void_eye", "name": "ОКО МЕРЗЛОЙ ПУСТОТЫ", "tier": 3, "nature": "ice",
     "buff": {"crit": 0.07, "spd": 0.04}, "cost": {"ice": 4, "dark": 3}, "gems": 14,
     "desc": "Видит уязвимости."},
    {"id": "hemomancer_sign", "name": "ЗНАК ГЕМАТОМАНТА", "tier": 3, "nature": "blood",
     "buff": {"dmg": 0.08, "vamp": 0.07}, "cost": {"blood": 6, "metal": 1}, "gems": 14,
     "desc": "Кровь — это валюта."},
    {"id": "mountain_carapace", "name": "ПАНЦИРЬ ГОРЫ", "tier": 3, "nature": "metal",
     "buff": {"armor": 0.11, "hp": 0.06, "spd": -0.02}, "cost": {"metal": 6, "earth": 2}, "gems": 16,
     "desc": "Тяжек, как сама гора."},
    {"id": "plague_herald", "name": "ВЕСТНИК ЧУМЫ", "tier": 3, "nature": "poison",
     "buff": {"dmg": 0.09, "blast": 0.09}, "cost": {"poison": 5, "soul": 3}, "gems": 16,
     "desc": "За ним приходит эпидемия."},
    {"id": "soul_spiral", "name": "СПИРАЛЬ ДУШ", "tier": 3, "nature": "soul",
     "buff": {"energy": 0.14, "crit": 0.05}, "cost": {"soul": 6, "light": 3}, "gems": 18,
     "desc": "Душа кружит, как ворон."},
    {"id": "valfrost_crown", "name": "КОРОНА ВАЛФРОСТА", "tier": 4, "nature": "ice",
     "buff": {"hp": 0.1, "armor": 0.08, "blast": 0.1}, "cost": {"ice": 7, "water": 4}, "gems": 24, "bps": 1,
     "desc": "Венец короля-подо льдом."},
    {"id": "bloodstone_halo", "name": "КРОВАВЫЙ ОРЕОЛ", "tier": 4, "nature": "blood",
     "buff": {"dmg": 0.14, "vamp": 0.1}, "cost": {"blood": 7, "dark": 3}, "gems": 24, "bps": 1,
     "desc": "Ореол павшего полководца."},
    {"id": "executor_core", "name": "ЯДРО ПАЛАЧА", "tier": 4, "nature": "metal",
     "buff": {"dmg": 0.12, "crit": 0.08}, "cost": {"metal": 7, "fire": 4}, "gems": 24, "bps": 1,
     "desc": "Механизм приговорённых."},
    {"id": "king_venom", "name": "ЦЕРЕМОНИАЛЬНЫЙ ЯД", "tier": 4, "nature": "poison",
     "buff": {"dmg": 0.13, "crit": 0.07}, "cost": {"poison": 7, "soul": 3}, "gems": 26, "bps": 1,
     "desc": "Подан в золотом кувшине."},
    {"id": "spirit_engine", "name": "ДВИГАТЕЛЬ ДУШ", "tier": 4, "nature": "soul",
     "buff": {"energy": 0.2, "parry": 0.05}, "cost": {"soul": 7, "light": 4}, "gems": 24, "bps": 1,
     "desc": "Бессмертная машина духа."},
    {"id": "aurora_bulwark", "name": "ЗАЩИТА АВРОРЫ", "tier": 4, "nature": "ice",
     "buff": {"armor": 0.14, "hp": 0.09}, "cost": {"ice": 6, "metal": 3}, "gems": 26, "bps": 1,
     "desc": "Сияние, что поглощает удары."},
    {"id": "abyssal_leech", "name": "ПИЯВКА БЕЗДНЫ", "tier": 4, "nature": "blood",
     "buff": {"vamp": 0.13, "hp": 0.07}, "cost": {"blood": 6, "water": 3}, "gems": 26, "bps": 1,
     "desc": "Жрёт всё, что бьётся."},
    {"id": "titanium_warlord", "name": "ТИТАН ВОЙНЫ", "tier": 4, "nature": "metal",
     "buff": {"armor": 0.1, "dmg": 0.1, "blast": 0.1}, "cost": {"metal": 8, "earth": 3}, "gems": 28, "bps": 1,
     "desc": "Броня поколения сражений."},
    {"id": "plague_lord_seal", "name": "ПЕЧАТЬ ВЛАДЫКИ ЧУМЫ", "tier": 4, "nature": "poison",
     "buff": {"crit": 0.1, "dmg": 0.09, "vamp": 0.05}, "cost": {"poison": 8, "dark": 3}, "gems": 28, "bps": 1,
     "desc": "Печать мора для особых."},
    {"id": "ankh_of_eons", "name": "АНХ ЭПОХ", "tier": 4, "nature": "soul",
     "buff": {"hp": 0.12, "energy": 0.12, "parry": 0.05}, "cost": {"soul": 8, "earth": 3}, "gems": 28, "bps": 1,
     "desc": "Реликвия бесконечности."},
    {"id": "frozen_thunder_heart", "name": "СЕРДЦЕ ЛЕДЯНОЙ ГРОЗЫ", "tier": 4, "nature": "ice",
     "buff": {"spd": 0.1, "crit": 0.08}, "cost": {"ice": 6, "wind": 4}, "gems": 26, "bps": 1,
     "desc": "Гром в ледяной броне."},
    {"id": "crimson_scale", "name": "КРОВАВАЯ ЧЕШУЯ", "tier": 4, "nature": "blood",
     "buff": {"hp": 0.1, "dmg": 0.1, "armor": 0.05}, "cost": {"blood": 6, "fire": 4}, "gems": 28, "bps": 1,
     "desc": "Чешуя алого дракона."},
    {"id": "gods_cogwheel", "name": "ШЕСТЕРНЯ БОГОВ", "tier": 4, "nature": "metal",
     "buff": {"dmg": 0.11, "spd": 0.07, "armor": 0.04}, "cost": {"metal": 6, "light": 4}, "gems": 28, "bps": 1,
     "desc": "Часовой механизм мироздания."},
    {"id": "empress_toxin", "name": "ЯД ИМПЕРАТРИЦЫ", "tier": 4, "nature": "poison",
     "buff": {"dmg": 0.15, "spd": -0.02}, "cost": {"poison": 9, "wind": 2}, "gems": 30, "bps": 1,
     "desc": "Один вкус — один конец."},
    {"id": "soul_of_the_void", "name": "ДУША ПУСТОТЫ", "tier": 4, "nature": "soul",
     "buff": {"crit": 0.09, "energy": 0.15, "vamp": 0.06}, "cost": {"soul": 8, "dark": 4}, "gems": 30, "bps": 1,
     "desc": "Осколок изначальной тьмы."},
]

ART_BY_ID = {a["id"]: a for a in ARTIFACTS}


def can_craft(art, frags, gems, bps=None):
    for nat, n in art["cost"].items():
        if frags.get(nat, 0) < n:
            return False
    need_bps = art.get("bps", 0)
    if need_bps and bps is not None and bps.get(art["id"], 0) < need_bps:
        return False
    return gems >= art["gems"]


def craft_cost_label(art, bps=None):
    parts = ["%d×%s" % (n, NATURE_LABEL[nat]) for nat, n in sorted(art["cost"].items())]
    need_bps = art.get("bps", 0)
    if need_bps:
        have = bps.get(art["id"], 0) if bps else 0
        parts.append("%s %d/%d" % (BPS_LABEL, have, need_bps))
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
