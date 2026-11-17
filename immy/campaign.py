"""IMMY — кампании: 38 кампаний для новичков и профи, награды: герои, монеты, самоцветы."""

CAMPAIGNS = [
    {"name": "АРЕНЫ НОВИЧКА", "desc": "Первые шаги бойца: 10 лёгких ступеней.",
     "stages": 10, "base": 1, "step": 1.3, "reward": {"type": "coins"}, "color": "#c9a07a"},
    {"name": "КРОВАВЫЙ ЗАМОК", "desc": "Проклятый замок гулей: 10 ступеней ужаса.",
     "stages": 10, "base": 2, "step": 1.6, "reward": {"type": "hero", "hero": "GHOULEY"}, "color": "#8aff8a"},
    {"name": "ЛЕДЯНОЙ ПРЕДЕЛ", "desc": "Вечная мерзлота: 10 ступеней холода.",
     "stages": 10, "base": 3, "step": 1.5, "reward": {"type": "gems"}, "color": "#9fe0ff"},
    {"name": "ПЕПЕЛЬНЫЕ ПУСТОШИ", "desc": "Выжженные земли пепла: 12 ступеней ярости.",
     "stages": 12, "base": 4, "step": 1.8, "reward": {"type": "hero", "hero": "ASHY"}, "color": "#e8c9a0"},
    {"name": "ЯДОВИТЫЕ ТОПИ", "desc": "Гнилые болота: 12 ступеней заразы.",
     "stages": 12, "base": 6, "step": 1.7, "reward": {"type": "coins"}, "color": "#7ad12a"},
    {"name": "ПЕЩЕРЫ ЭХА", "desc": "Кристальные глубины: 12 ступеней тьмы.",
     "stages": 12, "base": 8, "step": 1.8, "reward": {"type": "gems"}, "color": "#b06aff"},
    {"name": "НЕБЕСНЫЙ ЗАЛ", "desc": "Арена над облаками: 13 ступеней бури.",
     "stages": 13, "base": 10, "step": 1.9, "reward": {"type": "coins"}, "color": "#fff2b0"},
    {"name": "ТРОН ПЛАМЕНИ", "desc": "Цитадель владыки огня: 15 ступеней ада.",
     "stages": 15, "base": 8, "step": 2.0, "reward": {"type": "hero", "hero": "PYROY"}, "color": "#ff8c1a"},
    {"name": "ПУСТОТА МЕЖДУ МИРАМИ", "desc": "Разлом реальности: 13 ступеней бездны.",
     "stages": 13, "base": 12, "step": 2.0, "reward": {"type": "gems"}, "color": "#9a5cff"},
    {"name": "КУЗНЯ БОГОВ", "desc": "Наковальня титанов: 14 ступеней жара.",
     "stages": 14, "base": 14, "step": 2.1, "reward": {"type": "coins"}, "color": "#ffcf6a"},
    {"name": "БЕЗДНА", "desc": "Царство мёртвых душ: 14 ступеней отчаяния.",
     "stages": 14, "base": 16, "step": 2.2, "reward": {"type": "hero", "hero": "NECROMANCERY"}, "color": "#4ad16a"},
    {"name": "ЗВЁЗДНЫЙ РАЗЛОМ", "desc": "Хаос созвездий: 15 ступеней безумия.",
     "stages": 15, "base": 18, "step": 2.3, "reward": {"type": "hero", "hero": "CHAOSY"}, "color": "#e04aff"},
    {"name": "ПОСЛЕДНИЙ РАУНД", "desc": "Испытание для профи: 15 ступеней богов.",
     "stages": 15, "base": 20, "step": 2.5, "reward": {"type": "hero", "hero": "TITANY"}, "color": "#ff2a8a"},
    {"name": "ОГНЕННЫЕ ВРАТА", "desc": "Врата в пламенный предел: 12 ступеней.",
     "stages": 12, "base": 24, "step": 2.4, "reward": {"type": "gems"}, "color": "#ff5a1a"},
    {"name": "КОРРОЗИЯ", "desc": "Ржавчина и металл: 12 ступеней.",
     "stages": 12, "base": 26, "step": 2.4, "reward": {"type": "coins"}, "color": "#9aa4ae"},
    {"name": "НЕДРА ГЛУБИН", "desc": "Темницы без дна: 13 ступеней.",
     "stages": 13, "base": 28, "step": 2.5, "reward": {"type": "gems"}, "color": "#4ac9ff"},
    {"name": "ЛЕГИОН ТЕНЕЙ", "desc": "Армия теней: 13 ступеней.",
     "stages": 13, "base": 30, "step": 2.6, "reward": {"type": "coins"}, "color": "#5a646e"},
    {"name": "ГРОЗОВОЙ ФРОНТ", "desc": "Буря не умолкает: 14 ступеней.",
     "stages": 14, "base": 33, "step": 2.6, "reward": {"type": "gems"}, "color": "#5ab4d9"},
    {"name": "ЦИТАДЕЛЬ БУРИ", "desc": "Обитель ветров: 14 ступеней.",
     "stages": 14, "base": 36, "step": 2.7, "reward": {"type": "coins"}, "color": "#bfe9ff"},
    {"name": "ПРОКЛЯТЫЕ ЗВЕЗДЫ", "desc": "Звезды мертвцов: 15 ступеней.",
     "stages": 15, "base": 39, "step": 2.8, "reward": {"type": "gems"}, "color": "#e04aff"},
    {"name": "КОЛЕСО ПУСТОТЫ", "desc": "Вращение бездны: 15 ступеней.",
     "stages": 15, "base": 42, "step": 2.9, "reward": {"type": "coins"}, "color": "#9a5cff"},
    {"name": "ТРОН ВСЕЛЕННОЙ", "desc": "Престол миров: 16 ступеней.",
     "stages": 16, "base": 46, "step": 3.0, "reward": {"type": "gems"}, "color": "#ffc400"},
    {"name": "ИСПЫТАНИЕ БЕССМЕРТНЫХ", "desc": "Лишь боги выйдут: 16 ступеней.",
     "stages": 16, "base": 50, "step": 3.2, "reward": {"type": "coins"}, "color": "#fff2b0"},
]


# ===== 8.0: +15 campaigns =====
CAMPAIGNS += [
    {"name": "РУННЫЕ ШАХТЫ", "desc": "Шахты архивариуса: 12 ступеней рун.",
     "stages": 12, "base": 54, "step": 3.2, "reward": {"type": "hero", "hero": "RUNEY"}, "color": "#ffe95a"},
    {"name": "ИСКРА НЕБЕС", "desc": "Молнии сияют: 12 ступеней.",
     "stages": 12, "base": 57, "step": 3.2, "reward": {"type": "gems"}, "color": "#5ab4ff"},
    {"name": "СЕРДЦЕ ВУЛКАНА", "desc": "Магма и молнии: 13 ступеней.",
     "stages": 13, "base": 60, "step": 3.3, "reward": {"type": "coins"}, "color": "#ff5a1a"},
    {"name": "ТЕНИ ЖНЕЦА", "desc": "Клинки осколков: 13 ступеней.",
     "stages": 13, "base": 63, "step": 3.3, "reward": {"type": "hero", "hero": "SHARDY"}, "color": "#9fe0ff"},
    {"name": "ЛЕДЯНОЙ ТРОН", "desc": "Окова вечного льда: 14 ступеней.",
     "stages": 14, "base": 66, "step": 3.4, "reward": {"type": "gems"}, "color": "#dff3ff"},
    {"name": "КЛАДБИЩЕ ТЕНЕЙ", "desc": "Тени не спят: 14 ступеней.",
     "stages": 14, "base": 69, "step": 3.4, "reward": {"type": "coins"}, "color": "#5a646e"},
    {"name": "ГНЕЗДО ВЫРОДКОВ", "desc": "Трясина гнилого роя: 14 ступеней.",
     "stages": 14, "base": 72, "step": 3.5, "reward": {"type": "coins"}, "color": "#8a8a2a"},
    {"name": "ПОРОГ ВЕЧНОСТИ", "desc": "Империя пепла: 15 ступеней.",
     "stages": 15, "base": 75, "step": 3.5, "reward": {"type": "hero", "hero": "EMPERORY"}, "color": "#d99a2a"},
    {"name": "СУД НЕБЕС", "desc": "Небесное приговор: 15 ступеней.",
     "stages": 15, "base": 78, "step": 3.5, "reward": {"type": "gems"}, "color": "#fff2b0"},
    {"name": "ШЛЕМ РАГНАРЁКА", "desc": "Битва богов: 15 ступеней.",
     "stages": 15, "base": 81, "step": 3.6, "reward": {"type": "coins"}, "color": "#ff5a1a"},
    {"name": "ВЕЧНОЕ ЗАТМЕНИЕ", "desc": "Тень солнца: 16 ступеней.",
     "stages": 16, "base": 84, "step": 3.6, "reward": {"type": "hero", "hero": "ECLIPSY"}, "color": "#7a4ae0"},
    {"name": "ХРЕБЕТ АБИССА", "desc": "Голос бездны: 16 ступеней.",
     "stages": 16, "base": 87, "step": 3.6, "reward": {"type": "gems"}, "color": "#6a4ad9"},
    {"name": "СИЯНИЕ СЕРАФИМА", "desc": "Небесный страж: 16 ступеней.",
     "stages": 16, "base": 90, "step": 3.7, "reward": {"type": "hero", "hero": "SERAPHY"}, "color": "#ffffff"},
    {"name": "УЗЕЛ ПУСТОТЫ", "desc": "Грань реальности: 17 ступеней.",
     "stages": 17, "base": 94, "step": 3.7, "reward": {"type": "coins"}, "color": "#9a5cff"},
    {"name": "ПОСЛЕДНИЙ ШАГ БОГА", "desc": "Финал всех дорог: 18 ступеней.",
     "stages": 18, "base": 98, "step": 3.7, "reward": {"type": "gems"}, "color": "#ffc400"},
]

UNLOCK_PLVL = 1


def stage_level(camp_idx, stage):
    c = CAMPAIGNS[camp_idx]
    return max(1, int(round(c["base"] + (stage - 1) * c["step"])))


def is_final(camp_idx, stage):
    return stage >= CAMPAIGNS[camp_idx]["stages"]


def unlocked(camp_idx, save):
    if camp_idx == 0:
        return save.get("plvl", 1) >= UNLOCK_PLVL
    cleared = save.get("camp", {}).get(str(camp_idx - 1), {}).get("done", False)
    return cleared


def camp_progress(save, camp_idx):
    return save.get("camp", {}).get(str(camp_idx), {}).get("stage", 0)


def camp_done(save, camp_idx):
    return save.get("camp", {}).get(str(camp_idx), {}).get("done", False)


def reward_label(camp):
    r = camp["reward"]
    if r["type"] == "hero":
        return "НАГРАДА: ГЕРОЙ " + r["hero"]
    if r["type"] == "gems":
        return "НАГРАДА: САМОЦВЕТЫ"
    return "НАГРАДА: МОНЕТЫ"


def first_clear_coins(stage):
    return 60 + stage * 15


def first_clear_gems(stage):
    return 2 + stage // 2


def replay_reward(stage):
    return 15 + stage * 4
