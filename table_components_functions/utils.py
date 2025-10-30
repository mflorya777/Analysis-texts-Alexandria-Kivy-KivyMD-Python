from kivy.core.window import Window
from kivymd.uix.button import MDIconButton
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line

from kivymd.uix.tooltip import MDTooltip


class HoverButton(Button):
    """
    Кнопка с изменением цвета при наведении.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Убираем дефолтный фон
        self.background_color = (0.5, 0.5, 0.5, 1)  # Белый фон
        self.hover_color = (0.7, 0.7, 0.7, 1)  # Серый при наведении
        self.default_color = self.background_color

        # Привязываем события движения мыши
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        """
        Отслеживаем позицию мыши.
        """
        if not self.get_parent_window():
            return
        pos = args[1]
        if self.collide_point(*self.to_widget(*pos)):
            self.background_color = self.hover_color
        else:
            self.background_color = self.default_color


class IconButtonWithTooltip(MDIconButton, MDTooltip):
    """
    Класс кастомной кнопки для отображения текста при наведении на кнопку.
    """
    pass


class BorderedCell(BoxLayout):
    """Универсальная ячейка с рамкой для имитации сетки в таблице.

    Оборачивает переданный виджет и рисует прямоугольную рамку по его границам.
    """

    def __init__(self, child=None, border_color=(0.7, 0.7, 0.7, 1), line_width=1, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = (0, 0, 0, 0)
        self.spacing = 0
        self.border_color = border_color
        self.line_width = line_width

        # Если передан дочерний виджет — настраиваем размеры и добавляем внутрь
        if child is not None:
            # Высоту берем из ребенка (если задана), чтобы сохранить высоту строки
            if hasattr(child, 'height') and child.height:
                self.size_hint_y = None
                self.height = child.height
            # По ширине заполняем ячейку колонны
            self.size_hint_x = child.size_hint_x if hasattr(child, 'size_hint_x') else 1

            # Ребенок растягивается внутри рамки
            try:
                child.size_hint = (1, 1)
            except Exception:
                pass

            self.add_widget(child)

        # Обновляем отрисовку рамки при изменении размеров/позиции
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self._update_canvas()

    def _update_canvas(self, *args):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(*self.border_color)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=self.line_width)
