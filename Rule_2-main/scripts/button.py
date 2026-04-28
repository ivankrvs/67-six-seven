import pygame

pygame.init()

class Button:
    def __init__(self, rect, text, action=None, font=pygame.font.SysFont('Times', 20), color_idle=[107, 127, 136], color_hover=[77, 93, 100], color_active=[65, 78, 84], text_color='white'):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color_idle = color_idle
        self.color_hover = color_hover
        self.color_active = color_active
        self.text_color = text_color
        self.action = action

        self.pressed = False
        self.hovered = False

    def draw(self, surface):
        color = self.color_idle
        if self.pressed:
            color = self.color_active
        elif self.hovered:
            color = self.color_hover

        corner_radius = 20

        pygame.draw.rect(surface, color, self.rect, border_radius=corner_radius)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
            self.pressed = False