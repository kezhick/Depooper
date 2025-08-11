#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI-версия симулятора с простой 2.5D (изометрической) сценой и кнопками действий.

Зависимости: pygame
Установка: pip install pygame
Запуск: python depooper_gui.py
"""

import sys
import math
import json
import pygame
from typing import Callable, List, Tuple, Dict

try:
    # Используем игровую логику из консольной версии
    from depooper import Person
except Exception:  # pragma: no cover
    print("Не удалось импортировать Person из depooper.py. Убедитесь, что файл находится рядом.")
    raise


# --- Настройки окна ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60

# --- Цвета ---
COLOR_BG = (22, 24, 28)
COLOR_PANEL = (32, 36, 42)
COLOR_TEXT = (230, 230, 230)
COLOR_ACCENT = (60, 170, 250)
COLOR_ACCENT_HOVER = (90, 195, 255)
COLOR_WARN = (255, 80, 80)
COLOR_OK = (90, 200, 120)
COLOR_YELLOW = (240, 200, 80)
COLOR_OVERLAY_BG = (0, 0, 0, 180)
COLOR_PANEL_DARK = (28, 30, 36)

# --- Изометрическая сетка ---
GRID_W, GRID_H = 6, 6
TILE_W, TILE_H = 96, 48  # ширина/высота ромба
GRID_ORIGIN = (WINDOW_WIDTH // 2, 180)  # центр сцены


def grid_to_iso(x: int, y: int) -> Tuple[int, int]:
    iso_x = (x - y) * (TILE_W // 2) + GRID_ORIGIN[0]
    iso_y = (x + y) * (TILE_H // 2) + GRID_ORIGIN[1]
    return iso_x, iso_y


def draw_tile(surface: pygame.Surface, gx: int, gy: int, color: Tuple[int, int, int]):
    cx, cy = grid_to_iso(gx, gy)
    points = [
        (cx, cy - TILE_H // 2),
        (cx + TILE_W // 2, cy),
        (cx, cy + TILE_H // 2),
        (cx - TILE_W // 2, cy),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (0, 0, 0), points, 1)


def draw_room(surface: pygame.Surface):
    # Пол
    for y in range(GRID_H):
        for x in range(GRID_W):
            base = 70 + ((x + y) % 2) * 10
            draw_tile(surface, x, y, (base, base + 15, base))

    # Простая мебель: кровать, стол, плита (прямоугольники поверх тайлов)
    def draw_iso_box(gx: int, gy: int, w: int, h: int, color: Tuple[int, int, int]):
        # рисуем верх прямоугольника в изометрии, как набор тайлов
        for dy in range(h):
            for dx in range(w):
                draw_tile(surface, gx + dx, gy + dy, color)

    # Кровать в левом верхнем углу
    draw_iso_box(0, 0, 2, 1, (110, 85, 85))
    # Стол в центре
    draw_iso_box(2, 2, 1, 1, (95, 110, 130))
    # Плита справа
    draw_iso_box(4, 1, 1, 1, (120, 105, 90))

    # Локации: дом, работа, качалка, площадка
    # Отметим их плитками/цветами
    # Дом (0..1,4..5)
    draw_tile(surface, 0, 4, (120, 120, 160))
    surface.blit(pygame.font.SysFont("Segoe UI", 16).render("Дом", True, (0,0,0)), (grid_to_iso(0, 4)[0]-20, grid_to_iso(0,4)[1]-28))
    # Работа (5,0)
    draw_tile(surface, 5, 0, (160, 120, 120))
    surface.blit(pygame.font.SysFont("Segoe UI", 16).render("Работа", True, (0,0,0)), (grid_to_iso(5, 0)[0]-28, grid_to_iso(5,0)[1]-28))
    # Качалка (5,5)
    draw_tile(surface, 5, 5, (120, 160, 120))
    surface.blit(pygame.font.SysFont("Segoe UI", 16).render("Качалка", True, (0,0,0)), (grid_to_iso(5, 5)[0]-32, grid_to_iso(5,5)[1]-28))
    # Площадка (0,5)
    draw_tile(surface, 0, 5, (120, 160, 160))
    surface.blit(pygame.font.SysFont("Segoe UI", 16).render("Площадка", True, (0,0,0)), (grid_to_iso(0, 5)[0]-40, grid_to_iso(0,5)[1]-28))


class Button:
    def __init__(self, rect: pygame.Rect, label: str, on_click: Callable[[], None]):
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.enabled = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: Tuple[int, int]):
        hovered = self.rect.collidepoint(mouse_pos)
        color = COLOR_ACCENT_HOVER if hovered and self.enabled else COLOR_ACCENT
        if not self.enabled:
            color = (90, 90, 90)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        label_surf = font.render(self.label, True, (0, 0, 0))
        surface.blit(label_surf, label_surf.get_rect(center=self.rect.center))

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()


def draw_status(surface: pygame.Surface, font: pygame.font.Font, hero: Person, day_counter: int, difficulty_mode: str):
    panel = pygame.Rect(20, WINDOW_HEIGHT - 200, WINDOW_WIDTH - 40, 180)
    pygame.draw.rect(surface, COLOR_PANEL, panel, border_radius=12)

    # Заголовок
    title = font.render(f"День #{day_counter}  |  Время: {hero.format_time()}  |  Режим: {('Хардкор' if difficulty_mode=='hardcore' else 'Обычный')}", True, COLOR_TEXT)
    surface.blit(title, (panel.x + 16, panel.y + 12))

    # Параметры
    def draw_bar(x: int, y: int, w: int, h: int, value: float, max_value: float, color: Tuple[int, int, int]):
        pygame.draw.rect(surface, (55, 60, 66), (x, y, w, h), border_radius=6)
        pct = max(0.0, min(1.0, value / max_value))
        pygame.draw.rect(surface, color, (x, y, int(w * pct), h), border_radius=6)

    # Бодрость
    alert_col = COLOR_YELLOW if 35 <= hero.alertness < 70 else (COLOR_OK if hero.alertness >= 70 else COLOR_WARN)
    draw_bar(panel.x + 16, panel.y + 50, 300, 20, hero.alertness, 100, alert_col)
    surface.blit(font.render(f"Бодрость: {hero.alertness}/100", True, COLOR_TEXT), (panel.x + 16, panel.y + 76))

    # Здоровье
    if hero.health_score >= 140:
        health_col = COLOR_OK
    elif hero.health_score >= 70:
        health_col = COLOR_YELLOW
    else:
        health_col = COLOR_WARN
    draw_bar(panel.x + 16 + 330, panel.y + 50, 300, 20, hero.health_score, 200, health_col)
    surface.blit(font.render(f"Здоровье: {hero.health_score}/200", True, COLOR_TEXT), (panel.x + 346, panel.y + 76))

    # Вес, сон, деньги и калории
    surface.blit(font.render(f"Вес: {hero.weight_kg:.1f} кг", True, COLOR_TEXT), (panel.x + 16 + 660, panel.y + 50))
    surface.blit(font.render(f"Сон (нужен): {hero.sleep_need:.1f} ч.", True, COLOR_TEXT), (panel.x + 16 + 660, panel.y + 76))
    surface.blit(font.render(f"Деньги: {hero.rubles} ₽", True, COLOR_TEXT), (panel.x + 16 + 660, panel.y + 102))
    # Новые показатели питания
    if hasattr(hero, 'calories_today'):
        surface.blit(font.render(f"Калории: {hero.calories_today} ккал", True, COLOR_TEXT), (panel.x + 16 + 660, panel.y + 128))

    # Привычки
    habits_text = []
    habits_text.append(f"Кофе: {'Да' if hero.has_coffee_habit else 'Нет'}")
    habits_text.append(f"Переедание: {'Да' if hero.has_overeat_habit else 'Нет'}")
    habits_text.append(f"Курение: {'Да' if hero.has_smoking_habit else 'Нет'}")
    habits_surf = font.render(" | ".join(habits_text), True, COLOR_TEXT)
    surface.blit(habits_surf, (panel.x + 16, panel.y + 110))

    # Цель 90 дней
    goal_text = f"Цель 90 дней: серия {hero.goal_streak_days}/{hero.goal_days_target}"
    surface.blit(font.render(goal_text, True, COLOR_TEXT), (panel.x + 16 + 330, panel.y + 110))

    # Локация
    loc_map = {"home": "Дом", "work": "Работа", "gym": "Качалка", "park": "Площадка"}
    surface.blit(font.render(f"Локация: {loc_map.get(hero.current_location, hero.current_location)}", True, COLOR_TEXT), (panel.x + 16, panel.y + 140))
    # RPG-панель
    rpg = f"Ур.{hero.level}  XP {hero.xp}/{hero.level*100}  Сила {hero.strength}  Ловк {hero.agility}  Инт {hero.intelligence}  Хар {hero.charisma}  Мораль {hero.morale}"
    surface.blit(font.render(rpg, True, COLOR_TEXT), (panel.x + 16 + 330, panel.y + 140))


def draw_hero(surface: pygame.Surface, gx: int, gy: int):
    # Рисуем персонажа как кружок в центре тайла
    cx, cy = grid_to_iso(gx, gy)
    pygame.draw.circle(surface, (230, 235, 245), (cx, cy - 8), 12)
    pygame.draw.circle(surface, (30, 35, 45), (cx, cy - 8), 12, 2)


def draw_tutorial(surface: pygame.Surface, font: pygame.font.Font, text: str):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    surface.blit(overlay, (0, 0))
    lines = text.split("\n")
    y = 80
    for line in lines:
        surf = font.render(line, True, (250, 240, 180))
        rect = surf.get_rect(center=(WINDOW_WIDTH // 2, y))
        surface.blit(surf, rect)
        y += 28


def draw_mini_log(surface: pygame.Surface, font: pygame.font.Font, hero: Person, max_lines: int = 7):
    # Панель в правом верхнем углу для последних событий
    pad = 12
    panel_w = 480
    panel_h = 24 + max_lines * 22 + pad
    panel = pygame.Rect(WINDOW_WIDTH - panel_w - 20, 16, panel_w, panel_h)
    pygame.draw.rect(surface, COLOR_PANEL, panel, border_radius=10)
    title = font.render("Последние события", True, COLOR_TEXT)
    surface.blit(title, (panel.x + 12, panel.y + 8))
    # Список
    y = panel.y + 34
    for msg in hero.event_log[-max_lines:]:
        text_surf = font.render(msg, True, (210, 210, 210))
        surface.blit(text_surf, (panel.x + 12, y))
        y += 22


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    for w in words:
        test = (" ".join(current + [w])).strip()
        if font.size(test)[0] <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def build_action_groups(hero: Person,
                        end_day_cb: Callable[[], None],
                        toggle_logs_cb: Callable[[], None],
                        toggle_diff_cb: Callable[[], None],
                        random_enc_cb: Callable[[], None],
                        difficulty_mode: str,
                        sleep1_cb: Callable[[], None],
                        start_work_cb: Callable[[], None],
                        open_travel_cb: Callable[[], None],
                        save_cb: Callable[[], None],
                        load_cb: Callable[[], None],
                        open_coffee_dialog_cb: Callable[[], None],
                        open_food_dialog_cb: Callable[[], None],
                        buy_coffee_machine_cb: Callable[[], None],
                        open_loan_dialog_cb: Callable[[], None],
                        open_repay_dialog_cb: Callable[[], None]) -> Dict[str, List[Tuple[str, Callable[[], None], bool]]]:
    groups: Dict[str, List[Tuple[str, Callable[[], None], bool]]] = {
        "Привычки": [],
        "Сон": [],
        "Действия": [],
        "Система": [],
    }

    # Хелпер: оборачиваем действие шансом фоновой встречи
    def with_bg_events(cb: Callable[[], None]) -> Callable[[], None]:
        def _wrapped():
            cb()
            # Малый шанс фоновой встречи после любого действия
            import random as _r
            chance = 0.25 if difficulty_mode == 'hardcore' else 0.15
            if _r.random() < chance:
                random_enc_cb()
            # Случайный сдвиг времени для действий вне сна уже учтен в моделях, здесь ничего не делаем
        return _wrapped

    # Базовые действия привычек
    groups["Привычки"].append(("Кофе (выбрать)", open_coffee_dialog_cb, True))
    groups["Привычки"].append(("Курить", with_bg_events(lambda: hero.smoke()), True))
    groups["Привычки"].append(("Еда (выбрать)", open_food_dialog_cb, True))

    # Попытки бросить с учётом кулдауна и условий
    for habit_key, base_label in [("coffee", "Бросить кофе"), ("smoking", "Бросить курить"), ("overeating", "Бросить переедание")]:
        ok, reason = hero.can_attempt_to_kick_habit(habit_key)
        remaining = hero.days_until_quit_available(habit_key)
        label = base_label
        if not ok:
            # Показать кратко статус
            if remaining > 0:
                label = f"{base_label} ({remaining} дн)"
            else:
                # укоротим типовые причины
                short = "недоступно"
                if "бодрость" in reason:
                    short = "бодрость <60"
                elif "здоровье" in reason:
                    short = "здоровье <90"
                elif "сегодня" in reason.lower():
                    short = "завтра"
                label = f"{base_label} [{short}]"

        def make_attempt(hk: str) -> Callable[[], None]:
            return lambda: hero.attempt_to_kick_habit(hk)

        groups["Привычки"].append((label, with_bg_events(make_attempt(habit_key)), ok))

    # Сон
    groups["Сон"].append(("Поспать 1 ч", with_bg_events(sleep1_cb), True))

    # Действия
    # Действия: зависят от локации
    if hero.current_location == 'work':
        groups["Действия"].append(("Начать смену", start_work_cb, True))
    else:
        groups["Действия"].append(("Переместиться", open_travel_cb, True))
    # Контекстные действия по локации
    loc = hero.current_location
    if loc == 'gym':
        groups["Действия"].append(("Тренировка в качалке", with_bg_events(lambda: hero.train_gym()), True))
    elif loc == 'park':
        groups["Действия"].append(("Тренировка на площадке", with_bg_events(lambda: hero.train_park()), True))
    elif loc == 'home':
        groups["Действия"].append(("Почитать (библиотека)", with_bg_events(lambda: hero.read_in_library()), True))
        if not hero.has_coffee_machine:
            groups["Действия"].append(("Купить кофемашину (7990 ₽)", buy_coffee_machine_cb, True))
    # Перемещения вынесены в отдельный оверлей «Навигация»

    # Система
    groups["Система"].append((f"Сложность: {'Хардкор' if difficulty_mode=='hardcore' else 'Обычный'}", toggle_diff_cb, True))
    groups["Система"].append(("Журнал событий", toggle_logs_cb, True))
    groups["Система"].append(("Сохранить", save_cb, True))
    groups["Система"].append(("Загрузить", load_cb, True))
    # Микрозаймы
    loan_label = f"Взять микрозайм (долг {hero.loan_principal} ₽)"
    repay_label = "Погасить займ"
    groups["Система"].append((loan_label, open_loan_dialog_cb, True))
    groups["Система"].append((repay_label, open_repay_dialog_cb, True))
    groups["Система"].append(("Завершить день", end_day_cb, True))

    return groups


def layout_buttons(actions: List[Tuple[str, Callable[[], None]]], font: pygame.font.Font, bottom_margin: int = 0) -> Tuple[List[pygame.Rect], int]:
    """Считаем сетку кнопок, чтобы они красиво переносились по рядам."""
    gap = 12
    max_rows = 3
    max_cols = 5
    usable_width = WINDOW_WIDTH - 40
    # Оценим минимальную ширину кнопки по тексту
    label_widths = [font.size(label)[0] + 28 for (label, _) in actions]
    min_btn_w = min(max(label_widths), 220)  # не слишком широкие
    cols = min(max(3, usable_width // (min_btn_w + gap)), max_cols, len(actions))
    rows = (len(actions) + cols - 1) // cols
    rows = min(rows, max_rows)
    # Пересчитаем ширину/высоту
    btn_w = (usable_width - gap * (cols - 1)) // cols
    btn_h = 44
    total_h = rows * btn_h + (rows - 1) * gap
    # Начальная позиция так, чтобы блок кнопок был над панелью статуса и над нижним отступом (селектора групп)
    y_start = WINDOW_HEIGHT - 220 - total_h - bottom_margin
    x_start = 20
    rects: List[pygame.Rect] = []
    for i in range(len(actions)):
        r = i // cols
        c = i % cols
        x = x_start + c * (btn_w + gap)
        y = y_start + r * (btn_h + gap)
        rects.append(pygame.Rect(x, y, btn_w, btn_h))
    return rects, total_h


def main():
    pygame.init()
    pygame.display.set_caption("Сова → Жаворонок (GUI 2.5D)")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Segoe UI", 20)

    hero = Person(name="Артем")
    difficulty_mode = "normal"  # or 'hardcore'
    day_counter = 1

    # Позиция героя на сетке (старт дома)
    hero_gx, hero_gy = 0, 4

    # Журнал/лог – отдельное меню (вкладка)
    active_tab = "game"  # 'game' | 'log'
    log_scroll = 0
    new_events_flag = False

    # Стартовое меню (выбор сложности и пропуск обучения)
    start_menu_active = True
    skip_tutorial = False
    selected_hero_name = "Артем"
    end_day_latch = False

    # Туториал
    tutorial_active = True
    tutorial_step = 0
    tutorial_steps: List[Tuple[str, List[str]]] = [
        ("Добро пожаловать!\nНажми кнопку 'Выпить кофе'", ["Выпить кофе"]),
        ("Теперь попробуй 'Курить' или 'Еда'", ["Курить", "Еда"]),
        ("Попробуй бросить одну привычку\n(кнопки Бросить ...)", ["Бросить кофе", "Бросить курить", "Бросить переедание"]),
        ("Заверши день", ["Завершить день"]),
    ]

    last_clicked_index = None
    active_actions_group = "Привычки"

    def end_day():
        nonlocal day_counter
        hero.end_of_day_update()
        hero.reset_daily_counters()
        day_counter += 1

    def toggle_logs():
        nonlocal active_tab, new_events_flag
        active_tab = "log" if active_tab == "game" else "game"
        if active_tab == "log":
            new_events_flag = False

    def toggle_difficulty():
        nonlocal difficulty_mode
        difficulty_mode = "hardcore" if difficulty_mode == "normal" else "normal"
        hero.apply_difficulty(difficulty_mode)
        hero.log_event(f"Переключен режим: {'Хардкор' if difficulty_mode=='hardcore' else 'Обычный'}")

    def do_random_encounter():
        nonlocal new_events_flag
        if work_overlay.get('active'):
            return
        if hero.is_encounter_available():
            enc = hero.random_encounter(difficulty_mode, apply=False)
            # Включим оверлей встречи
            encounter_overlay['active'] = True
            encounter_overlay['data'] = enc
            new_events_flag = True

    def sleep_1h():
        nonlocal new_events_flag
        hero.sleep(1.0)
        # Если в последней встрече гопники вырубили героя — позволим отоспаться 1 час без последствий
        new_events_flag = True

    # Завершение дня = сон 8 часов
    def combined_end_day_sleep():
        nonlocal new_events_flag, day_counter
        hero.sleep(8.0)
        hero.end_of_day_update()
        hero.reset_daily_counters()
        day_counter += 1
        new_events_flag = True

    def sleep_8h():
        # Используем объединённое действие
        combined_end_day_sleep()

    # Мини-игра: Работа
    work_overlay = {
        'active': False,
        'events_left': 0,
        'focus': 50,
        'stress': 0,
        'message': '',
        'choices': [],  # List[Tuple[label, callback]]
        'choice_rects': [],
    }

    # Оверлей случайной встречи
    encounter_overlay = {
        'active': False,
        'data': None,  # {type, message}
    }

    # Оверлей перемещений (Навигация)
    travel_overlay = {
        'active': False,
        'options': [],  # List[(label, callback)]
        'option_rects': [],
        'title': 'Навигация',
    }

    # Универсальный диалоговый оверлей (выбор кофе/еды/прочее)
    dialog_overlay = {
        'active': False,
        'title': 'Диалог',
        'message': '',
        'options': [],  # List[(label, callback)]
        'option_rects': [],
        'panel_size': (620, 360),
    }

    # Диалоги выбора кофе/еды и покупка техники
    def open_coffee_dialog():
        dialog_overlay['active'] = True
        dialog_overlay['title'] = 'Кофе — выбор качества'
        dialog_overlay['message'] = 'Для молотого/премиум нужна кофемашина.'
        dialog_overlay['options'] = []
        dialog_overlay['option_rects'] = []
        def make_drink(kind: str):
            def _cb():
                hero.drink_coffee(kind)
                dialog_overlay['active'] = False
            return _cb
        dialog_overlay['options'].append(("Растворимый (100 ₽)", make_drink('instant')))
        dialog_overlay['options'].append(("Молотый (150 ₽)" + (" (нужна кофемашина)" if not hero.has_coffee_machine else ""), make_drink('ground')))
        dialog_overlay['options'].append(("Супер премиум (300 ₽)" + (" (нужна кофемашина)" if not hero.has_coffee_machine else ""), make_drink('premium')))

    def open_food_dialog(from_break: bool = False, break_fill: int = 60):
        dialog_overlay['active'] = True
        dialog_overlay['title'] = 'Выбор еды'
        dialog_overlay['message'] = 'Выберите тип питания.'
        dialog_overlay['options'] = []
        dialog_overlay['option_rects'] = []
        def make_eat(kind: str, base_minutes: int):
            def _cb():
                hero.eat_food(kind)
                if from_break:
                    leftover = max(0, break_fill - base_minutes)
                    hero.advance_time(leftover)
                    work_overlay['in_break'] = False
                    work_overlay['break_left'] = 0
                    _next_work_event()
                dialog_overlay['active'] = False
            return _cb
        dialog_overlay['options'].append(("Фастфуд (150 ₽)", make_eat('fast', 20)))
        dialog_overlay['options'].append(("Сбалансированная (300 ₽)", make_eat('balanced', 40)))
        dialog_overlay['options'].append(("Супер полезная (500 ₽, дома)", make_eat('super', 50)))

    def buy_coffee_machine():
        hero.buy_coffee_machine()

    # Диалоги микрозайма
    def open_loan_dialog():
        dialog_overlay['active'] = True
        dialog_overlay['title'] = 'Микрозайм'
        dialog_overlay['message'] = f"Текущий долг: {hero.loan_principal} ₽. Возьми займ?"
        dialog_overlay['options'] = []
        dialog_overlay['option_rects'] = []
        def make_take(amount: int):
            def _cb():
                hero.take_microloan(amount)
                dialog_overlay['active'] = False
            return _cb
        dialog_overlay['options'].append(("Взять 2000 ₽", make_take(2000)))
        dialog_overlay['options'].append(("Взять 5000 ₽", make_take(5000)))
        dialog_overlay['options'].append(("Отмена", lambda: dialog_overlay.update({'active': False})))

    def open_repay_dialog():
        dialog_overlay['active'] = True
        dialog_overlay['title'] = 'Погашение займа'
        dialog_overlay['message'] = f"Текущий долг: {hero.loan_principal} ₽. Сколько погасить?"
        dialog_overlay['options'] = []
        dialog_overlay['option_rects'] = []
        def make_pay(amount: int):
            def _cb():
                hero.repay_loan(amount)
                dialog_overlay['active'] = False
            return _cb
        dialog_overlay['options'].append(("Погасить 1000 ₽", make_pay(1000)))
        dialog_overlay['options'].append(("Погасить 3000 ₽", make_pay(3000)))
        dialog_overlay['options'].append(("Отмена", lambda: dialog_overlay.update({'active': False})))

    def _set_work_event(message: str, choices: List[Tuple[str, Callable[[], None]]]):
        work_overlay['message'] = message
        work_overlay['choices'] = choices
        work_overlay['choice_rects'] = []

    def _maybe_bg_after_choice():
        import random as _r
        # во время активной работы не вызываем встречи
        if work_overlay.get('active'):
            return
        if _r.random() < (0.2 if difficulty_mode == 'hardcore' else 0.12):
            do_random_encounter()

    def _next_work_event():
        if work_overlay['events_left'] <= 0:
            # Завершение работы: подвести итоги
            focus = work_overlay['focus']
            stress = work_overlay['stress']
            # Баффы/дебаффы
            if focus >= 65:
                hero.health_score = min(200, hero.health_score + 5)
                hero.log_event("Работа прошла продуктивно: здоровье +5.")
                hero.work_productive_today = True
            elif focus <= 35:
                hero.alertness = max(0, hero.alertness - 6)
                hero.log_event("Провал по фокусу на работе: бодрость -6.")
            if stress >= 10:
                hero.alertness = max(0, hero.alertness - 8)
                hero.log_event("Стресс на работе: бодрость -8.")
            elif stress <= 2:
                hero.health_score = min(200, hero.health_score + 2)
                hero.log_event("Спокойная смена: здоровье +2.")
            work_overlay['active'] = False
            hero.worked_today = True
            hero.change_money(0)  # отрисуем баланс
            return

        import random as _r
        etype = _r.choice(['focus_task', 'feature_task', 'incident_task', 'client_demo'])
        if etype == 'tempt_smoke':
            msg = "Перекур: коллеги зовут покурить."
            def refuse():
                work_overlay['stress'] += 6
                if hero.alertness >= 70:
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 3)
                hero.log_event("На работе отказался от перекура. Стресс +6, фокус немного вырос.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def accept():
                hero.smoke()
                work_overlay['stress'] = max(0, work_overlay['stress'] - 3)
                work_overlay['focus'] = max(0, work_overlay['focus'] - 4)
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Отказаться", refuse), ("Пойти покурить", accept)])
        elif etype == 'tempt_coffee':
            msg = "Кофе-брейк: коллеги зовут выпить кофе."
            def take():
                hero.consume_coffee()
                work_overlay['focus'] = min(100, work_overlay['focus'] + 2)
                work_overlay['stress'] = max(0, work_overlay['stress'] - 1)
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def skip():
                work_overlay['stress'] += 3
                delta = 1 if hero.alertness >= 60 else -2
                work_overlay['focus'] = max(0, min(100, work_overlay['focus'] + delta))
                hero.log_event("Отказался от кофе на работе.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Выпить кофе", take), ("Отказаться", skip)])
        elif etype == 'focus_task':
            msg = "Задача от начальника: успеешь к сроку?"
            def focus_on():
                import random as _r2
                base = 0.45
                base += 0.05 if hero.alertness >= 60 else 0.0
                base += 0.03 * max(0, hero.intelligence - 1)
                if _r2.random() < min(0.9, base):
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 8)
                    hero.log_event("Сконцентрировался на задаче: фокус +8.")
                    # прогресс квеста по работе (отчёты)
                    try:
                        hero.increment_quest('work_reports', 1)
                    except Exception:
                        pass
                else:
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 3)
                    hero.log_event("Старался, но отвлекался: фокус +3.")
                work_overlay['stress'] += 1
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def procrastinate():
                work_overlay['focus'] = max(0, work_overlay['focus'] - 5)
                work_overlay['stress'] = max(0, work_overlay['stress'] - 2)
                hero.log_event("Прокрастинировал на работе: фокус -5, стресс -2.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Сконцентрироваться", focus_on), ("Прокрастинировать", procrastinate)])
        elif etype == 'feature_task':
            msg = "Новая фича: спроектировать и реализовать модуль."
            def design():
                import random as _r2
                success = _r2.random() < (0.55 + 0.03 * max(0, hero.intelligence - 1))
                if success:
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 7)
                    hero.log_event("Спроектировал архитектуру модуля. Фокус +7.")
                    try:
                        # Показать квест при первом успехе
                        if hero.quests.get('work_features', {}).get('status') == 'Скрыто':
                            hero.quests['work_features']['status'] = 'В процессе'
                        hero.increment_quest('work_features', 1)
                    except Exception:
                        pass
                else:
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 3)
                    hero.log_event("Идея сырая. Фокус +3.")
                work_overlay['stress'] += 2
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def implement():
                import random as _r2
                success = _r2.random() < (0.5 + 0.04 * max(0, hero.intelligence - 1) + 0.03 * max(0, hero.agility - 1))
                if success:
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 9)
                    hero.log_event("Имплементировал модуль без багов. Фокус +9.")
                    try:
                        if hero.quests.get('work_features', {}).get('status') == 'Скрыто':
                            hero.quests['work_features']['status'] = 'В процессе'
                        hero.increment_quest('work_features', 1)
                    except Exception:
                        pass
                else:
                    work_overlay['stress'] += 3
                    hero.log_event("Срыв сроков, нужно рефакторить.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Спроектировать", design), ("Имплементировать", implement)])
        elif etype == 'incident_task':
            msg = "Инцидент в проде: сервис 500. Что делать?"
            def rollback():
                work_overlay['stress'] = max(0, work_overlay['stress'] - 1)
                hero.log_event("Откатились — стабильно, но откат по задачам.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def hotfix():
                import random as _r2
                success = _r2.random() < (0.52 + 0.03 * max(0, hero.intelligence - 1))
                if success:
                    hero.log_event("Хотфикс прошёл успешно.")
                    try:
                        if hero.quests.get('work_incidents', {}).get('status') == 'Скрыто':
                            hero.quests['work_incidents']['status'] = 'В процессе'
                        hero.increment_quest('work_incidents', 1)
                    except Exception:
                        pass
                    work_overlay['focus'] = min(100, work_overlay['focus'] + 5)
                else:
                    work_overlay['stress'] += 4
                    hero.log_event("Хотфикс не удался. Стресс +4.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Откат", rollback), ("Хотфикс", hotfix)])
        else:  # client_demo
            msg = "Встреча с клиентом: провести демо."
            def prepare():
                work_overlay['focus'] = min(100, work_overlay['focus'] + 4)
                hero.log_event("Подготовился к демо. Фокус +4.")
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            def present():
                import random as _r2
                success = _r2.random() < (0.5 + 0.05 * max(0, hero.charisma - 1))
                if success:
                    hero.log_event("Демо прошло успешно, клиент доволен.")
                    try:
                        if hero.quests.get('work_presentations', {}).get('status') == 'Скрыто':
                            hero.quests['work_presentations']['status'] = 'В процессе'
                        hero.increment_quest('work_presentations', 1)
                    except Exception:
                        pass
                    work_overlay['stress'] = max(0, work_overlay['stress'] - 1)
                else:
                    hero.log_event("Демо средней руки. Нужно улучшить подачу.")
                    work_overlay['stress'] += 2
                _maybe_bg_after_choice()
                work_overlay['events_left'] -= 1
                _next_work_event()
            _set_work_event(msg, [("Подготовиться", prepare), ("Провести демо", present)])

    def start_work():
        # Разрешаем прийти пораньше: ждать до 10:00
        current_h = hero.time_minutes // 60
        if current_h < 10:
            wait = 10*60 - hero.time_minutes
            if wait > 0:
                hero.advance_time(wait)
                hero.log_event("Пришел пораньше и подождал до 10:00.")
        if hero.time_minutes // 60 >= 17:
            hero.log_event("Смена уже закончилась. Приходи завтра.")
            return
        work_overlay['active'] = True
        work_overlay['events_left'] = 20
        work_overlay['focus'] = 50
        work_overlay['stress'] = 0
        hero.current_location = 'work'
        hero.log_event("Начал рабочую смену.")
        _next_work_event()

    def go_home():
        hero.current_location = 'home'
        hero.advance_time(20)
        hero.log_event("Вернулся домой.")

    def go_gym():
        hero.current_location = 'gym'
        hero.advance_time(25)
        hero.log_event("Пришел в качалку.")

    def go_park():
        hero.current_location = 'park'
        hero.advance_time(20)
        hero.log_event("Пришел на спортивную площадку.")

    def open_travel():
        # Собираем варианты перемещения в зависимости от текущей локации
        travel_overlay['active'] = True
        travel_overlay['options'] = []
        travel_overlay['option_rects'] = []
        loc = hero.current_location
        targets = [('home', 'Дом', 25, 10, 40), ('work', 'Работа', 25, 10, 40), ('gym', 'Качалка', 25, 10, 40), ('park', 'Площадка', 25, 10, 40)]
        loc_to_tile = {'home': (0,4), 'work': (5,0), 'gym': (5,5), 'park': (0,5)}
        def make_walk(target_key: str, label: str, minutes: int):
            def _cb():
                # Корректируем путь по РПГ статам
                adj = hero.compute_travel_minutes('walk', minutes)
                hero.advance_time(adj)
                hero.weight_kg = max(40.0, hero.weight_kg - 0.02)
                hero.current_location = target_key
                hero.log_event(f"Пешком в {label} (-0.02 кг, {adj} мин).")
                travel_overlay['active'] = False
                _maybe_bg_after_choice()
                nonlocal hero_gx, hero_gy
                hero_gx, hero_gy = loc_to_tile.get(target_key, (hero_gx, hero_gy))
            return _cb
        def make_bus(target_key: str, label: str, minutes: int, cost: int):
            def _cb():
                hero.change_money(-cost)
                hero.advance_time(minutes)
                hero.current_location = target_key
                hero.log_event(f"Автобусом в {label} (-{cost} ₽).")
                travel_overlay['active'] = False
                _maybe_bg_after_choice()
                nonlocal hero_gx, hero_gy
                hero_gx, hero_gy = loc_to_tile.get(target_key, (hero_gx, hero_gy))
            return _cb
        def make_taxi(target_key: str, label: str, minutes: int, cost: int):
            def _cb():
                hero.change_money(-cost)
                hero.advance_time(minutes)
                hero.current_location = target_key
                hero.log_event(f"Такси в {label} (-{cost} ₽).")
                travel_overlay['active'] = False
                _maybe_bg_after_choice()
                nonlocal hero_gx, hero_gy
                hero_gx, hero_gy = loc_to_tile.get(target_key, (hero_gx, hero_gy))
            return _cb
        def make_cancel():
            def _cb():
                travel_overlay['active'] = False
            return _cb
        for key, label, walk_min, bus_min, bus_cost in targets:
            if key == loc:
                continue
            travel_overlay['options'].append((f"В {label} пешком", make_walk(key, label, walk_min)))
            travel_overlay['options'].append((f"В {label} автобусом", make_bus(key, label, bus_min, bus_cost)))
            taxi_min = max(5, bus_min - 3)
            taxi_cost = max(120, bus_cost * 4)
            travel_overlay['options'].append((f"В {label} на такси", make_taxi(key, label, taxi_min, taxi_cost)))
        # Кнопка отмены
        travel_overlay['options'].append(("Отмена", make_cancel()))

    # Сохранение/загрузка
    def save_game():
        data = {
            'hero': hero.__dict__,
            'day_counter': day_counter,
            'hero_gx': hero_gx,
            'hero_gy': hero_gy,
            'difficulty_mode': difficulty_mode,
            'tutorial_active': tutorial_active,
        }
        try:
            with open('savegame.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            hero.log_event("Игра сохранена в savegame.json")
        except Exception as e:
            hero.log_event(f"Ошибка сохранения: {e}")

    def load_game():
        nonlocal day_counter, hero_gx, hero_gy, difficulty_mode, tutorial_active
        try:
            with open('savegame.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Восстановим героя по известным полям
            hero_dict = data.get('hero', {})
            for k, v in hero_dict.items():
                if hasattr(hero, k):
                    setattr(hero, k, v)
            day_counter = int(data.get('day_counter', day_counter))
            hero_gx = int(data.get('hero_gx', hero_gx))
            hero_gy = int(data.get('hero_gy', hero_gy))
            difficulty_mode = data.get('difficulty_mode', difficulty_mode)
            tutorial_active = bool(data.get('tutorial_active', tutorial_active))
            hero.apply_difficulty(difficulty_mode)
            hero.log_event("Игра загружена из savegame.json")
        except FileNotFoundError:
            hero.log_event("Сохранение не найдено.")
        except Exception as e:
            hero.log_event(f"Ошибка загрузки: {e}")

    # Кнопки
    groups = build_action_groups(
        hero,
        combined_end_day_sleep,
        toggle_logs,
        toggle_difficulty,
        do_random_encounter,
        difficulty_mode,
        sleep_1h,
        start_work,
        open_travel,
        save_game,
        load_game,
        open_coffee_dialog,
        lambda: open_food_dialog(False, 60),
        buy_coffee_machine,
        open_loan_dialog,
        open_repay_dialog,
    )
    actions = groups.get(active_actions_group, [])
    rects, _grid_h = layout_buttons([(label, cb) for (label, cb, _en) in actions], font, bottom_margin=48)
    buttons: List[Button] = []
    for i, ((label, cb, en), rect) in enumerate(zip(actions, rects)):
        def make_cb(idx: int, action_cb: Callable[[], None]):
            def _inner():
                nonlocal last_clicked_index
                action_cb()
                last_clicked_index = idx
            return _inner
        b = Button(rect, label, make_cb(i, cb))
        b.enabled = en
        buttons.append(b)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Движение героя по комнате
                elif event.key == pygame.K_LEFT:
                    hero_gx = max(0, hero_gx - 1)
                    if random_chance := (0.35 if difficulty_mode == 'hardcore' else 0.2):
                        import random as _r
                        if _r.random() < random_chance:
                            do_random_encounter()
                elif event.key == pygame.K_RIGHT:
                    hero_gx = min(GRID_W - 1, hero_gx + 1)
                    if random_chance := (0.35 if difficulty_mode == 'hardcore' else 0.2):
                        import random as _r
                        if _r.random() < random_chance:
                            do_random_encounter()
                elif event.key == pygame.K_UP:
                    hero_gy = max(0, hero_gy - 1)
                    if random_chance := (0.35 if difficulty_mode == 'hardcore' else 0.2):
                        import random as _r
                        if _r.random() < random_chance:
                            do_random_encounter()
                elif event.key == pygame.K_DOWN:
                    hero_gy = min(GRID_H - 1, hero_gy + 1)
                    if random_chance := (0.35 if difficulty_mode == 'hardcore' else 0.2):
                        import random as _r
                        if _r.random() < random_chance:
                            do_random_encounter()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_menu_active:
                    # Обработаем клики по стартовому меню ниже в рендере, где есть прямоугольники
                    pass
                else:
                    if work_overlay['active']:
                        # Клики по кнопкам мини-игры Работа
                        if work_overlay['choice_rects']:
                            for (rect, (_label, cb)) in work_overlay['choice_rects']:
                                if rect.collidepoint(event.pos):
                                    cb()
                                    break
                    elif encounter_overlay['active']:
                        # Клик на оверлей встречи — проверим кнопку ОК
                        ok_rect = encounter_overlay.get('ok_rect')
                        if ok_rect and ok_rect.collidepoint(event.pos):
                            hero.random_encounter(difficulty_mode, apply=True, forced_type=encounter_overlay['data']['type'])
                            encounter_overlay['active'] = False
                    elif travel_overlay['active']:
                        # Навигация: выбор опции
                        for (rect, (_lbl, cb)) in travel_overlay.get('option_rects', []):
                            if rect.collidepoint(event.pos):
                                cb()
                                break
                    elif dialog_overlay['active']:
                        for (rect, (_lbl, cb)) in dialog_overlay.get('option_rects', []):
                            if rect.collidepoint(event.pos):
                                cb()
                                break
                    else:
                        for b in buttons:
                            b.handle_event(event)
            elif event.type == pygame.MOUSEWHEEL:
                if active_tab == "log":
                    log_scroll = max(0, log_scroll - event.y * 24)

        # Туториал логика (привязка к названиям действий, а не индексам)
        if tutorial_active and tutorial_step < len(tutorial_steps):
            required_labels = tutorial_steps[tutorial_step][1]
            # Автовыбор группы, содержащей требуемые кнопки
            if required_labels:
                # Найдем первую группу, где есть любая из требуемых кнопок
                for gname, gactions in groups.items():
                    # нормализуем метки (убираем суффиксы статусов)
                    def base_label(lbl: str) -> str:
                        return lbl.split(' (')[0].split(' [')[0]
                    labels_in_group = {base_label(lbl) for (lbl, _cb, _en) in gactions}
                    if any(base_label(l) in labels_in_group for l in required_labels):
                        active_actions_group = gname
                        break

            actions = groups.get(active_actions_group, [])
            # карта по нормализованной метке
            def base_label(lbl: str) -> str:
                return lbl.split(' (')[0].split(' [')[0]
            labels_to_idx = {base_label(label): i for i, (label, _cb, _en) in enumerate(actions)}
            required = [labels_to_idx[base_label(l)] for l in required_labels if base_label(l) in labels_to_idx]
            for i, b in enumerate(buttons):
                b.enabled = (i in required)
            if last_clicked_index is not None and last_clicked_index in required:
                tutorial_step += 1
                last_clicked_index = None
                if tutorial_step >= len(tutorial_steps):
                    tutorial_active = False
                    for b in buttons:
                        b.enabled = True
        else:
            for b in buttons:
                b.enabled = True

        # Рендер
        screen.fill(COLOR_BG)

        # Верхняя плашка вкладок
        tab_bar = pygame.Rect(20, 16, 380, 36)
        pygame.draw.rect(screen, COLOR_PANEL, tab_bar, border_radius=10)
        # Кнопки вкладок
        game_tab_rect = pygame.Rect(tab_bar.x + 8, tab_bar.y + 4, 120, 28)
        log_tab_rect = pygame.Rect(tab_bar.x + 132, tab_bar.y + 4, 120, 28)
        quests_tab_rect = pygame.Rect(tab_bar.x + 256, tab_bar.y + 4, 120, 28)
        pygame.draw.rect(screen, COLOR_ACCENT if active_tab == 'game' else (70, 75, 82), game_tab_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_ACCENT if active_tab == 'log' else (70, 75, 82), log_tab_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_ACCENT if active_tab == 'quests' else (70, 75, 82), quests_tab_rect, border_radius=8)
        screen.blit(font.render("Игра", True, (0, 0, 0)), font.render("Игра", True, (0,0,0)).get_rect(center=game_tab_rect.center))
        log_label = "Журнал" + (" •" if new_events_flag and active_tab != 'log' else "")
        screen.blit(font.render(log_label, True, (0, 0, 0)), font.render(log_label, True, (0,0,0)).get_rect(center=log_tab_rect.center))
        screen.blit(font.render("Квесты", True, (0, 0, 0)), font.render("Квесты", True, (0,0,0)).get_rect(center=quests_tab_rect.center))

        # Клики по вкладкам (не во время оверлеев)
        if pygame.mouse.get_pressed()[0] and not start_menu_active and not work_overlay.get('active', False):
            if game_tab_rect.collidepoint(mouse_pos):
                active_tab = 'game'
            elif log_tab_rect.collidepoint(mouse_pos):
                active_tab = 'log'
                new_events_flag = False
            elif quests_tab_rect.collidepoint(mouse_pos):
                active_tab = 'quests'

        # Кнопка "Завершить день" отдельным большим акцентом в левом-верхнем углу
        end_day_button_rect = pygame.Rect(420, 16, 200, 36)
        pygame.draw.rect(screen, (255, 120, 60), end_day_button_rect, border_radius=10)
        screen.blit(font.render("Завершить день", True, (0,0,0)), font.render("Завершить день", True, (0,0,0)).get_rect(center=end_day_button_rect.center))
        if pygame.mouse.get_pressed()[0]:
            if end_day_button_rect.collidepoint(mouse_pos) and not start_menu_active and not end_day_latch:
                combined_end_day_sleep()
                end_day_latch = True
        else:
            end_day_latch = False

        if start_menu_active:
            # Рисуем стартовое меню
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            panel = pygame.Rect(0, 0, 520, 320)
            panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=14)
            title = font.render("Выбор сложности и обучение", True, COLOR_TEXT)
            screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))

            # Кнопки сложности
            norm_btn = pygame.Rect(panel.x + 40, panel.y + 100, 200, 44)
            hard_btn = pygame.Rect(panel.x + 280, panel.y + 100, 200, 44)
            pygame.draw.rect(screen, COLOR_ACCENT if difficulty_mode=='normal' else (70,75,82), norm_btn, border_radius=10)
            pygame.draw.rect(screen, COLOR_ACCENT if difficulty_mode=='hardcore' else (70,75,82), hard_btn, border_radius=10)
            screen.blit(font.render("Обычный", True, (0,0,0)), font.render("Обычный", True, (0,0,0)).get_rect(center=norm_btn.center))
            screen.blit(font.render("Хардкор", True, (0,0,0)), font.render("Хардкор", True, (0,0,0)).get_rect(center=hard_btn.center))

            # Чекбокс пропуска обучения
            cb_rect = pygame.Rect(panel.x + 40, panel.y + 170, 24, 24)
            pygame.draw.rect(screen, (200,200,200), cb_rect, 2, border_radius=4)
            if skip_tutorial:
                pygame.draw.rect(screen, (200,200,200), cb_rect.inflate(-6,-6), 0, border_radius=3)
            screen.blit(font.render("Пропустить обучение", True, COLOR_TEXT), (cb_rect.right + 10, cb_rect.y))

            # Выбор героя
            names = ["Артем", "Филя", "Апполлон"]
            hero_rects = []
            hx = panel.x + 40
            hy = panel.y + 200
            for nm in names:
                r = pygame.Rect(hx, hy, 140, 36)
                pygame.draw.rect(screen, COLOR_ACCENT if selected_hero_name == nm else (70,75,82), r, border_radius=8)
                screen.blit(font.render(nm, True, (0,0,0)), font.render(nm, True, (0,0,0)).get_rect(center=r.center))
                hero_rects.append((nm, r))
                hx += 160

            # Кнопка старт
            start_btn = pygame.Rect(panel.x + 160, panel.y + 250, 200, 48)
            pygame.draw.rect(screen, COLOR_OK, start_btn, border_radius=12)
            screen.blit(font.render("Начать", True, (0,0,0)), font.render("Начать", True, (0,0,0)).get_rect(center=start_btn.center))

            # Обработка кликов
            if pygame.mouse.get_pressed()[0]:
                for nm, r in hero_rects:
                    if r.collidepoint(mouse_pos):
                        selected_hero_name = nm
                if norm_btn.collidepoint(mouse_pos):
                    difficulty_mode = 'normal'
                elif hard_btn.collidepoint(mouse_pos):
                    difficulty_mode = 'hardcore'
                elif cb_rect.collidepoint(mouse_pos):
                    skip_tutorial = not skip_tutorial
                elif start_btn.collidepoint(mouse_pos):
                    hero.name = selected_hero_name
                    hero.apply_difficulty(difficulty_mode)
                    if skip_tutorial:
                        tutorial_active = False
                    start_menu_active = False
        elif active_tab == 'game':
            # Обновим текущую локацию по позиции героя (простое соответствие тайлам)
            if (hero_gx, hero_gy) == (0, 4):
                hero.current_location = 'home'
            elif (hero_gx, hero_gy) == (5, 0):
                hero.current_location = 'work'
            elif (hero_gx, hero_gy) == (5, 5):
                hero.current_location = 'gym'
            elif (hero_gx, hero_gy) == (0, 5):
                hero.current_location = 'park'

            draw_room(screen)
            # Отрисуем след перемещений в виде пунктирных кружков на последних шагах
            # (упрощённая реализация: рисуем лёгкий блик вокруг текущей клетки)
            pygame.draw.circle(screen, (120, 180, 220), (grid_to_iso(hero_gx, hero_gy)[0], grid_to_iso(hero_gx, hero_gy)[1] - 8), 18, 1)
            draw_hero(screen, hero_gx, hero_gy)
            draw_status(screen, font, hero, day_counter, difficulty_mode)
            draw_mini_log(screen, font, hero)
            # Группы действий и селектор групп
            groups = build_action_groups(
                hero,
                combined_end_day_sleep,
                toggle_logs,
                toggle_difficulty,
                do_random_encounter,
                difficulty_mode,
                sleep_1h,
                start_work,
                open_travel,
                save_game,
                load_game,
                open_coffee_dialog,
                lambda: open_food_dialog(False, 60),
                buy_coffee_machine,
                open_loan_dialog,
                open_repay_dialog,
            )

            # Селектор групп над кнопками
            group_names = list(groups.keys())
            selector_h = 36
            selector_rect = pygame.Rect(20, WINDOW_HEIGHT - 220 - selector_h - 12, WINDOW_WIDTH - 40, selector_h)
            pygame.draw.rect(screen, COLOR_PANEL, selector_rect, border_radius=10)
            # Рисуем табы групп
            gx = selector_rect.x + 8
            tab_gap = 8
            group_tab_rects: List[Tuple[str, pygame.Rect]] = []
            for gname in group_names:
                w = max(120, font.size(gname)[0] + 24)
                rect = pygame.Rect(gx, selector_rect.y + 4, w, selector_h - 8)
                pygame.draw.rect(screen, COLOR_ACCENT if gname == active_actions_group else (70, 75, 82), rect, border_radius=8)
                screen.blit(font.render(gname, True, (0, 0, 0)), font.render(gname, True, (0,0,0)).get_rect(center=rect.center))
                group_tab_rects.append((gname, rect))
                gx += w + tab_gap

            # Обработка кликов по табам групп
            if pygame.mouse.get_pressed()[0]:
                for gname, rect in group_tab_rects:
                    if rect.collidepoint(mouse_pos):
                        active_actions_group = gname

            # Перерисуем кнопки (с перераскладкой по активной группе)
            actions = groups.get(active_actions_group, [])
            rects, _grid_h = layout_buttons([(label, cb) for (label, cb, _en) in actions], font, bottom_margin=selector_h + 12)
            if len(buttons) != len(actions):
                buttons = []
                for i, ((label, cb, en), rect) in enumerate(zip(actions, rects)):
                    def make_cb(idx: int, action_cb: Callable[[], None]):
                        def _inner():
                            nonlocal last_clicked_index
                            action_cb()
                            last_clicked_index = idx
                        return _inner
                    b = Button(rect, label, make_cb(i, cb))
                    b.enabled = en
                    buttons.append(b)
            else:
                # обновляем позиции, подписи и доступность
                for b, rect in zip(buttons, rects):
                    b.rect = rect
                for b, (label, _cb, en) in zip(buttons, actions):
                    b.label = label
                    b.enabled = en if not tutorial_active else b.enabled
            for b in buttons:
                b.draw(screen, font, mouse_pos)

            # Рисуем мини-игру Работа, если активна
            if work_overlay['active']:
                ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                ov.fill(COLOR_OVERLAY_BG)
                screen.blit(ov, (0, 0))
                panel = pygame.Rect(0, 0, 640, 360)
                panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=14)
                # Заголовок и статы
                title = font.render("Работа", True, COLOR_TEXT)
                screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 28)))
                # Отображаем окно времени работы и предупреждений
                stats = font.render(
                    f"Фокус: {work_overlay['focus']}  |  Стресс: {work_overlay['stress']}  | Осталось событий: {work_overlay['events_left']}  | Ставка: {hero.job_daily_wage} ₽  | Предупреждения: {hero.job_warnings}",
                    True, COLOR_TEXT
                )
                screen.blit(stats, stats.get_rect(center=(panel.centerx, panel.y + 62)))
                # Сообщение
                lines = work_overlay['message'].split('\n') if work_overlay['message'] else [""]
                y = panel.y + 100
                for line in lines:
                    surf = font.render(line, True, COLOR_TEXT)
                    screen.blit(surf, (panel.x + 24, y))
                    y += 28
                # Кнопки выбора
                btn_w = (panel.w - 24*3)//2
                btn_h = 44
                btn_y = panel.bottom - 24 - btn_h
                left_btn = pygame.Rect(panel.x + 24, btn_y, btn_w, btn_h)
                right_btn = pygame.Rect(panel.x + 24*2 + btn_w, btn_y, btn_w, btn_h)
                choice_rects: List[Tuple[pygame.Rect, Tuple[str, Callable[[], None]]]] = []
                if len(work_overlay['choices']) >= 1:
                    lbl0, cb0 = work_overlay['choices'][0]
                    pygame.draw.rect(screen, COLOR_ACCENT, left_btn, border_radius=10)
                    screen.blit(font.render(lbl0, True, (0,0,0)), font.render(lbl0, True, (0,0,0)).get_rect(center=left_btn.center))
                    choice_rects.append((left_btn, (lbl0, cb0)))
                if len(work_overlay['choices']) >= 2:
                    lbl1, cb1 = work_overlay['choices'][1]
                    pygame.draw.rect(screen, COLOR_ACCENT, right_btn, border_radius=10)
                    screen.blit(font.render(lbl1, True, (0,0,0)), font.render(lbl1, True, (0,0,0)).get_rect(center=right_btn.center))
                    choice_rects.append((right_btn, (lbl1, cb1)))
                work_overlay['choice_rects'] = choice_rects

            # Рисуем встречу, если активна
            if encounter_overlay['active'] and encounter_overlay['data']:
                ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                ov.fill(COLOR_OVERLAY_BG)
                screen.blit(ov, (0, 0))
                panel = pygame.Rect(0, 0, 600, 260)
                panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=14)
                # Заголовок
                title = font.render("Случайная встреча", True, COLOR_TEXT)
                screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 30)))
                # Иконка/тип
                etype = encounter_overlay['data']['type']
                etype_label = {
                    'drunk': 'Алкаш',
                    'gopnik': 'Гопники',
                    'janitor': 'Дворник',
                }.get(etype, etype)
                screen.blit(font.render(f"Тип: {etype_label}", True, COLOR_TEXT), (panel.x + 24, panel.y + 70))
                # Сообщение
                msg_lines = encounter_overlay['data']['message'].split('\n')
                y = panel.y + 104
                for line in msg_lines:
                    screen.blit(font.render(line, True, COLOR_TEXT), (panel.x + 24, y))
                    y += 26
                # Кнопка OK
                ok_rect = pygame.Rect(0, 0, 140, 44)
                ok_rect.center = (panel.centerx, panel.bottom - 40)
                pygame.draw.rect(screen, COLOR_OK, ok_rect, border_radius=10)
                screen.blit(font.render("ОК", True, (0,0,0)), font.render("ОК", True, (0,0,0)).get_rect(center=ok_rect.center))
                # Сохраним активную кнопку для обработки клика
                encounter_overlay['ok_rect'] = ok_rect

            # Рисуем навигацию, если активна
            if travel_overlay['active']:
                ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                ov.fill(COLOR_OVERLAY_BG)
                screen.blit(ov, (0, 0))
                panel = pygame.Rect(0, 0, 640, 360)
                panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=14)
                title = font.render(travel_overlay['title'], True, COLOR_TEXT)
                screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 28)))
                # Список опций
                y = panel.y + 80
                travel_overlay['option_rects'] = []
                for label, _cb in travel_overlay['options']:
                    rect = pygame.Rect(panel.x + 24, y, panel.w - 48, 40)
                    pygame.draw.rect(screen, COLOR_ACCENT, rect, border_radius=8)
                    screen.blit(font.render(label, True, (0,0,0)), font.render(label, True, (0,0,0)).get_rect(center=rect.center))
                    travel_overlay['option_rects'].append((rect, (label, _cb)))
                    y += 48

            # Универсальный диалог
            if dialog_overlay['active']:
                ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                ov.fill(COLOR_OVERLAY_BG)
                screen.blit(ov, (0, 0))
                pw, ph = dialog_overlay.get('panel_size', (620, 360))
                panel = pygame.Rect(0, 0, pw, ph)
                panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=14)
                title = font.render(dialog_overlay['title'], True, COLOR_TEXT)
                screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 28)))
                # Текст
                msg = dialog_overlay.get('message', '')
                y = panel.y + 70
                # перенос строк по ширине
                maxw = panel.w - 48
                for para in msg.split('\n'):
                    for line in wrap_text(font, para, maxw):
                        screen.blit(font.render(line, True, COLOR_TEXT), (panel.x + 24, y))
                        y += 24
                # Опции
                dialog_overlay['option_rects'] = []
                y += 8
                for label, _cb in dialog_overlay['options']:
                    rect = pygame.Rect(panel.x + 24, y, panel.w - 48, 40)
                    pygame.draw.rect(screen, COLOR_ACCENT, rect, border_radius=8)
                    screen.blit(font.render(label, True, (0,0,0)), font.render(label, True, (0,0,0)).get_rect(center=rect.center))
                    dialog_overlay['option_rects'].append((rect, (label, _cb)))
                    y += 48

            if tutorial_active and tutorial_step < len(tutorial_steps):
                draw_tutorial(screen, font, tutorial_steps[tutorial_step][0] + "\n\nНажми здесь, чтобы пропустить обучение")
                # Прямоугольник-кнопка пропуска обучения
                skip_rect = pygame.Rect(WINDOW_WIDTH//2 - 140, 300, 280, 36)
                pygame.draw.rect(screen, (240, 200, 80), skip_rect, border_radius=8)
                screen.blit(font.render("Пропустить обучение", True, (0,0,0)), font.render("Пропустить обучение", True, (0,0,0)).get_rect(center=skip_rect.center))
                if pygame.mouse.get_pressed()[0] and skip_rect.collidepoint(mouse_pos):
                    tutorial_active = False
                    for b in buttons:
                        b.enabled = True
        elif active_tab == 'log':
            # Режим ЖУРНАЛ
            log_panel = pygame.Rect(20, 64, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 84)
            pygame.draw.rect(screen, COLOR_PANEL, log_panel, border_radius=12)
            screen.blit(font.render("Журнал событий", True, COLOR_TEXT), (log_panel.x + 16, log_panel.y + 12))
            # Область прокрутки
            inner = pygame.Rect(log_panel.x + 16, log_panel.y + 44, log_panel.w - 32, log_panel.h - 60)
            pygame.draw.rect(screen, (28, 30, 36), inner, border_radius=8)
            # Рисуем события с прокруткой
            y = inner.y + 8 - log_scroll
            line_h = 24
            for msg in hero.event_log[-500:]:
                surf = font.render(msg, True, (230, 230, 230))
                if y + line_h > inner.y and y < inner.bottom:
                    screen.blit(surf, (inner.x + 10, y))
                y += line_h
        else:
            # Вкладка КВЕСТЫ
            qp = pygame.Rect(20, 64, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 84)
            pygame.draw.rect(screen, COLOR_PANEL, qp, border_radius=12)
            screen.blit(font.render("Квесты", True, COLOR_TEXT), (qp.x + 16, qp.y + 12))
            inner = pygame.Rect(qp.x + 16, qp.y + 44, qp.w - 32, qp.h - 60)
            pygame.draw.rect(screen, (28, 30, 36), inner, border_radius=8)
            y = inner.y + 12
            line_h = 26
            # Заголовки квестов из hero.quests
            try:
                for key, q in hero.quests.items():
                    if q.get('status') == 'Скрыто':
                        continue
                    title = q.get('title', key)
                    desc = q.get('desc', '')
                    status = q.get('status', '')
                    progress = q.get('progress', 0)
                    target = q.get('target', 0)
                    screen.blit(font.render(f"{title} — {status}", True, COLOR_TEXT), (inner.x + 10, y))
                    y += line_h
                    screen.blit(font.render(f"{desc}", True, (200,200,200)), (inner.x + 18, y))
                    y += line_h
                    if target:
                        screen.blit(font.render(f"Прогресс: {progress}/{target}", True, (210,210,210)), (inner.x + 18, y))
                        y += line_h
                    y += 8
            except Exception:
                pass

        # Оверлеи, требующие таймеров, отсутствуют

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()


