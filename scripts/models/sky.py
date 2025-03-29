from random import choice, randint
import pygame
from settings import *
from scripts.helpers.support import *
from scripts.models.sprites import Generic

class Drop(Generic):
    def __init__(self, surf, pos, moving, groups, z):
        
        super().__init__(pos, surf, groups, z)
        self.lifetime = randint(400, 500)
        self.start_time = pygame.time.get_ticks()

        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2, 4)
            self.speed = randint(200, 250)
    def update(self, dt):
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

class Rain:
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        self.rain_drops = import_folder(f'{GRAPHICS_PATH}/rain/drops/')
        self.rain_floor = import_folder(f'{GRAPHICS_PATH}/rain/floor/')

        self.floor_w, self.floor_h = pygame.image.load(f'{GRAPHICS_PATH}/world/ground.png').get_size()

    def create_floor(self):
        Drop(
            surf= choice(self.rain_floor),
            pos= (randint(0, self.floor_w), randint(0, self.floor_h)),
            moving= False,
            groups= self.all_sprites,
            z = LAYERS['rain floor'])

    def create_drops(self):
        Drop(            
            surf= choice(self.rain_drops),
            pos= (randint(0, self.floor_w), randint(0, self.floor_h)),
            moving= True,
            groups= self.all_sprites,
            z = LAYERS['rain drops'])

    def update(self):
        self.create_floor()
        self.create_drops()

class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Add color phases for different times of day
        self.sky_colors = {
            'night': [38, 101, 189],    # Midnight (0:00)
            'dawn': [155, 186, 228],    # Dawn (5:00)
            'day': [255, 255, 255],     # Day (7:00)
            'dusk': [255, 163, 127],    # Dusk (17:00)
            'evening': [146, 126, 191]   # Evening (20:00)
        }
        self.current_color = self.sky_colors['day'].copy()
        
        # Time settings (24 hour cycle)
        self.time_of_day = 0  # 0 to 24 (hours)
        self.day_length = 24 * 60 * 1000  # 24 minutes real time = 24 hours game time
        self.last_time = pygame.time.get_ticks()
        self.day_passed = 0  # Số ngày đã trôi qua

    def get_sky_color(self):
        """Get sky color based on current time"""
        hour = self.time_of_day

        if 0 <= hour < 5:  # Night
            return self.sky_colors['night']
        elif 5 <= hour < 7:  # Dawn
            progress = (hour - 5) / 2
            return self.blend_colors(self.sky_colors['dawn'], self.sky_colors['day'], progress)
        elif 7 <= hour < 17:  # Day
            return self.sky_colors['day']
        elif 17 <= hour < 20:  # Dusk
            progress = (hour - 17) / 3
            return self.blend_colors(self.sky_colors['dusk'], self.sky_colors['evening'], progress)
        else:  # Evening to night (20-24)
            progress = (hour - 20) / 4
            return self.blend_colors(self.sky_colors['evening'], self.sky_colors['night'], progress)

    def blend_colors(self, color1, color2, progress):
        """Blend between two colors based on progress (0-1)"""
        return [
            int(color1[i] + (color2[i] - color1[i]) * progress)
            for i in range(3)
        ]

    def update_sky_color(self):
        """Update sky color based on current time"""
        target_color = self.get_sky_color()
        self.current_color = target_color

    def update_time(self, dt):
        """Update time of day and day counter"""
        # Tính lượng thời gian tăng thêm (24 giờ game ứng với day_length ms thực)
        self.time_of_day += (dt * 1000 * 24) / self.day_length
        # Nếu vượt quá 24, tính số ngày trôi qua và điều chỉnh lại time_of_day
        if self.time_of_day >= 24:
            additional_days = int(self.time_of_day // 24)
            self.day_passed += additional_days
            self.time_of_day %= 24

    def display(self, dt):
        # Update time and sky color
        self.update_time(dt)
        self.update_sky_color()
        
        # Draw sky
        self.full_surf.fill(self.current_color)
        self.display_surface.blit(self.full_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def reset_to_time(self, hour):
        """Reset sky to specific hour"""
        self.time_of_day = hour % 24  # Ensure hour stays within 0-24
        self.update_sky_color()  # Update color immediately for new time



