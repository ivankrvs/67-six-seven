from scripts.button import Button
import pygame

class Menu:
    def __init__(self, game, buttons):
        self.buttons = buttons
        self.game = game

    def update(self, event):
        for button in self.buttons:
            if self.game.nickname == 'гость' and button.text != 'Разлогиниться' and button.text != 'Косметика':
                button.handle_event(event)
            elif self.game.nickname != 'гость' and button.text != 'Создать аккаунт':
                button.handle_event(event)

    def render(self):
        for button in self.buttons:
            if self.game.nickname == 'гость' and button.text != 'Разлогиниться' and button.text != 'Косметика':
                button.draw(self.game.display)
            elif self.game.nickname != 'гость' and button.text != 'Создать аккаунт':
                button.draw(self.game.display)

class Main_menu(Menu):
    def __init__(self, game, buttons, input_boxes):
        self.input_boxes = input_boxes
        super().__init__(game, buttons)

    def update(self, event):
        for input_box in self.input_boxes:
            input_box.handle_event(event, self.game)
            input_box.update()
        return super().update(event)
    
    def render(self):
        for input_box in self.input_boxes:
            input_box.draw(self.game.display)
        return super().render()

class Statistics(Menu):
    def __init__(self, game, buttons, src_table):
        self.src_table = src_table
        super().__init__(game, buttons)

    def update(self, event):
        self.src_table.handle_event(event)
        return super().update(event)

    def render(self):
        self.src_table.render(self.game.display)
        return super().render()