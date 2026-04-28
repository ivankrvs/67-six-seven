import json

import pygame

import random

import string

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

class Card:
    def __init__(self, game, information, image):
        self.game = game
        
        self.information = information

        scale = image.get_width() / image.get_height()

        self.image = pygame.transform.smoothscale(image, (self.game.display.get_width() // 3 * scale, self.game.display.get_width() // 3))
        #self.image.center = (self.game.display.get_width() // 3 * 2, self.game.display.get_height() // 3 * 2)
        self.render_image = self.image

        self.pos = [self.game.display.get_rect().centerx - self.image.get_width() / 2, self.game.display.get_rect().centery - self.image.get_height() / 2]
        self.render_pos = self.pos

        self.animation = False
        self.text_animation = ['']*len(self.information["sentence"].split("\n"))

        self.choices = analyze_last_sentence(self.information["sentence"])

        self.movement = [1, 1]
        self.random_movement = [0, 0]

        self.angle = 0
        self.random_angle = 0

    def update(self):
        if not self.animation:
            # Кэшируем часто используемые значения
            screen_rect = self.game.screen.get_rect()
            display_rect = self.game.display.get_rect()
            mouse_pos = pygame.mouse.get_pos()
            
            # Вычисляем смещение
            offset_x = (mouse_pos[0] - screen_rect.centerx) / 5
            offset_x = max(-30, min(30, offset_x))
            
            offset_y = (mouse_pos[1] - screen_rect.centery) / 15
            offset_y = max(-10, min(10, offset_y))
            
            # Целевая позиция
            target_x = display_rect.centerx - self.image.get_width() / 2 + offset_x
            target_y = display_rect.centery - self.image.get_height() / 2 + offset_y
            
            # Плавное движение
            lerp_factor = 0.1
            self.pos[0] += (target_x - self.pos[0]) * lerp_factor
            self.pos[1] += (target_y - self.pos[1]) * lerp_factor

            # Текстовая анимация
            if not hasattr(self, '_cached_text_lines'):
                self._cached_text_lines = self.information["sentence"].split("\n")
                
            for i, line in enumerate(self._cached_text_lines):
                if len(self.text_animation[i]) < len(line):
                    self.text_animation[i] = line[:len(self.text_animation[i]) + 1]
                    break

            if self.game.button:
                self.animation = True
                self.direction = 1 if offset_x > 0 else -1
                display_width = self.game.display.get_width()
                display_height = self.game.display.get_height()

                self.movement = [
                    self.direction * (display_width / 160),
                    -display_height / 90
                ]
                self.random_movement = [self.direction * random.random() * 3, 0]
                self.random_angle = random.random() * 6

                # Обновляем характеристики
                for key in self.game.characteristics.keys():
                    if self.direction > 0:
                        self.game.characteristics[key] += self.information['right_' + key]
                    else:
                        self.game.characteristics[key] += self.information['left_' + key]
                    
        else:
            # Анимация полета карты
            self.angle += self.random_angle * self.movement[0] / (self.game.display.get_width() / 160)

            self.render_image = pygame.transform.rotate(self.image, self.angle)
            center_pos = (
                self.pos[0] + self.image.get_width() / 2,
                self.pos[1] + self.image.get_height() / 2
            )
            
            render_rect = self.render_image.get_rect(center=center_pos)
            self.render_pos = render_rect.topleft

            self.pos[0] += self.movement[0] + self.random_movement[0]
            self.pos[1] += self.movement[1] + self.random_movement[1]
            self.movement[1] += self.game.display.get_height() / 720
            
            # Проверка завершения анимации
            if self.render_pos[1] > self.game.display.get_height():
                self.game.cards.update()
                self.reset_card_state()

    def reset_card_state(self):
        """Сбрасывает состояние карты к начальному"""
        self.animation = False
        self.game.button = False
        self.movement = [1, 1]
        self.angle = 0
        
        display_rect = self.game.display.get_rect()
        self.pos = [
            display_rect.centerx - self.image.get_width() / 2,
            display_rect.centery - self.image.get_height() / 2
        ]
        self.render_pos = self.pos.copy()
        self.render_image = self.image

    def render(self):
        display_width = self.game.display.get_width()
        display_height = self.game.display.get_height()
        third_width = display_width // 3
        
        rect = pygame.Rect(third_width, 0, third_width, display_height)
        pygame.draw.rect(self.game.display, (34, 34, 34), rect)
        
        if not hasattr(self, '_overlay_surfaces'):
            self.create_overlay_surfaces()
        
        if not self.game.escape:
            mouse_x = pygame.mouse.get_pos()[0]
            if mouse_x > display_width / 2:
                self.game.display.blit(self._right_overlay, (2 * third_width, 0))
            elif mouse_x < display_width / 2:
                self.game.display.blit(self._left_overlay, (0, 0))
        
        self.render_text(rect)
        
        self.game.display.blit(self.game.assets['right_arrow'], self.game.right_arrow_pos)
        self.game.display.blit(self.game.assets['left_arrow'], self.game.left_arrow_pos)
        
        self.render_choices()
        
        next_image = self.game.heap[self.game.next_index].image
        next_pos = [
            display_width / 2 - next_image.get_width() / 2,
            display_height / 2 - next_image.get_height() / 2
        ]
        self.game.display.blit(next_image, next_pos)
        
        # Рендерим саму карту
        self.game.display.blit(self.render_image, self.render_pos)

    def create_overlay_surfaces(self):
        """Создает заранее overlay поверхности"""
        third_width = self.game.display.get_width() // 3
        display_height = self.game.display.get_height()
        
        # Левая область
        self._left_overlay = pygame.Surface((third_width, display_height), pygame.SRCALPHA)
        self._left_overlay.fill((255, 255, 255, 50))
        
        # Правая область
        self._right_overlay = pygame.Surface((third_width, display_height), pygame.SRCALPHA)
        self._right_overlay.fill((255, 255, 255, 50))

    def render_text(self, rect):
        """Рендерит анимированный текст"""
        if not hasattr(self, '_font'):
            self._font = pygame.font.SysFont('Times', 25)
            self._line_height = self._font.get_linesize()
        
        transparent_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        y = rect.height * 7 / 8 - (len(self.text_animation) * self._line_height / 2)
        center_x = rect.width / 2
        
        for line in self.text_animation:
            text_surf = self._font.render(line, True, 'white')
            text_rect = text_surf.get_rect(center=(center_x, y + self._line_height / 2))
            transparent_surf.blit(text_surf, text_rect)
            y += self._line_height
        
        self.game.display.blit(transparent_surf, rect.topleft)

    def render_choices(self):
        """Рендерит текст выборов"""
        if not hasattr(self, '_font'):
            self._font = pygame.font.SysFont('Times', 25)
        
        overlay = pygame.Surface((self.game.display.get_width(), 
                                self.game.display.get_height()), pygame.SRCALPHA)
        
        # Правый выбор
        text_surf = self._font.render(self.choices[0], True, 'white')
        text_rect = text_surf.get_rect(center=self.game.right_choice_pos)
        overlay.blit(text_surf, text_rect)
        
        # Левый выбор
        text_surf = self._font.render(self.choices[1], True, 'white')
        text_rect = text_surf.get_rect(center=self.game.left_choice_pos)
        overlay.blit(text_surf, text_rect)
        
        self.game.display.blit(overlay, (0, 0))

class Cards:
    def __init__(self, path, game):
        with open(path, encoding="UTF-8") as file_in:
            self.cards = json.load(file_in)

        self.game = game

    def update(self):
        last_index = self.game.current_index
        self.game.current_index = self.game.next_index
        if self.game.heap[last_index].direction > 0:
            choice = 'right'
        elif self.game.heap[last_index].direction < 0:
            choice = 'left'

        if self.game.heap[last_index].information[choice + '_cons'] == '':
            self.game.next_index = random.randint(0, 4)
            while self.game.heap[self.game.next_index].information["sentence"] == self.game.heap[self.game.current_index].information["sentence"]:
                self.game.next_index = random.randint(0, 4)

            index = random.randint(1, 10)
            while self.game.heap[last_index].information == self.cards[str(index)]["sentence"]:
                index = random.randint(1, 10)
            self.game.heap[last_index] = (Card(self.game, self.cards[str(index)], pygame.image.load('data/images/cards/' + self.cards[str(index)]['individual'] + '.png')))
        else:
            index = int(self.game.heap[last_index].information[choice + '_cons'])
            self.game.next_index = last_index
            #if self.game.heap[self.game.next_index].information['left_cons'] == '' and self.game.heap[self.game.next_index].information['right_cons']:
            #    while index == self.game.next_index or index == self.game.current_index or
            #    self.game.heap[]
            self.game.heap[last_index] = (Card(self.game, self.cards[str(index)], pygame.image.load('data/images/cards/' + self.cards[str(index)]['individual'] + '.png')))

        self.game.progress = self.game.progress + 1