import pygame

font = pygame.font.SysFont('Arial', 20)

class InputBox:
    def __init__(self, x, y, w, h, inactive, active, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = inactive
        self.color_active = active
        self.color = self.color_inactive
        self.text = text
        self.txt_surface = font.render(text, True, pygame.Color('black'))
        self.active = False
        self.pressed = False

    def handle_event(self, event, game):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Если кликнули в область input box — активируем его
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos) and self.pressed == True:
                self.active = not self.active
                self.pressed = False
                # Меняем цвет в зависимости от активности
                self.color = self.color_active if self.active else self.color_inactive
        elif event.type == pygame.KEYDOWN and self.active == True:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode
            # Перерисовываем текст
            self.txt_surface = font.render(self.text, True, pygame.Color('black'))
        elif event.type == pygame.KEYUP:
            if self.active:
                if event.key == pygame.K_ESCAPE:
                    self.active = False
                    self.color = self.color_active if self.active else self.color_inactive
                    self.text = ''
                    self.txt_surface = font.render(self.text, True, pygame.Color('black'))
                if event.key == pygame.K_RETURN:
                    for player in game.players:
                        if player == self.text:
                            game.nickname = self.text
                            print(player)
                            game.assets['user'] = pygame.image.load('data/images/cards/' + game.players[player]['record'][0] + '.png')

    def update(self):
        # По желанию — можно менять размер input box под текст
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        pygame.draw.rect(screen, pygame.Color('white'), self.rect, 0, 20)
        # Рисуем текст
        txt_rect = self.txt_surface.get_rect()
        txt_rect.center = self.rect.center 
        screen.blit(self.txt_surface, (txt_rect.x, txt_rect.y))
        # Рисуем прямоугольник вокруг
        pygame.draw.rect(screen, self.color, self.rect, 4, 20)