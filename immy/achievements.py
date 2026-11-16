"""IMMY — достижения: 45 достижений, награда — монеты."""

ACHIEVEMENTS = [
    {"id": "w1", "name": "ПЕРВАЯ КРОВЬ", "desc": "Победи бота 1 раз", "reward": 50, "stat": "wins", "goal": 1},
    {"id": "w5", "name": "УЛИЧНЫЙ БОЕЦ", "desc": "Победи бота 5 раз", "reward": 100, "stat": "wins", "goal": 5},
    {"id": "w15", "name": "ВЕТЕРАН", "desc": "Победи бота 15 раз", "reward": 250, "stat": "wins", "goal": 15},
    {"id": "w30", "name": "МАСТЕР АРЕНЫ", "desc": "Победи бота 30 раз", "reward": 500, "stat": "wins", "goal": 30},
    {"id": "w100", "name": "ЛЕГЕНДА АРЕНЫ", "desc": "Победи бота 100 раз", "reward": 1500, "stat": "wins", "goal": 100},
    {"id": "b1", "name": "УБИЙЦА ГИГАНТОВ", "desc": "Победи 1 босса", "reward": 150, "stat": "bosses", "goal": 1},
    {"id": "b3", "name": "ГРОЗА БОССОВ", "desc": "Победи 3 боссов", "reward": 300, "stat": "bosses", "goal": 3},
    {"id": "b10", "name": "КОЛЛЕКЦИОНЕР ЧЕРЕПОВ", "desc": "Победи 10 боссов", "reward": 700, "stat": "bosses", "goal": 10},
    {"id": "b25", "name": "ИМПЕРАТОР АРЕНЫ", "desc": "Победи 25 боссов", "reward": 2000, "stat": "bosses", "goal": 25},
    {"id": "wv5", "name": "СТОЯК", "desc": "Пройди 5 волн выживания (суммарно)", "reward": 100, "stat": "waves", "goal": 5},
    {"id": "wv15", "name": "ОБОРОНЕЦ", "desc": "Пройди 15 волн выживания (суммарно)", "reward": 250, "stat": "waves", "goal": 15},
    {"id": "wv30", "name": "НЕСЛОМЛЕННЫЙ", "desc": "Пройди 30 волн выживания (суммарно)", "reward": 600, "stat": "waves", "goal": 30},
    {"id": "wv60", "name": "БЕССМЕРТНЫЙ", "desc": "Пройди 60 волн выживания (суммарно)", "reward": 1500, "stat": "waves", "goal": 60},
    {"id": "s5", "name": "НОВОБРАНЕЦ", "desc": "Примени 5 спецприёмов", "reward": 80, "stat": "specials", "goal": 5},
    {"id": "s25", "name": "ЗНАТОК ПРИЁМОВ", "desc": "Примени 25 спецприёмов", "reward": 200, "stat": "specials", "goal": 25},
    {"id": "s100", "name": "ХОЗЯИН ЭНЕРГИИ", "desc": "Примени 100 спецприёмов", "reward": 600, "stat": "specials", "goal": 100},
    {"id": "s300", "name": "ПУСТОТНАЯ ЖИЛА", "desc": "Примени 300 спецприёмов", "reward": 1800, "stat": "specials", "goal": 300},
    {"id": "u1", "name": "ПЕРВОЕ ДОБИВАНИЕ", "desc": "Примени ультимативный навык", "reward": 150, "stat": "ults", "goal": 1},
    {"id": "u10", "name": "КАЗНОВЬ ПО ВЕЛИЧИЮ", "desc": "Примени 10 ультимативных навыков", "reward": 500, "stat": "ults", "goal": 10},
    {"id": "u30", "name": "АНГЕЛ СМЕРТИ", "desc": "Примени 30 ультимативных навыков", "reward": 1200, "stat": "ults", "goal": 30},
    {"id": "f1", "name": "КАЧЕСТВЕННО", "desc": "Выполни качественное добивание", "reward": 200, "stat": "finishers", "goal": 1},
    {"id": "f10", "name": "МЯСНИК", "desc": "Выполни 10 качественных добиваний", "reward": 600, "stat": "finishers", "goal": 10},
    {"id": "f30", "name": "ВЕРШИТЕЛЬ СУДЕБ", "desc": "Выполни 30 качественных добиваний", "reward": 1500, "stat": "finishers", "goal": 30},
    {"id": "p10", "name": "ЖЕЛЕЗНЫЙ КУЛАК", "desc": "Парируй 10 атак", "reward": 100, "stat": "parries", "goal": 10},
    {"id": "p50", "name": "МОНТАЖНИК", "desc": "Парируй 50 атак", "reward": 300, "stat": "parries", "goal": 50},
    {"id": "p200", "name": "АБСОЛЮТНАЯ ЗАЩИТА", "desc": "Парируй 200 атак", "reward": 1000, "stat": "parries", "goal": 200},
    {"id": "c5", "name": "ДВУХХОДОВКА", "desc": "Собери комбо x5", "reward": 100, "stat": "max_combo", "goal": 5},
    {"id": "c8", "name": "СЕРИЙНЫЙ УДАРНИК", "desc": "Собери комбо x8", "reward": 300, "stat": "max_combo", "goal": 8},
    {"id": "c12", "name": "НЕОСТАНОВИМЫЙ", "desc": "Собери комбо x12", "reward": 800, "stat": "max_combo", "goal": 12},
    {"id": "g1k", "name": "ПЕРВАЯ ТЫСЯЧА", "desc": "Заработай 1000 монет", "reward": 100, "stat": "coins_earned", "goal": 1000},
    {"id": "g5k", "name": "СОЛИДНЫЙ КАПИТАЛ", "desc": "Заработай 5000 монет", "reward": 400, "stat": "coins_earned", "goal": 5000},
    {"id": "g20k", "name": "ЗОЛОТАЯ ГРА", "desc": "Заработай 20000 монет", "reward": 1500, "stat": "coins_earned", "goal": 20000},
    {"id": "h1", "name": "НОВЫЙ ЛИЦО", "desc": "Купи 1 героя", "reward": 100, "stat": "buys", "goal": 1},
    {"id": "h5", "name": "ОТРЯД", "desc": "Купи 5 героев", "reward": 300, "stat": "buys", "goal": 5},
    {"id": "h10", "name": "РОСТА", "desc": "Купи 10 героев", "reward": 700, "stat": "buys", "goal": 10},
    {"id": "h15", "name": "ВСЕЗВЁЗДНЫЙ СОСТАВ", "desc": "Купи 15 героев", "reward": 1500, "stat": "buys", "goal": 15},
    {"id": "l5", "name": "ПОДЪЁМ", "desc": "Достигни 5 уровня", "reward": 150, "stat": "plvl", "goal": 5},
    {"id": "l10", "name": "ЗАКАЛЁННЫЙ", "desc": "Достигни 10 уровня", "reward": 400, "stat": "plvl", "goal": 10},
    {"id": "l20", "name": "ВЕРШИНА МАСТЕРСТВА", "desc": "Достигни 20 уровня", "reward": 1200, "stat": "plvl", "goal": 20},
    {"id": "cs5", "name": "ВТОЖДЕНИЕ", "desc": "Пройди 5 ступеней кампаний", "reward": 200, "stat": "camp_stages", "goal": 5},
    {"id": "cs15", "name": "ЗАВОЕВАТЕЛЬ", "desc": "Пройди 15 ступеней кампаний", "reward": 600, "stat": "camp_stages", "goal": 15},
    {"id": "cs37", "name": "ПОКОРИТЕЛЬ МИРОВ", "desc": "Пройди все 37 ступеней кампаний", "reward": 2500, "stat": "camp_stages", "goal": 37},
    {"id": "cm1", "name": "ПРОКЛЯТИЕ СНЯТО", "desc": "Заверши 1 кампанию", "reward": 500, "stat": "camps", "goal": 1},
    {"id": "cm2", "name": "ПЕПЕЛ ПО КОЛЕНО", "desc": "Заверши 2 кампании", "reward": 1000, "stat": "camps", "goal": 2},
    {"id": "cm3", "name": "ВЛАДЫКА ТРОНА", "desc": "Заверши все 3 кампании", "reward": 2500, "stat": "camps", "goal": 3},
]

BY_ID = {a["id"]: a for a in ACHIEVEMENTS}


def check(save):
    stats = save.get("stats", {})
    claimed = save.get("ach", [])
    if not isinstance(claimed, list):
        claimed = []
    claimed_set = set(claimed)
    granted = []
    for a in ACHIEVEMENTS:
        if a["id"] in claimed_set:
            continue
        if stats.get(a["stat"], 0) >= a["goal"]:
            claimed.append(a["id"])
            save["coins"] = save.get("coins", 0) + a["reward"]
            granted.append(a)
    if granted:
        save["ach"] = claimed
    return granted
