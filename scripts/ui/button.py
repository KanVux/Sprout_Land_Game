import pygame

from scripts.helpers.timer import Timer
from settings import *

class Button:
    def __init__(self, x, y, image, scale, callback=None, text=None, text_color=None, pressed_image=None):
        # Tính kích thước và tạo sprite normal
        width = image.get_width()
        height = image.get_height()
        self.normal_image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.callback = callback
        self.hovered = False
        self.clicked = False
        self.was_pressed = False
        self.timer = Timer(200)
        # Lưu sprite pressed nếu có, nếu không, đặt None
        if pressed_image:
            self.pressed_image = pygame.transform.scale(pressed_image, (int(pressed_image.get_width() * scale), int(pressed_image.get_height() * scale)))
        else:
            self.pressed_image = None

        # Nếu có text
        self.text = text
        if text:
            self.font = pygame.font.Font(f'{FONT_PATH}/LycheeSoda.ttf', 30)
            self.text_color = text_color if text_color else 'Black'
            self.text_surf = self.font.render(text, True, self.text_color)
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def update(self, mouse_pos):
        self.timer.update()
        old_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        pressed = pygame.mouse.get_pressed()[0]
        if self.hovered:
            # edge-detection: chỉ gọi callback khi chuyển từ không nhấn sang nhấn
            if pressed and not self.was_pressed:
                self.clicked = True
                self.timer.activate()  # nếu cần auto-repeat
                if self.callback:
                    self.callback()
            elif not pressed:
                self.clicked = False

            # Chuyển sprite nếu đang nhấn
            if pressed and self.pressed_image:
                self.image = self.pressed_image
            else:
                self.image = self.normal_image
        else:
            self.clicked = False
            self.image = self.normal_image

        self.was_pressed = pressed
        return old_hovered != self.hovered

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.text:
            surface.blit(self.text_surf, self.text_rect)
        if self.hovered:
            hover_color = (255, 255, 255, 100)
            hover_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hover_surf, hover_color, hover_surf.get_rect())
            surface.blit(hover_surf, self.rect)



