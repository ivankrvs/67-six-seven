import pygame

class ScrollableTable:
    def __init__(self, rect, row_height, rows, font=pygame.font.SysFont('Arial', 20), col_widths=None, bg_color=(255, 255, 255), border_color=(107, 127, 136)):
        """
        rect: pygame.Rect - область, где рисуется таблица
        row_height: int - высота одной строки
        font: pygame.font.Font - шрифт для текста
        rows: list of tuple(str, str) - данные таблицы (2 столбца)
        col_widths: tuple(int, int) - ширины двух столбцов (если None, делит rect по ширине пополам)
        bg_color: цвет фона
        border_color: цвет линий
        """

        self.rect = rect
        self.row_height = row_height
        self.font = font
        self.rows = rows
        self.bg_color = bg_color
        self.border_color = border_color

        if col_widths is None:
            half_width = self.rect.width // 2
            self.col_widths = (half_width, self.rect.width - half_width)
        else:
            self.col_widths = col_widths

        self.offset = 0  # смещение прокрутки по вертикали (в пикселях)
        self.max_offset = max(0, len(rows) * row_height - self.rect.height)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            # прокрутка колесом мыши (обычно event.y = 1 или -1)
            scroll_speed = 20  # пикселей на шаг прокрутки
            self.offset -= event.y * scroll_speed
            if self.offset < 0:
                self.offset = 0
            if self.offset > self.max_offset:
                self.offset = self.max_offset

    def render(self, surface):
        # рисуем фон и границы
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)

        # создаём "окно" для отрисовки таблицы, чтобы можно было обрезать выход за границы
        clip = surface.get_clip()
        surface.set_clip(self.rect)

        start_row = self.offset // self.row_height
        y_offset = -(self.offset % self.row_height)

        for i in range(start_row, len(self.rows)):
            y = self.rect.y + y_offset + (i - start_row) * self.row_height
            if y > self.rect.bottom:
                break  # вышли за пределы видимой области

            row_rect = pygame.Rect(self.rect.x, y, self.rect.width, self.row_height)
            pygame.draw.rect(surface, self.border_color, row_rect, 1)

            col1_x = self.rect.x + self.col_widths[0]
            pygame.draw.line(surface, self.border_color, (col1_x, y), (col1_x, y + self.row_height), 1)

            text1 = self.font.render(str(self.rows[i][0]), True, (0, 0, 0))
            text2 = self.font.render(str(self.rows[i][1]), True, (0, 0, 0))

            surface.blit(text1, (self.rect.x + 5, y + (self.row_height - text1.get_height()) // 2))
            surface.blit(text2, (col1_x + 5, y + (self.row_height - text2.get_height()) // 2))

        surface.set_clip(clip)