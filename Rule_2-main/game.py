import pygame

import random

import sys

from scripts.card import Card, Cards
from scripts.utils import darken_image, draw_characteristics, check_for_end, go_back, continue_menu, statistics, settings, screen, load_players, draw_account, animation, create_rects, draw_progress, unlogin, upgrade_record, restart, draw_lose, change_player_information, player_hub, create_account
from scripts.button import Button
from scripts.input_box import InputBox
from scripts.menu import Menu, Main_menu, Statistics
from scripts.scrollable_table import ScrollableTable
from data import config

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(config.screen_size)
        self.display = pygame.Surface((1280, 720))

        self.players = load_players()
        text = []
        for player in self.players:
            text.append((player, str(self.players[player]['record'][1])))
        scr_table = ScrollableTable(rect=pygame.Rect(20, 20, self.display.get_width() / 4, self.display.get_height() / 6), row_height=20, rows=text)

        button_width = self.display.get_width() / 8
        button_height = self.display.get_height() / 16

        input_boxes = [InputBox(20, 20 + 3 * (button_height + 20), button_width, button_height, [107, 127, 136], [65, 78, 84])]
        buttons = [Button(pygame.Rect(20, 20, button_width, button_height), 'Настройки', action=lambda: settings(game=self)),
                   Button(pygame.Rect(20, 20 + button_height + 20, button_width, button_height), 'Продолжить', action=lambda: continue_menu(game=self)),
                   Button(pygame.Rect(20, 20 + 2 * (button_height + 20), button_width, button_height), 'Статистика', action=lambda: statistics(game=self)),
                   Button(pygame.Rect(20, 20 + 4 * (button_height + 20), button_width, button_height), 'Разлогиниться', action=lambda: unlogin(game=self)),
                   Button(pygame.Rect(20, 20 + 5 * (button_height + 20), button_width, button_height), 'Косметика', action=lambda: player_hub(game=self)),
                   Button(pygame.Rect(20, 20 + 4 * (button_height + 20), button_width, button_height), 'Создать аккаунт', action=lambda: create_account(game=self))]
        self.menu = Main_menu(self, buttons, input_boxes)

        buttons = []
        self.statistics = Statistics(self, buttons, scr_table)

        buttons = [Button(pygame.Rect(20, 20, button_width, button_height), 'Разрешение экрана', action=lambda: screen(game=self))] 
        self.settings = Menu(self, buttons)

        buttons = [Button(pygame.Rect(20, 20, button_width, button_height), 'Поменять аватар', action=lambda: change_player_information(game=self))]
        input_boxes = [InputBox(20, 20 + 1 * (button_height + 20), button_width, button_height, [107, 127, 136], [65, 78, 84])]
        self.player_hub = Main_menu(self, buttons=buttons, input_boxes=input_boxes)

        self.characteristics = {'church': 50,
                        'people': 50,
                        'army': 50,
                        'money': 50}
        
        self.restart_button = Button(pygame.Rect(20, 20, button_width, button_height), 'Перезапустить', action=lambda: restart(game=self))
        
        self.cards = Cards('data/cards/cards.json', self)

        self.current_index = 0

        self.next_index = 1
        
        self.assets = {'church': pygame.transform.smoothscale(pygame.image.load('data/images/characteristics/church.png'), (self.display.get_width() / 30, self.display.get_width() / 30)),
                       'people': pygame.transform.smoothscale(pygame.image.load('data/images/characteristics/people.png'), (self.display.get_width() / 30, self.display.get_width() / 30)),
                       'army': pygame.transform.smoothscale(pygame.image.load('data/images/characteristics/army.png'), (self.display.get_width() / 30, self.display.get_width() / 30)),
                       'money': pygame.transform.smoothscale(pygame.image.load('data/images/characteristics/money.png'), (self.display.get_width() / 30, self.display.get_width() / 30)),
                       'left_arrow': pygame.transform.rotate(pygame.transform.smoothscale(pygame.image.load('data/images/cards/arrow.png'), (self.display.get_width() / 15, self.display.get_width() / 15)), 180),
                       'right_arrow': pygame.transform.smoothscale(pygame.image.load('data/images/cards/arrow.png'), (self.display.get_width() / 15, self.display.get_width() / 15)),
                       'user':pygame.image.load('data/images/cards/44.png')}
        
        self.right_arrow_pos = [self.display.get_width() * 3 / 4, self.display.get_height() / 2]
        self.right_choice_pos = [self.display.get_width() * 3 / 4 + self.display.get_width() / 30, self.display.get_height() / 2 - self.display.get_width() / 15]
        self.left_arrow_pos = [self.display.get_width() / 4 - self.assets['left_arrow'].get_width(), self.display.get_height() / 2]
        self.left_choice_pos = [self.display.get_width() / 4 - self.assets['left_arrow'].get_width() + self.display.get_width() / 30, self.display.get_height() / 2 - self.display.get_width() / 15]

        self.clock = pygame.time.Clock()

        self.background = darken_image(pygame.transform.scale(pygame.image.load('data/images/background.png'), self.display.get_size()))

        self.heap = []

        self.nickname = "гость"

        self.button = False

        self.escape = False

        self.statistics_b = False

        self.settings_b = False

        self.player_hub_b = False

        self.progress = 0

        self.end = False

        self.animation = [60, 0, 60]
        self.rects = []
        size = random.randint(4, 8)
        for i in range(size):
            self.rects.append([self.display.get_width(), self.display.get_height() // size + 1, 0, random.randint(21, 28)])


    def run(self):
        for i in range(4):
            index = random.randint(1, 10)
            self.heap.append(Card(self, self.cards.cards[str(index)], pygame.image.load('data/images/cards/' + self.cards.cards[str(index)]['individual'] + '.png')))
        self.heap.append(Card(self, self.cards.cards[str(10)], pygame.image.load('data/images/cards/' + self.cards.cards[str(11)]['individual'] + '.png')))
        self.next_index = random.randint(0, 4)
        while self.heap[self.next_index].information["sentence"] == self.heap[self.current_index].information["sentence"]:
            self.next_index = random.randint(0, 4)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display.blit(self.background, (0, 0))

            self.end = check_for_end(self)
            if self.end:
                if self. animation[1] < self.progress / 10 + 1:
                    self.animation[0] = 120  
                    self.animation[1] += 1 
                    self.animation[2] = 120
                    self.rects = create_rects(self)
                upgrade_record(self)
                self.restart_button.handle_event(event)    
                draw_lose(self)
            else:
                if self.progress % 10 == 0 and self.progress > 0 and self.animation[1] < self.progress / 10:
                    self.animation[0] = 120  
                    self.animation[1] += 1 
                    self.animation[2] = 120
                    self.rects = create_rects(self)
                
                if self.escape == False and self.animation[0] == 0:
                    self.heap[self.current_index].update()
                
                draw_progress(self)

                self.heap[self.current_index].render()

                draw_characteristics(self)
                draw_account(self)

            if self.escape == True:
                if self.statistics_b == True:
                    self.statistics.render()
                elif self.settings_b == True:
                    self.settings.render()
                elif self.player_hub_b == True:
                    self.player_hub.render()
                else:
                    self.menu.render()     

            if self.animation[0] > 0:
                animation(self)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP:
                    self.button = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE and self.animation[0] == 0:
                        self.menu.update(event)
                        go_back(self)


                if self.escape == True:
                    self.button = False
                    if self.statistics_b == True:
                        self.statistics.update(event)
                    elif self.settings_b == True:
                        self.settings.update(event)
                    elif self.player_hub_b == True:
                        self.player_hub.update(event)
                    else:
                        self.menu.update(event)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()

            self.clock.tick(60)

Game().run()