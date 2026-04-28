import pygame

import string

import random

import json

from scripts.card import Card

from data import config

def darken_image(image, darkness=100):
    dark_surf = pygame.Surface(image.get_size(), flags=pygame.SRCALPHA)
    dark_surf.fill((0, 0, 0, darkness))  # чёрный с заданной прозрачностью
    image_copy = image.copy()
    image_copy.blit(dark_surf, (0, 0))
    return image_copy

def darken_pixels(image, darkness=100):
    image_copy = image.copy()
    image_copy.lock()  # для ускорения доступа к пикселям

    width, height = image_copy.get_size()
    for x in range(width):
        for y in range(height):
            r, g, b, a = image_copy.get_at((x, y))
            if a > 0:
                r = max(0, r - darkness)
                g = max(0, g - darkness)
                b = max(0, b - darkness)
                image_copy.set_at((x, y), (r, g, b, a))

    image_copy.unlock()
    return image_copy

def draw_characteristics(game):
    icon_size = game.display.get_width() / 30
    padding = 5
    bar_width = game.display.get_width() / 6 - icon_size - padding * 3
    bar_height = bar_width / 5

    rect = pygame.Rect(game.display.get_width() / 3, 0, game.display.get_width() / 3, game.display.get_height() / 3)

    keys = list(game.characteristics.keys())

    for i, key in enumerate(keys):
        if i < 2:
            x = rect.left + padding
            y = rect.top + padding + i * (icon_size + padding)
        else:
            x = rect.left + rect.width // 2 + padding
            y = rect.top + padding + (i - 2) * (icon_size + padding)


        icon = game.assets.get(key)
        if icon:
            game.display.blit(icon, (x, y))

        x = x + icon_size + padding
        y = y + (icon_size - bar_height) // 2

        pygame.draw.rect(game.display, (200, 200, 200), (x, y, bar_width, bar_height), 2)

        value = max(0, min(100, game.characteristics[key]))

        fill_width = int(bar_width * (value / 100))
        pygame.draw.rect(game.display, (100, 200, 100), (x + 1, y + 1, fill_width - 2, bar_height - 2))

def draw_progress(game):
    font = pygame.font.SysFont('Arial', 24)
    rect = pygame.Rect(game.display.get_width() / 10 * 9, game.display.get_height() / 8 * 7, game.display.get_width() / 10, game.display.get_height() / 8)
    txt_surface = font.render(str(game.progress), True, pygame.Color('white'))
    game.display.blit(txt_surface, (rect.x, rect.y))

def draw_account(game):
    icon_size = game.display.get_width() / 25
    nickname_size = game.display.get_width() / 20

    game.display.blit(pygame.transform.smoothscale(game.assets['user'], (icon_size, icon_size)), (game.display.get_width() / 4 * 3, game.display.get_height() / 40))
    
    rect = pygame.Rect(game.display.get_width() / 4 * 3, game.display.get_height() / 40, icon_size, icon_size)
    pygame.draw.rect(game.display, (100, 100, 100), rect, 4, 4)

    font = pygame.font.SysFont('Arial', 20)

    rect = pygame.Rect(game.display.get_width() / 4 * 3 + icon_size * 1.5, game.display.get_height() / 40, nickname_size, nickname_size)
    txt_surface = font.render(game.nickname, True, pygame.Color('white'))
    game.display.blit(txt_surface, (rect.x, rect.y))

def draw_lose(game):
    # image - pygame.Surface (квадратное)
    # text - строка
    # font - pygame.font.Font
    # button - объект с методом draw()
    # y_start - верхняя координата, откуда начинать рисовать (по вертикали)

    y_start = 200
    center_x = game.display.get_width() // 2
    img_size = (300, 300)
    image = pygame.transform.scale(game.assets['user'], img_size)

    # Позиция для картинки (по центру)
    img_rect = image.get_rect()
    img_rect.centerx = center_x
    img_rect.top = y_start
    game.display.blit(image, img_rect)

    font = pygame.font.SysFont('Arial', 20)

    # Позиция для текста чуть ниже картинки
    text_surf = font.render('Счет: ' + str(game.progress + 1), True, (255, 255, 255))
    text_rect = text_surf.get_rect()
    text_rect.centerx = center_x
    text_rect.top = img_rect.bottom + 5
    game.display.blit(text_surf, text_rect)

    # Позиция для кнопки чуть ниже текста
    if hasattr(game.restart_button, "rect"):
        game.restart_button.rect.centerx = center_x
        game.restart_button.rect.top = text_rect.bottom + 10
    game.restart_button.draw(game.display)

def analyze_last_sentence(text):
    # Разбиваем текст на строки, берем последнюю
    last_line = text.strip().split('.')[-1]
    
    def clean_and_capitalize(s):
        # Удаляем знаки препинания справа
        s = s.rstrip(string.punctuation)
        # Приводим первый символ к заглавному, остальные оставляем как есть
        if s:
            s = s[0].upper() + s[1:]
        return s

    # Проверяем наличие " или " (с пробелами)
    if ' или ' in last_line:
        parts = last_line.split(' или ', 1)
        right_text = clean_and_capitalize(parts[0].strip())
        left_text = clean_and_capitalize(parts[1].strip())
    else:
        right_text = 'Да'
        left_text = 'Нет'

    return right_text, left_text

def check_for_end(game):
    for char in game.characteristics:
        if game.characteristics[char] <= 0:
            return True
    return False 

def statistics(game):
    game.statistics_b = True

def continue_menu(game):
    game.escape = False

def settings(game):
    game.settings_b = True

def go_back(game):
    if game.settings_b == True or game.statistics_b == True or game.player_hub_b == True:
        game.settings_b = False
        game.statistics_b = False
        game.player_hub_b = False
    else:
        game.escape = not game.escape

        game.animation[0] = 30 
        game.animation[1] += 1 
        game.animation[2] = 30
        game.rects = create_rects(game, [106, 110])

def screen(game):
    if config.screen_size[0] == 1280:
        config.screen_size = (1920, 1080)
    else:
        config.screen_size = (1280, 720)
    game.screen = pygame.display.set_mode(config.screen_size)

def load_players():
    with open('data/players.json', encoding="UTF-8") as file_in:
        players = json.load(file_in)

    return players

def animation(game):
    i = 0
    for r in game.rects:
        rect = pygame.Rect(r[2] + r[3] * (game.animation[2] - game.animation[0]), r[1] * i, r[0], r[1])
        pygame.draw.rect(game.display, (10, 10, 10), rect)
        i += 1
    game.animation[0] -= 1

def create_rects(game, speed=[26, 32]):
    rects = []
    size = random.randint(4, 8)
    for i in range(size):
        rects.append([random.randint(game.display.get_width() // 2, game.display.get_width()), game.display.get_height() // size + 1, -game.display.get_width() * 1.5, random.randint(speed[0], speed[1])])
    return rects

def restart(game):
    game.current_index = 0
    for i in range(4):
        index = random.randint(1, 10)
        game.heap[i] = (Card(game, game.cards.cards[str(index)], pygame.image.load('data/images/cards/' + game.cards.cards[str(index)]['individual'] + '.png')))
    game.heap[4] = (Card(game, game.cards.cards[str(10)], pygame.image.load('data/images/cards/' + game.cards.cards[str(11)]['individual'] + '.png')))
    game.next_index = random.randint(0, 4)
    while game.heap[game.next_index].information["sentence"] == game.heap[game.current_index].information["sentence"]:
        game.next_index = random.randint(0, 4)

    game.characteristics = {'church': 50,
                        'people': 50,
                        'army': 50,
                        'money': 50}

    game.button = False

    game.escape = False

    game.statistics_b = False

    game.settings_b = False

    game.player_hub_b = False

    game.progress = 0

    game.end = False

    game.animation = [60, 0, 60]
    game.rects = []
    size = random.randint(4, 8)
    for i in range(size):
        game.rects.append([game.display.get_width(), game.display.get_height() // size + 1, 0, random.randint(21, 28)])

def upgrade_record(game):
    for player in game.players:
        if player == game.nickname:
            if game.players[player]['record'][1] < game.progress + 1:
                game.players[player]['record'][1] = game.progress + 1
                print(str(game.players[player]['record'][1]))
                with open("data/players.json", "w", encoding="utf-8") as f:
                    json.dump(game.players, f, ensure_ascii=False, indent=4)
                game.players = load_players()
                text = []
                for player in game.players:
                    text.append((player, str(game.players[player]['record'][1])))
                game.statistics.src_table.rows = text
                break

def unlogin(game):
    game.assets['user'] = pygame.image.load('data/images/cards/44.png')
    game.nickname = 'гость'

def player_hub(game):
    game.player_hub_b = True

def change_player_information(game):
    game.players[game.nickname]['record'][0] = str(int(game.players[game.nickname]['record'][0]) + 1)
    if game.players[game.nickname]['record'][0] == '49':
        game.players[game.nickname]['record'][0] = '44'
        
    game.assets['user'] = pygame.image.load('data/images/cards/' + game.players[game.nickname]['record'][0] + '.png')

    with open("data/players.json", "w", encoding="utf-8") as f:
        json.dump(game.players, f, ensure_ascii=False, indent=4)

def create_account(game):
    for player in game.players:
        if player == game.menu.input_boxes[0].text or game.menu.input_boxes[0].text == '':
            print('ошибка ввода имени')
            return

    game.players[game.menu.input_boxes[0].text] = {'record': ['45', 0]}
    with open("data/players.json", "w", encoding="utf-8") as f:
        json.dump(game.players, f, ensure_ascii=False, indent=4)
    text = []
    for player in game.players:
        text.append((player, str(game.players[player]['record'][1])))
    game.statistics.src_table.rows = text