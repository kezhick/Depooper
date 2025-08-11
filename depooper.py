#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Симулятор человека‑совы, который хочет стать человеком-жаворонком.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Цветовой вывод ---
def color_text(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'bold': '\033[1m',
        'reset': '\033[0m',
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

@dataclass
class Person:
    """Основной объект – персонаж."""
    name: str = "Артем"
    # Состояние бодрости и сна (0–100)
    alertness: int = 50          # насколько он бодрый сегодня
    sleep_need: float = 8.0      # сколько часов нужен для нормального функционирования

    # Вес, здоровье и привычки
    weight_kg: float = 105.0
    health_score: int = 100     # от 0 до 200 (чем выше – лучше)

    coffee_cups_today: int = 0
    cigarettes_smoked_today: int = 0

    # Флаги привычек; True означает «привычка есть».
    has_coffee_habit: bool = True
    has_overeat_habit: bool = True
    has_smoking_habit: bool = True

    # Параметры, влияющие на бодрость и сон.
    coffee_benefit: int = 10     # +% бодрости за чашку кофе (было 15)
    smoke_penalty: int = -7      # –% здоровья при курении (было -10)
    overeating_cost: float = 0.3   # сколько часов сна теряется из-за переедания (было 0.5)
    
    # Флаги событий дня
    overeaten_today: bool = False  # переедал ли сегодня

    # Журнал событий (лог)
    event_log: List[str] = field(default_factory=list)

    # Прогресс и мета
    days_elapsed: int = 0
    goal_streak_days: int = 0
    goal_days_target: int = 90
    difficulty_mode: str = "normal"
    quit_attempt_cooldown_days: int = 7
    last_quit_attempt_day_by_habit: Dict[str, int] = field(
        default_factory=lambda: {"coffee": -999, "smoking": -999, "overeating": -999}
    )
    # Время суток (минуты от начала дня)
    time_minutes: int = 8 * 60  # стартуем в 08:00
    # Локации и деньги
    current_location: str = "home"  # home | work | gym | park
    rubles: int = 1000
    # Кулдаун случайных встреч
    encounter_cooldown_min: int = 45
    last_encounter_minute: int = -10_000
    # Работа и выплаты
    job_daily_wage: int = 2000
    wage_accrued: int = 0
    bonus_accrued: int = 0
    worked_today: bool = False
    work_productive_today: bool = False
    work_minutes_today: int = 0
    job_bonus_eligibility_today: bool = True
    job_late_today: bool = False
    job_warnings: int = 0
    employed: bool = True
    fired_reason: str = ""
    # Микрозайм
    loan_principal: int = 0
    loan_weekly_interest_pct: int = 20
    # RPG: характеристики и прогресс
    morale: int = 50  # 0..100
    strength: int = 1
    agility: int = 1
    intelligence: int = 1
    charisma: int = 1
    level: int = 1
    xp: int = 0
    # Бытовая техника
    has_coffee_machine: bool = False
    # Бытовые платежи
    utilities_weekly: int = 1500
    # Социальное
    has_girlfriend: bool = False
    # Квесты
    quests: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "main": {
            "title": "Стать жаворонком",
            "desc": "Держи серию 90 дней без вредных привычек",
            "status": "Скрыто",
            "progress": 0,
            "target": 90,
            "reward": {"xp": 300, "rub": 2000},
        },
        "work_reports": {
            "title": "Рабочая рутина",
            "desc": "Собери 3 отчёта",
            "status": "Скрыто",
            "progress": 0,
            "target": 3,
            "reward": {"xp": 80, "rub": 600},
        },
        "buy_coffeemachine": {
            "title": "Кофе дома",
            "desc": "Купить кофемашину",
            "status": "Скрыто",
            "progress": 0,
            "target": 1,
            "reward": {"xp": 40},
        },
        "work_features": {
            "title": "Новые фичи",
            "desc": "Реализуй 5 задач",
            "status": "Скрыто",
            "progress": 0,
            "target": 5,
            "reward": {"xp": 150, "rub": 800},
        },
        "work_incidents": {
            "title": "Дежурство героя",
            "desc": "Разрули 3 инцидента",
            "status": "Скрыто",
            "progress": 0,
            "target": 3,
            "reward": {"xp": 150},
        },
        "work_presentations": {
            "title": "Слово за тобой",
            "desc": "Проведи 2 демо/встречи с клиентом",
            "status": "Скрыто",
            "progress": 0,
            "target": 2,
            "reward": {"xp": 120, "rub": 500},
        },
        "money_crunch": {
            "title": "Деньги на исходе",
            "desc": "Герой попал в ситуевину, ему срочно нужно рожать деньги!",
            "status": "Скрыто",
            "progress": 0,
            "target": 1,
            "reward": {"xp": 50},
        },
    })

    # --- Логгер событий ---
    def log_event(self, message: str, color: Optional[str] = None) -> None:
        """Сохраняем событие в журнал и дублируем в stdout.

        color аргумент оставлен для совместимости, но сейчас не используется в GUI.
        """
        self.event_log.append(message)
        print(message)

    # Функция, вызываемая в начале каждого дня.
    def reset_daily_counters(self):
        self.coffee_cups_today = 0
        self.cigarettes_smoked_today = 0
        self.overeaten_today = False
        self.calories_today = 0  # суммарные калории за день
        self.night_binge_protection_today = False  # защита от ночных жоров (супер-еда)

    # Проверка и корректировка состояния после всех действий за день.
    def end_of_day_update(self):
        """Обновляем сон, здоровье, вес."""
        # Сон: если бодрость < порог – персонаж спит меньше нужного времени
        if self.alertness < 30:
            sleep_hours = max(0.5, self.sleep_need * (self.alertness / 50))
        else:
            sleep_hours = self.sleep_need

        # Влияние переедания на сон (если сегодня переедал)
        if self.overeaten_today:
            sleep_hours -= self.overeating_cost

        # Восстановление здоровья, если не было вредных привычек за день
        if self.coffee_cups_today == 0 and self.cigarettes_smoked_today == 0 and (not self.has_overeat_habit or self.weight_kg == 70.0):
            self.health_score = min(200, self.health_score + 5)

        # Прогресс цели 90 дней без привычек
        successful_day = (
            self.coffee_cups_today == 0 and
            self.cigarettes_smoked_today == 0 and
            not self.overeaten_today
        )
        if successful_day:
            self.goal_streak_days += 1
        else:
            self.goal_streak_days = 0
        # Прогресс по главному квесту
        try:
            # Показать основной квест только когда серия >= 1
            if self.goal_streak_days >= 1 and self.quests["main"]["status"] == "Скрыто":
                self.quests["main"]["status"] = "В процессе"
            self.quests["main"]["progress"] = int(self.goal_streak_days)
            if self.quests["main"]["status"] != "Завершено" and self.goal_streak_days >= int(self.quests["main"]["target"]):
                self.complete_quest("main")
        except Exception:
            pass

        # Работа: итоги дня, если трудоустроен
        if self.employed:
            if self.worked_today:
                # Лишение премии при опоздании/недоработке было учтено во время смены
                self.wage_accrued += self.job_daily_wage
                if self.work_productive_today and self.job_bonus_eligibility_today:
                    self.bonus_accrued += 500
            else:
                # Прогул: предупреждение и штраф
                self.job_warnings += 1
                fine = 300
                self.change_money(-fine)
                self.change_morale(-6)
                self.log_event(f"Прогул. Предупреждение #{self.job_warnings}. Штраф {fine} ₽ и мораль -6.")
                if self.job_warnings >= 3:
                    self.employed = False
                    self.fired_reason = "Систематические прогулы/опоздания"
                    self.log_event("Вас уволили за систематические нарушения.")
        # Сброс флагов рабочего дня
        self.worked_today = False
        self.work_productive_today = False

        # Переход к следующему дню – сброс бодрости и сна до нормального уровня
        self.alertness = min(100, max(0, self.alertness))
        if sleep_hours < 0:                  # если сон отрицательный → здоровье падает
            self.health_score -= int(abs(sleep_hours) * 5)
        else:
            self.sleep_need = max(4.0, min(self.sleep_need + (sleep_hours - 8), 12))

        # Ночные жоры: шанс, если калорий много и нет защиты
        try:
            import random as _r
            if not self.night_binge_protection_today:
                # базовый шанс 0.2, +0.1 если калорий > 3000
                chance = 0.2 + (0.1 if self.calories_today > 3000 else 0)
                if _r.random() < chance and self.has_overeat_habit:
                    extra_cal = _r.randint(400, 1200)
                    self.calories_today += extra_cal
                    self.weight_kg = max(40.0, self.weight_kg + (extra_cal / 7700.0))
                    self.change_money(-200)
                    self.overeaten_today = True
                    self.log_event(f"Ночной жор на {extra_cal} ккал. Вес теперь {self.weight_kg:.1f} кг.")
        except Exception:
            pass

        # Счетчик дней
        self.days_elapsed += 1
        # Сброс времени дня к утру
        self.time_minutes = 8 * 60
        # Сброс рабочих флагов на новый день
        self.worked_today = False
        self.work_productive_today = False
        self.work_minutes_today = 0
        self.job_bonus_eligibility_today = True
        self.job_late_today = False

        # Недельные выплаты и проценты по займу каждые 7 дней
        if self.days_elapsed % 7 == 0:
            # Буст выплат: фикс + премия + бонусы за РПГ
            rpg_bonus = int(max(0, (self.charisma - 1)) * 100 + max(0, (self.level - 1)) * 50)
            payout = self.wage_accrued + self.bonus_accrued + 7500 + 1500 + rpg_bonus
            if payout > 0:
                self.rubles += payout
                self.log_event(f"Выплата за неделю: ставка {self.wage_accrued} ₽ + премии {self.bonus_accrued} ₽ + 7500 фикс + 1500 премия + РПГ-бонус {rpg_bonus} ₽ = {payout} ₽.")
                self.wage_accrued = 0
                self.bonus_accrued = 0
            # Коммунальные платежи
            if self.utilities_weekly > 0:
                self.rubles -= self.utilities_weekly
                self.log_event(f"Оплачены коммунальные услуги: −{self.utilities_weekly} ₽.")
            # Начисление процентов по микрозайму
            if self.loan_principal > 0:
                import math as _m
                interest = int(_m.ceil(self.loan_principal * self.loan_weekly_interest_pct / 100.0))
                self.loan_principal += interest
                self.log_event(f"Начислены проценты по микрозайму: +{interest} ₽. Долг: {self.loan_principal} ₽.")
            # Супер-события недели (редкие неожиданности)
            import random as _r
            if _r.random() < 0.15:
                event = _r.choice(["phone_repair", "relative_funeral", "relative_wedding"])
                if event == "phone_repair":
                    cost = 3500
                    self.rubles -= cost
                    self.log_event(f"Неожиданность: Сломался телефон. Ремонт −{cost} ₽.")
                elif event == "relative_funeral":
                    cost = 2000
                    self.rubles -= cost
                    self.change_morale(-10)
                    self.log_event(f"Горе в семье. Расходы −{cost} ₽, мораль −10.")
                else:
                    cost = 5000
                    self.rubles -= cost
                    self.change_morale(6)
                    self.log_event(f"Свадьба у родственников. Подарки −{cost} ₽, мораль +6.")

    # --- Время суток ---
    def advance_time(self, minutes: int) -> None:
        minutes = max(0, int(minutes))
        self.time_minutes = max(0, min(23 * 60 + 59, self.time_minutes + minutes))

    def compute_travel_minutes(self, mode: str, base_minutes: int) -> int:
        """Скорректировать время пути с учётом РПГ-характеристик и веса.
        mode: 'walk' | 'bus' | 'taxi'
        """
        minutes = int(max(1, base_minutes))
        if mode == 'walk':
            agility_bonus = max(0, (self.agility - 1) * 2)
            weight_penalty = 0
            if self.weight_kg >= 110:
                weight_penalty = 6
            elif self.weight_kg >= 100:
                weight_penalty = 3
            minutes = max(1, minutes - agility_bonus + weight_penalty)
        # bus/taxi без изменений времени, но можно в будущем влиять харизмой/интеллектом на цену/маршрут
        return minutes

    def format_time(self) -> str:
        h = (self.time_minutes // 60) % 24
        m = self.time_minutes % 60
        return f"{h:02d}:{m:02d}"

    # --- RPG утилиты ---
    def gain_xp(self, amount: int) -> None:
        amount = max(0, int(amount))
        if amount == 0:
            return
        self.xp += amount
        # Уровень каждые 100*level XP
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1
            # На апе случайно +1 к одной из характеристик и мораль +5
            import random as _r
            attr = _r.choice(['strength', 'agility', 'intelligence', 'charisma'])
            setattr(self, attr, getattr(self, attr) + 1)
            self.morale = min(100, self.morale + 5)
            self.log_event(f"Новый уровень {self.level}! +1 к {attr} и мораль +5.")

    def change_morale(self, delta: int) -> None:
        self.morale = max(0, min(100, self.morale + int(delta)))

    # --- Деньги ---
    def change_money(self, delta: int) -> None:
        amount = int(delta)
        # Небольшие бонусы/скидки от РПГ: харизма улучшает сделки на 1% за уровень >1 (до 10%)
        if amount != 0 and amount < 0:
            discount_pct = min(10, max(0, self.charisma - 1))
            amount = int(round(amount * (100 - discount_pct) / 100.0))
        self.rubles += amount
        self.log_event(f"Баланс: {self.rubles} ₽")
        # Авто-квест на минусовый баланс
        try:
            if self.rubles <= -5000 and self.quests.get('money_crunch', {}).get('status') == 'Скрыто':
                self.quests['money_crunch']['status'] = 'В процессе'
                self.log_event("Квест: Герой попал в ситуевину, ему срочно нужно рожать деньги!")
        except Exception:
            pass

    def _normalize_habit_key(self, habit_name: str) -> str:
        return {
            'coffee': 'coffee',
            'smoking': 'smoking',
            'overeating': 'overeat',
        }.get(habit_name, habit_name)

    def days_until_quit_available(self, habit_name: str) -> int:
        key = habit_name
        last_day = self.last_quit_attempt_day_by_habit.get(key, -999)
        days_passed = self.days_elapsed - last_day
        remaining = self.quit_attempt_cooldown_days - days_passed
        return max(0, remaining)

    def can_attempt_to_kick_habit(self, habit_name: str) -> (bool, str):
        """Проверка условий попытки избавиться от привычки.
        Возвращает (ok, reason_if_not_ok).
        """
        normalized_attr = self._normalize_habit_key(habit_name)
        has_habit_flag = getattr(self, f"has_{normalized_attr}_habit", False)
        if not has_habit_flag:
            return False, "Эту привычку уже удалось бросить."

        # Условия по использованию сегодня
        if habit_name == 'coffee' and self.coffee_cups_today > 0:
            return False, "Сегодня пил кофе. Попробуй завтра."
        if habit_name == 'smoking' and self.cigarettes_smoked_today > 0:
            return False, "Сегодня курил. Попробуй завтра."
        if habit_name == 'overeating' and self.overeaten_today:
            return False, "Сегодня переедал. Попробуй завтра."

        # Пороговые значения состояния
        if self.alertness < 60:
            return False, "Слишком низкая бодрость (<60). Выспись."
        if self.health_score < 90:
            return False, "Слишком низкое здоровье (<90). Улучши состояние."

        # Кулдаун по дням
        if self.days_until_quit_available(habit_name) > 0:
            return False, f"Попытка будет доступна через {self.days_until_quit_available(habit_name)} дн."

        return True, ""

    def attempt_to_kick_habit(self, habit_name: str):
        """Попытка избавиться от привычки — редкая и сложная.
        Учитывает кулдаун, состояние и сложность.
        """
        normalized = self._normalize_habit_key(habit_name)

        ok, reason = self.can_attempt_to_kick_habit(habit_name)
        if not ok:
            self.log_event(f"[{self.name}] Не готов к попытке бросить '{habit_name}': {reason}")
            return False

        base_chance_map = {'coffee': 0.15, 'smoking': 0.10, 'overeating': 0.12}
        chance = base_chance_map.get(habit_name, 0.0)

        # Модификаторы: хорошее состояние и серия чистых дней помогают
        if self.alertness >= 80:
            chance += 0.05
        if self.health_score >= 140:
            chance += 0.05
        if self.goal_streak_days >= 7:
            chance += 0.07

        if self.difficulty_mode.lower() == 'hardcore':
            chance -= 0.05

        chance = max(0.02, min(0.6, chance))

        roll = random.random()
        self.last_quit_attempt_day_by_habit[habit_name] = self.days_elapsed
        if roll < chance:
            setattr(self, f"has_{normalized}_habit", False)
            self.log_event(
                f"[{self.name}] Собрался с силами и бросил привычку '{habit_name}'! (шанс {int(chance*100)}%)"
            )
            return True
        else:
            # Цена неудачной попытки
            self.alertness = max(0, self.alertness - 10)
            self.log_event(
                f"[{self.name}] Не удалось бросить '{habit_name}' (шанс {int(chance*100)}%). Отдохни и попробуй позже."
            )
            return False

    def drink_coffee(self, quality: str = "instant") -> bool:
        """Выпить кофе с выбором качества.
        quality: 'instant' | 'ground' | 'premium'
        Возвращает True, если получилось выпить.
        """
        if not self.has_coffee_habit:
            self.log_event("[Внимание] У тебя уже нет кофе‑привычки!")
            return False

        quality_key = (quality or "instant").lower()
        # Базовые параметры напитков
        # benefit основан на self.coffee_benefit
        options = {
            "instant": {"cost": 100, "benefit": self.coffee_benefit, "time_min": 10, "needs_machine": False, "label": "растворимый"},
            "ground":  {"cost": 150, "benefit": self.coffee_benefit + 4, "time_min": 10, "needs_machine": True,  "label": "молотый"},
            "premium": {"cost": 300, "benefit": self.coffee_benefit + 8, "time_min": 12, "needs_machine": True,  "label": "супер премиум"},
        }
        opt = options.get(quality_key, options["instant"]) 
        if opt["needs_machine"] and not self.has_coffee_machine:
            self.log_event("[Внимание] Нужна кофемашина для такого кофе.")
            return False

        self.coffee_cups_today += 1
        self.alertness = min(100, self.alertness + int(opt["benefit"]))
        self.change_money(-int(opt["cost"]))
        self.log_event(f"[{self.name}] Выпил {opt['label']} кофе (−{opt['cost']} ₽). Бодрость: {self.alertness}.")
        self.advance_time(int(opt["time_min"]))
        self.gain_xp(2)
        return True

    def consume_coffee(self):
        """Старое API: по умолчанию — растворимый."""
        return self.drink_coffee("instant")

    def buy_coffee_machine(self, price: int = 7990) -> bool:
        if self.has_coffee_machine:
            self.log_event("Кофемашина уже есть.")
            return False
        self.change_money(-int(price))
        self.has_coffee_machine = True
        self.log_event(f"Купил кофемашину за {price} ₽.")
        try:
            self.increment_quest("buy_coffeemachine", 1)
        except Exception:
            pass
        return True

    def smoke(self):
        if not self.has_smoking_habit:
            self.log_event("[Внимание] У тебя уже нет привычки курить!")
            return
        self.cigarettes_smoked_today += 1
        self.health_score = max(0, self.health_score + self.smoke_penalty)
        self.alertness = max(0, self.alertness - 5)   # небольшое снижение бодрости после сигареты
        self.change_money(-20)
        self.log_event(f"[{self.name}] Курил (−20 ₽). Здоровье: {self.health_score}.")
        self.advance_time(7)
        self.change_morale(-3)

    def eat(self):
        """Старое API — сбалансированная еда по умолчанию."""
        return self.eat_food("balanced")

    def eat_food(self, food_type: str = "fast") -> bool:
        """Еда с калориями и эффектами: fast | balanced | super.
        - fast: 500–1500 ккал, риск ночного жора
        - balanced: 800 ккал
        - super: >=500 ккал, даёт защиту от ночного жора
        Возвращает True, если удалось поесть.
        """
        key = (food_type or "fast").lower()
        # Определим параметры
        # super требует дома
        options = {
            "fast": {"cost": 150, "time_min": 20, "label": "фастфуд", "requires_home": False},
            "balanced": {"cost": 300, "time_min": 40, "label": "сбалансированная еда", "requires_home": False},
            "super": {"cost": 500, "time_min": 50, "label": "супер полезная еда", "requires_home": True},
        }
        opt = options.get(key, options["fast"])
        if opt["requires_home"] and self.current_location != "home":
            self.log_event("Супер-полезную еду лучше готовить дома.")
            return False
        # денежный вопрос будет обработан change_money (учтёт скидки)
        self.change_money(-int(opt["cost"]))
        # калории и эффекты
        calories = 0
        if key == "fast":
            calories = random.randint(500, 1500)
            self.health_score = max(0, self.health_score - 1)  # не самая полезная
            self.alertness = min(100, self.alertness + 2)
        elif key == "balanced":
            calories = 800
            self.health_score = min(200, self.health_score + 3)
            self.alertness = min(100, self.alertness + 3)
        else:  # super
            calories = random.randint(500, 900)
            self.health_score = min(200, self.health_score + 7)
            self.alertness = min(100, self.alertness + 4)
            self.night_binge_protection_today = True

        self.calories_today += calories
        # Перевод калорий в вес: ~7700 ккал = 1 кг → грубо 0.1 кг за каждые 770 ккал
        self.weight_kg = max(40.0, self.weight_kg + (calories / 7700.0))
        # Переедание: если за день > 2500 ккал, помечаем
        if self.calories_today > 2500:
            self.overeaten_today = True
        # Риск ночного жора, если много фастфуда: обработаем в end_of_day_update, если нет защиты
        self.advance_time(int(opt["time_min"]))
        self.gain_xp(1)
        self.log_event(f"[{self.name}] Съел: {opt['label']} (−{opt['cost']} ₽, {calories} ккал). Зд: {self.health_score}, Бодр: {self.alertness}, Вес: {self.weight_kg:.1f} кг.")
        return True

    def sleep(self, hours: float):
        """Сон восполняет бодрость и немного здоровье. Переедание ухудшает качество сна."""
        hours = max(0.0, hours)
        penalty = 0.8 if self.overeaten_today else 0.0
        effective_hours = max(0.0, hours - penalty)

        alert_gain = int(min(100 - self.alertness, effective_hours * 10))  # ~10 бодрости за час
        health_gain = int(max(0, effective_hours * (2 if not self.has_smoking_habit else 1)))

        self.alertness = min(100, self.alertness + alert_gain)
        self.health_score = min(200, self.health_score + health_gain)
        # Регулярный сон чуть снижает потребность во сне
        self.sleep_need = max(4.0, min(12.0, self.sleep_need - 0.2))

        self.log_event(
            f"[{self.name}] Сон {hours:.1f} ч. (эффективно {effective_hours:.1f}) → Бодрость +{alert_gain}, Здоровье +{health_gain}."
        )
        self.advance_time(int(hours * 60))
        return alert_gain, health_gain

    # --- Тренировки ---
    def train_gym(self):
        # Скидка по харизме уже учтётся в change_money
        self.change_money(-300)
        health_gain = 8
        alert_gain = 5
        weight_loss = 0.5 if self.has_overeat_habit else 0.7
        self.health_score = min(200, self.health_score + health_gain)
        self.alertness = min(100, self.alertness + alert_gain)
        self.weight_kg = max(40.0, self.weight_kg - weight_loss)
        # Сила ускоряет восстановление сна
        self.sleep_need = max(4.0, min(12.0, self.sleep_need - (0.1 + 0.02 * max(0, self.strength - 1))))
        self.advance_time(90)
        self.log_event(f"Тренировка в качалке: здоровье +{health_gain}, бодрость +{alert_gain}, вес −{weight_loss:.1f} кг (−300 ₽).")
        self.strength += 1
        self.gain_xp(12)

    def train_park(self):
        health_gain = 4
        alert_gain = 4
        weight_loss = 0.3 if self.has_overeat_habit else 0.4
        self.health_score = min(200, self.health_score + health_gain)
        self.alertness = min(100, self.alertness + alert_gain)
        self.weight_kg = max(40.0, self.weight_kg - weight_loss)
        # Ловкость ускоряет время тренировки на площадке
        self.advance_time(max(30, 60 - 3 * max(0, self.agility - 1)))
        self.log_event(f"Тренировка на спортплощадке: здоровье +{health_gain}, бодрость +{alert_gain}, вес −{weight_loss:.1f} кг.")
        self.agility += 1
        self.gain_xp(9)

    def read_in_library(self):
        # Чтение повышает интеллект, иногда поднимает мораль
        self.advance_time(60)
        self.intelligence += 1
        self.gain_xp(10)
        self.log_event("Почитал в библиотеке: интеллект +1.")
        # Забавное событие: журнал с голыми бабами
        import random as _r
        if _r.random() < 0.25:
            self.change_morale(12)
            self.log_event("Нашёл журнал с голыми бабами. Мораль +12.")
        else:
            self.change_morale(4)
            self.log_event("Нашёл смешной комикс. Мораль +4.")

    # --- Встречи ---
    def is_encounter_available(self) -> bool:
        return (self.time_minutes - self.last_encounter_minute) >= self.encounter_cooldown_min

    def roll_dice(self, sides: int = 20) -> int:
        """Бросок кубика как в DnD (по умолчанию D20)."""
        sides = max(2, int(sides))
        value = random.randint(1, sides)
        self.log_event(f"Бросок D{sides}: {value}")
        return value

    # --- Баланс и сложность ---
    def apply_difficulty(self, mode: str = "normal") -> None:
        """Применяем пресет сложности."""
        m = mode.lower()
        self.difficulty_mode = m
        if m == "hardcore":
            self.coffee_benefit = 6
            self.smoke_penalty = -12
            self.overeating_cost = 0.6
        else:
            self.coffee_benefit = 10
            self.smoke_penalty = -7
            self.overeating_cost = 0.3

    # --- Случайные встречи ---
    def random_encounter(self, mode: str = "normal", apply: bool = True, forced_type: Optional[str] = None) -> Dict[str, str]:
        """Случайное событие: алкаш, гопники, дворник и т.д.
        Если apply=False, возвращает сценарий без применения эффектов.
        Можно указать forced_type.
        Возвращает словарь: {'type', 'message'}
        """
        hardcore = mode.lower() == "hardcore"
        encounter_type = forced_type or random.choice(["drunk", "gopnik", "janitor"])
        msg = ""
        if encounter_type == "drunk":
            delta_health = - (12 if hardcore else 7) - random.randint(0, 5)
            delta_alert = - (12 if hardcore else 8)
            msg = f"Подозрительный алкаш пристал к тебе. Здоровье {delta_health}, бодрость {delta_alert}."
            if apply:
                self.health_score = max(0, self.health_score + delta_health)
                self.alertness = max(0, self.alertness + delta_alert)
                self.log_event(f"Случайная встреча: {msg}")
        elif encounter_type == "gopnik":
            delta_health = - (15 if hardcore else 8) - random.randint(0, 6)
            delta_alert = - (10 if hardcore else 6)
            # Шанс вырубили
            knocked = random.random() < (0.25 if hardcore else 0.15)
            base_msg = f"Гопники докопались. Здоровье {delta_health}, бодрость {delta_alert}."
            msg = ("Вас вырубили. " + base_msg) if knocked else base_msg
            if apply:
                self.health_score = max(0, self.health_score + delta_health)
                self.alertness = max(0, self.alertness + delta_alert)
                if self.has_smoking_habit and random.random() < (0.6 if hardcore else 0.35):
                    self.smoke()
                else:
                    self.log_event(f"Случайная встреча: {msg}")
            if apply:
                self.last_encounter_minute = self.time_minutes
            return {"type": encounter_type, "message": msg, "knockout": knocked}
        else:  # janitor
            if self.has_smoking_habit and random.random() < (0.5 if hardcore else 0.3):
                delta_alert = - (6 if hardcore else 4)
                msg = f"Дворник сделал замечание за окурки. Бодрость {delta_alert}."
                if apply:
                    self.alertness = max(0, self.alertness + delta_alert)
                    self.log_event(f"Случайная встреча: {msg}")
            else:
                bonus = 3 if hardcore else 5
                msg = f"Дворник пожелал доброго утра и подбодрил. Здоровье +{bonus}."
                if apply:
                    self.health_score = min(200, self.health_score + bonus)
                    self.log_event(f"Случайная встреча: {msg}")

        if apply:
            self.last_encounter_minute = self.time_minutes
        return {"type": encounter_type, "message": msg, "knockout": False}

    # --- Квесты ---
    def increment_quest(self, key: str, amount: int = 1) -> None:
        if key not in self.quests:
            return
        q = self.quests[key]
        if q.get("status") == "Завершено":
            return
        q["progress"] = int(q.get("progress", 0)) + int(amount)
        target = int(q.get("target", 0))
        if target and q["progress"] >= target:
            self.complete_quest(key)

    def complete_quest(self, key: str) -> None:
        q = self.quests.get(key)
        if not q or q.get("status") == "Завершено":
            return
        q["status"] = "Завершено"
        reward = q.get("reward", {})
        rub = int(reward.get("rub", 0))
        xp = int(reward.get("xp", 0))
        if rub:
            self.rubles += rub
        if xp:
            self.gain_xp(xp)
        self.log_event(f"Квест завершён: {q.get('title', key)}. Награда: {rub} ₽, {xp} XP.")

    # --- Микрозайм ---
    def take_microloan(self, amount: int) -> None:
        amount = max(0, int(amount))
        if amount <= 0:
            return
        self.loan_principal += amount
        self.rubles += amount
        self.log_event(f"Получен микрозайм {amount} ₽. Долг: {self.loan_principal} ₽.")

    def repay_loan(self, amount: int) -> None:
        pay = max(0, int(amount))
        if pay <= 0:
            return
        pay = min(pay, self.rubles)
        if pay == 0:
            self.log_event("Недостаточно средств для погашения займа.")
            return
        self.rubles -= pay
        prev = self.loan_principal
        self.loan_principal = max(0, self.loan_principal - pay)
        self.log_event(f"Погашено по займу {prev - self.loan_principal} ₽. Остаток долга: {self.loan_principal} ₽.")

    # --- Подработка ---
    def do_construction_shift(self) -> None:
        # 6 часов, оплата 1200 ₽, риск дебаффа/баффа
        self.advance_time(360)
        pay = 1200
        self.rubles += pay
        import random as _r
        outcome = _r.random()
        if outcome < 0.2:
            # Травма
            self.health_score = max(0, self.health_score - 12)
            self.change_morale(-8)
            self.log_event(f"Подработка на стройке: травма. Здоровье -12, мораль -8. Оплата {pay} ₽.")
        elif outcome < 0.5:
            # Тяжело, но полезно
            self.strength += 1
            self.health_score = max(0, self.health_score - 4)
            self.log_event(f"Подработка на стройке: тяжело, но полезно. Сила +1, здоровье -4. Оплата {pay} ₽.")
        else:
            # Отлично потрудился
            self.strength += 1
            self.change_morale(6)
            self.log_event(f"Подработка на стройке: всё прошло отлично. Сила +1, мораль +6. Оплата {pay} ₽.")
        self.gain_xp(15)

    # --- Поиск работы ---
    def find_new_job(self) -> None:
        # Поиск занимает 4 часа; если повезёт — новая работа
        self.advance_time(240)
        import random as _r
        if _r.random() < 0.7:
            self.employed = True
            self.job_warnings = 0
            self.fired_reason = ""
            # Возможно другая ставка
            self.job_daily_wage = max(1600, min(2600, self.job_daily_wage + _r.randint(-200, 200)))
            self.log_event(f"Нашёл новую работу! Дневная ставка: {self.job_daily_wage} ₽.")
        else:
            self.log_event("Поиск работы не увенчался успехом. Попробуй позже.")

    def status(self):
        """Печатаем текущее состояние с цветами."""
        print("\n--- Состояние персонажа ---")
        print(f"Имя:          {self.name}")
        # Цвет бодрости
        if self.alertness >= 70:
            alert_col = 'blue'
        elif self.alertness >= 35:
            alert_col = 'yellow'
        else:
            alert_col = 'red'
        print(f"Bодрость:     {color_text(f'{self.alertness:.1f}/100', alert_col)}")
        print(f"Сон (нужен):  {self.sleep_need:.2f} ч.")
        # Цвет веса не меняем
        print(f"Вес:          {self.weight_kg:.1f} кг")
        # Цвет здоровья
        if self.health_score >= 140:
            health_col = 'green'
        elif self.health_score >= 70:
            health_col = 'yellow'
        else:
            health_col = 'red'
        print(f"Здоровье:    {color_text(f'{self.health_score}/200', health_col)}")
        print("Привычки:")
        for h in ['coffee', 'overeat', 'smoking']:
            flag = getattr(self, f'has_{h}_habit')
            col = 'green' if not flag else 'red'
            print(f"  - {h.capitalize()}: {color_text('Нет' if not flag else 'Да', col)}")


def main():
    hero = Person(name="Артем")
    day_counter = 1
    tutorial_active = True
    tutorial_step = 0

    tutorial_steps = [
        ("Добро пожаловать в симулятор! Ты — человек-" +
         "сова, который хочет стать жаворонком.\n\n" +
         "Твоя задача — избавиться от вредных привычек и улучшить здоровье.\n" +
         "Давай начнем с чашки кофе! Выбери действие 1.", "1"),
        ("Теперь попробуй покурить (2) или съесть еду (3).", ["2", "3"]),
        ("Попробуй избавиться от одной из привычек (4, 5 или 6).", ["4", "5", "6"]),
        ("Теперь заверши день (0).", "0"),
        ("Обучение завершено! Теперь играй как хочешь. Удачи!", None)
    ]

    while True:
        print("\n\n============================================")
        print(f"День #{day_counter}")
        hero.status()

        actions = {
            "1": ("Выпить кофе", hero.consume_coffee),
            "2": ("Курить сигарету", hero.smoke),
            "3": ("Съесть еду (переедать?)", hero.eat),
            "4": ("Пробовать избавиться от привычки кофе", lambda: hero.attempt_to_kick_habit("coffee")),
            "5": ("Пробовать избавиться от курения", lambda: hero.attempt_to_kick_habit("smoking")),
            "6": ("Пробовать избавить от переедания", lambda: hero.attempt_to_kick_habit("overeating")),
            "0": ("Завершить день (переход в сон)", None)
        }

        for key, (desc, _) in actions.items():
            print(color_text(f"{key}. {desc}", 'cyan'))

        if tutorial_active and tutorial_step < len(tutorial_steps):
            print(color_text("\n[ОБУЧЕНИЕ]", 'yellow'))
            print(color_text(tutorial_steps[tutorial_step][0], 'yellow'))

        choice = input("\nВыберите действие: ").strip()

        if tutorial_active and tutorial_step < len(tutorial_steps):
            valid = tutorial_steps[tutorial_step][1]
            if valid is None or (isinstance(valid, list) and choice in valid) or (choice == valid):
                tutorial_step += 1
                if tutorial_step == len(tutorial_steps):
                    tutorial_active = False
            else:
                print("\n[Подсказка] Пожалуйста, выбери действие, указанное в обучении!")
                continue

        if choice == '0':
            hero.end_of_day_update()
            day_counter += 1
            hero.reset_daily_counters()
            continue

        action_func = actions.get(choice, (None, None))[1]
        if action_func:
            action_func()
        else:
            print(color_text("Неверный выбор. Попробуйте снова.", 'red'))

        if hero.health_score <= 0 or hero.weight_kg > 120:
            print(color_text("\n!!! Симулятор окончен: герой не смог выжить в этом мире привычек !!!", 'bold'))
            break


if __name__ == "__main__":
    main()
