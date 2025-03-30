import pygame
from scripts.db.inventory_db import InventoryDatabase
from settings import *

class InventoryUI:
    def __init__(self, player):
        self.player = player
        self.display_surface = pygame.display.get_surface()
        
        # Tải font đẹp hơn
        self.title_font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 30)
        self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 20)
        
        # Thiết lập UI
        self.padding = 20
        self.slot_size = 64
        self.gap = 10
        self.cols = 5
        self.rows = 4
        
        # Số lượng slot đặc biệt (3 ô đầu tiên của hàng đầu)
        self.hotbar_slots = 3
        
        # Tính toán kích thước cửa sổ inventory
        self.width = self.cols * (self.slot_size + self.gap) + self.padding * 2
        self.height = self.rows * (self.slot_size + self.gap) + self.padding * 2 + 50  # Thêm không gian cho tiêu đề
        
        # Đặt vị trí inventory ở giữa màn hình
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = (SCREEN_HEIGHT - self.height) // 2
        
        # Thiết lập kéo thả
        self.hovering = False
        self.dragging = False
        self.dragged_item = None
        self.dragged_origin = None
        self.drag_offset = None
        self.drag_scale = 1.0  # Hiệu ứng phóng to khi kéo
        self.animation_time = 0
        
        # Tải tài nguyên
        try:
            # Tải các hình ảnh của slot với các trạng thái khác nhau
            self.slot_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/slot.png').convert_alpha()
            self.slot_hover = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/slot_hover.png').convert_alpha()
            self.slot_selected = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/slot_selected.png').convert_alpha()
            
            # Tải hình ảnh cho hotbar slot (hoặc sử dụng hình ảnh đặc biệt nếu có)
            try:
                self.hotbar_slot_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/hotbar_slot.png').convert_alpha()
                self.hotbar_slot_hover = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/hotbar_slot_hover.png').convert_alpha()
            except FileNotFoundError:
                # Nếu không có ảnh riêng, tạo các phiên bản màu khác của slot thông thường
                self.hotbar_slot_surface = self._generate_slot_image((80, 80, 120))  # Màu xanh dương nhạt
                self.hotbar_slot_hover = self._generate_slot_image((100, 100, 160))  # Màu xanh dương đậm
        except FileNotFoundError:
            # Fallback nếu không tìm thấy hình ảnh tùy chỉnh
            self.slot_surface = self._generate_slot_image((60, 60, 60))
            self.slot_hover = self._generate_slot_image((80, 80, 80))
            self.slot_selected = self._generate_slot_image((100, 100, 160))
            self.hotbar_slot_surface = self._generate_slot_image((80, 80, 120))
            self.hotbar_slot_hover = self._generate_slot_image((100, 100, 160))
            
        # Điều chỉnh tỷ lệ ảnh
        self.slot_surface = pygame.transform.scale(self.slot_surface, (self.slot_size, self.slot_size))
        self.slot_hover = pygame.transform.scale(self.slot_hover, (self.slot_size, self.slot_size))
        self.slot_selected = pygame.transform.scale(self.slot_selected, (self.slot_size, self.slot_size))
        self.hotbar_slot_surface = pygame.transform.scale(self.hotbar_slot_surface, (self.slot_size, self.slot_size))
        self.hotbar_slot_hover = pygame.transform.scale(self.hotbar_slot_hover, (self.slot_size, self.slot_size))
        
        # Tải ảnh nền inventory
        try:
            self.bg_image = pygame.image.load(f'{GRAPHICS_PATH}/ui/inventory/inventory_bg.png').convert_alpha()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        except FileNotFoundError:
            self.bg_image = None
            
        # Hiệu ứng mở inventory
        self.active = False
        self.opening = False
        self.open_progress = 0  # 0 - 1 (đóng - mở)
        self.mouse_pressed = False
        
        # Hiệu ứng hover
        self.hovered_slot = -1
        
        # Tooltip
        self.show_tooltip = False
        self.tooltip_item = None
        self.tooltip_timer = 0
        
        # Đồng bộ với hotbar khi mở inventory lần đầu
        self.sync_with_hotbar()

    def _generate_slot_image(self, color):
        """Tạo hình ảnh slot mặc định nếu không tìm thấy ảnh tùy chỉnh"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        pygame.draw.rect(surface, color, (0, 0, self.slot_size, self.slot_size), 0, border_radius=6)
        pygame.draw.rect(surface, (100, 100, 100), (0, 0, self.slot_size, self.slot_size), 2, border_radius=6)
        inner_rect = pygame.Rect(4, 4, self.slot_size-8, self.slot_size-8)
        pygame.draw.rect(surface, (30, 30, 30, 180), inner_rect, 0, border_radius=4)
        return surface
        
    def is_hotbar_slot(self, slot_index):
        """Kiểm tra xem slot có phải là slot trên hotbar hay không"""
        return 0 <= slot_index < self.hotbar_slots
    
    def sync_with_hotbar(self):
        """Đồng bộ 3 slot đầu tiên với danh sách hotbar của người chơi"""
        # Đảm bảo inventory có đủ slot
        while len(self.player.inventory.items) < self.rows * self.cols:
            self.player.inventory.items.append(None)
            
        # Lấy danh sách các item trong hotbar của player từ custom slots
        hotbar_items = []
        if hasattr(self.player, 'ui') and hasattr(self.player.ui, 'custom_slots'):
            for item in self.player.ui.custom_slots:
                if item is not None:
                    hotbar_items.append(item)
                    
        # Cập nhật lại 3 slot đầu tiên dựa trên các vật phẩm trong hotbar
        for i, item_name in enumerate(hotbar_items):
            if i < self.hotbar_slots:
                # Tìm item trong inventory để đặt vào slot hotbar
                for j, inv_item in enumerate(self.player.inventory.items):
                    if inv_item and inv_item.item_name == item_name:
                        # Nếu item không phải ở vị trí hotbar, hoán đổi vị trí
                        if j >= self.hotbar_slots:
                            self.player.inventory.items[i], self.player.inventory.items[j] = \
                            self.player.inventory.items[j], self.player.inventory.items[i]
                        break
        
    def toggle(self):
        """Hiển thị/ẩn inventory"""
        self.active = not self.active
        if self.active:
            self.opening = True
            self.open_progress = 0
            # Đồng bộ với hotbar khi mở inventory
            self.sync_with_hotbar()
        else:
            # Khi đóng inventory, đồng bộ các vật phẩm trong 3 slot đầu với hotbar
            InventoryDatabase.save_inventory(self.player.player_id, self.player.inventory)
    
   
   
            
    def get_slot_at_pos(self, pos):
        """Xác định vị trí slot dựa trên tọa độ chuột"""
        x, y = pos
        # Kiểm tra nếu vị trí nằm trong vùng inventory
        if (self.x <= x <= self.x + self.width and 
            self.y + 50 <= y <= self.y + self.height):  # +50 để bỏ qua vùng tiêu đề
            # Tính toán vị trí slot
            rel_x = x - self.x - self.padding
            rel_y = y - self.y - self.padding - 50  # Điều chỉnh cho tiêu đề
            col = rel_x // (self.slot_size + self.gap)
            row = rel_y // (self.slot_size + self.gap)
            
            if (0 <= col < self.cols and 0 <= row < self.rows and
                rel_x % (self.slot_size + self.gap) <= self.slot_size and
                rel_y % (self.slot_size + self.gap) <= self.slot_size):
                return row * self.cols + col
        return None

    def get_nearest_slot(self, pos):
        """Tìm slot gần nhất với vị trí chuột"""
        mouse_x, mouse_y = pos
        closest_slot = None
        min_distance = float('inf')
        
        # Tính khoảng cách đến tâm của mỗi slot
        for i in range(self.rows * self.cols):
            row = i // self.cols
            col = i % self.cols
            
            # Tính vị trí tâm slot
            slot_x = self.x + self.padding + col * (self.slot_size + self.gap) + self.slot_size / 2
            slot_y = self.y + self.padding + 50 + row * (self.slot_size + self.gap) + self.slot_size / 2
            
            # Tính khoảng cách đến chuột
            distance = ((mouse_x - slot_x) ** 2 + (mouse_y - slot_y) ** 2) ** 0.5
            
            # Cập nhật slot gần nhất nếu slot này gần hơn
            if distance < min_distance:
                min_distance = distance
                closest_slot = i
        
        # Chỉ trả về slot nếu chuột ở trong khoảng cách hợp lý
        max_snap_distance = self.slot_size * 1.5
        return closest_slot if min_distance <= max_snap_distance else None
    
    def handle_click(self, event):
        """Xử lý sự kiện nhấp chuột"""
        if not self.active:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Nhấp chuột trái
                slot_index = self.get_slot_at_pos(event.pos)
                if slot_index is not None and slot_index < len(self.player.inventory.items):
                    # Bắt đầu kéo từ slot
                    self.dragging = True
                    self.dragged_item = self.player.inventory.items[slot_index]
                    self.dragged_origin = slot_index
                    # Thêm offset để item không nhảy khi bắt đầu kéo
                    mouse_x, mouse_y = event.pos
                    slot_x = self.x + self.padding + (slot_index % self.cols) * (self.slot_size + self.gap)
                    slot_y = self.y + self.padding + 50 + (slot_index // self.cols) * (self.slot_size + self.gap)
                    self.drag_offset = (mouse_x - (slot_x + self.slot_size // 2),
                                      mouse_y - (slot_y + self.slot_size // 2))
                    self.drag_scale = 1.2  # Bắt đầu hiệu ứng phóng to
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                target_slot = self.get_nearest_slot(event.pos)
                
                if target_slot is not None and target_slot < self.rows * self.cols:
                    # Mở rộng inventory nếu cần
                    while len(self.player.inventory.items) <= target_slot:
                        self.player.inventory.items.append(None)
                    
                    # Hoán đổi item
                    if self.dragged_origin != target_slot:
                        self.player.inventory.items[self.dragged_origin], self.player.inventory.items[target_slot] = \
                        self.player.inventory.items[target_slot], self.player.inventory.items[self.dragged_origin]

                
                # Reset trạng thái kéo thả
                self.dragging = False
                self.dragged_item = None
                self.drag_offset = None
    
    def update(self, mouse_pos, mouse_pressed, dt=1/60):
        """Cập nhật logic cho inventory"""
        # Hiệu ứng mở inventory
        if self.active and self.opening:
            self.open_progress = min(1.0, self.open_progress + dt * 4)
            if self.open_progress >= 1.0:
                self.opening = False
        elif not self.active:
            self.open_progress = 0
            
        # Cập nhật hiệu ứng phóng to khi kéo
        if self.dragging and self.drag_scale > 1.0:
            self.drag_scale = max(1.0, self.drag_scale - dt * 0.5)  # Trở về kích thước bình thường dần dần
            
        # Cập nhật tooltip
        self.show_tooltip = False
        if self.active and not self.dragging:
            self.hovered_slot = self.get_slot_at_pos(mouse_pos)
            if self.hovered_slot is not None and self.hovered_slot < len(self.player.inventory.items):
                hovered_item = self.player.inventory.items[self.hovered_slot]
                if hovered_item is not None:
                    self.hovering = True
                    self.tooltip_timer += dt
                    if self.tooltip_timer > 0.7:  # Hiển thị tooltip sau 0.7 giây hover
                        self.show_tooltip = True
                        self.tooltip_item = hovered_item
            else:
                self.hovering = False         
                self.tooltip_timer = 0
        else:
            self.tooltip_timer = 0

        if not self.active:
            return

        # Xử lý khi nhấn chuột
        if mouse_pressed and not self.mouse_pressed:
            slot_index = self.get_slot_at_pos(mouse_pos)
            if slot_index is not None and slot_index < len(self.player.inventory.items):
                self.dragging = True
                self.dragged_item = self.player.inventory.items[slot_index]
                self.dragged_origin = slot_index
                # Tính offset
                slot_x = self.x + self.padding + (slot_index % self.cols) * (self.slot_size + self.gap)
                slot_y = self.y + self.padding + 50 + (slot_index // self.cols) * (self.slot_size + self.gap)
                self.drag_offset = (mouse_pos[0] - (slot_x + self.slot_size // 2),
                                  mouse_pos[1] - (slot_y + self.slot_size // 2))
                self.drag_scale = 1.2  # Bắt đầu hiệu ứng phóng to

        # Xử lý khi thả chuột
        elif not mouse_pressed and self.mouse_pressed:
            if self.dragging:
                target_slot = self.get_nearest_slot(mouse_pos)
                if target_slot is not None and target_slot < self.rows * self.cols:
                    while len(self.player.inventory.items) <= target_slot:
                        self.player.inventory.items.append(None)
                    if self.dragged_origin != target_slot:
                        self.player.inventory.items[self.dragged_origin], self.player.inventory.items[target_slot] = \
                        self.player.inventory.items[target_slot], self.player.inventory.items[self.dragged_origin]

                
                self.dragging = False
                self.dragged_item = None
                self.drag_offset = None

        self.mouse_pressed = mouse_pressed
        
        # Hiệu ứng nhấp nháy cho slot gần nhất khi đang kéo
        if self.dragging:
            self.animation_time += dt
            if self.animation_time > 0.8:
                self.animation_time = 0
    
    def draw_tooltip(self, item, pos):
        """Vẽ tooltip hiển thị thông tin chi tiết về item"""
        if not item:
            return
            
        # Chuẩn bị thông tin
        name = item.item_name.replace('_', ' ').title()
        description = getattr(item, 'item_description', "Một vật phẩm trong game")
        
        # Vẽ nền tooltip
        name_surf = self.font.render(name, True, (255, 255, 255))
        desc_surf = self.font.render(description, True, (220, 220, 220))
        
        width = max(name_surf.get_width(), desc_surf.get_width()) + 20
        height = name_surf.get_height() + desc_surf.get_height() + 25
        
        # Định vị tooltip để không ra ngoài màn hình
        tooltip_x = min(pos[0] + 15, SCREEN_WIDTH - width - 5)
        tooltip_y = min(pos[1] - 10, SCREEN_HEIGHT - height - 5)
        
        # Vẽ nền
        tooltip_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        tooltip_surf.fill((40, 40, 40, 230))
        pygame.draw.rect(tooltip_surf, (100, 100, 100, 255), tooltip_surf.get_rect(), 1, border_radius=5)
        
        # Vẽ văn bản
        tooltip_surf.blit(name_surf, (10, 8))
        pygame.draw.line(tooltip_surf, (150, 150, 150, 150), (10, name_surf.get_height() + 10), 
                        (width - 10, name_surf.get_height() + 10), 1)
        tooltip_surf.blit(desc_surf, (10, name_surf.get_height() + 15))
        
        # Hiển thị tooltip
        self.display_surface.blit(tooltip_surf, (tooltip_x, tooltip_y))

    def draw(self):
        """Vẽ inventory UI"""
        if not self.active:
            return
        # Tính toán hiệu ứng mở
        if self.opening:
            scale = self.open_progress
            target_width = self.width * scale
            target_height = self.height * scale
            target_x = self.x + (self.width - target_width) / 2
            target_y = self.y + (self.height - target_height) / 2
        else:
            target_width = self.width
            target_height = self.height
            target_x = self.x
            target_y = self.y
            
        # Vẽ nền
        if self.bg_image:
            # Sử dụng ảnh nền tùy chỉnh nếu có
            scaled_bg = pygame.transform.scale(self.bg_image, (int(target_width), int(target_height)))
            self.display_surface.blit(scaled_bg, (target_x, target_y))
        else:
            # Tạo nền gradient nếu không có ảnh
            background = pygame.Surface((int(target_width), int(target_height)), pygame.SRCALPHA)
            
            # Tạo gradient từ trên xuống
            for y in range(int(target_height)):
                alpha = 240  # Độ trong suốt
                r = int(70 - y/target_height * 20)  # Gradient từ đậm đến nhạt
                g = int(70 - y/target_height * 10)
                b = int(80 - y/target_height * 10)
                pygame.draw.line(background, (r, g, b, alpha), 
                               (0, y), (target_width, y))
            
            # Vẽ viền và các chi tiết
            pygame.draw.rect(background, (50, 50, 60, 255), background.get_rect(), 3, border_radius=10)
            pygame.draw.rect(background, (30, 30, 40, 255), background.get_rect().inflate(-6, -6), 2, border_radius=8)
            
            # Vẽ tiêu đề
            if not self.opening or (self.opening and self.open_progress > 0.7):
                title = self.title_font.render("Inventory", True, (255, 230, 180))
                background.blit(title, (target_width//2 - title.get_width()//2, 15))
                

            self.display_surface.blit(background, (target_x, target_y))
        
        # Không vẽ slot nếu đang mở
        if self.opening and self.open_progress < 0.8:
            return
            
        # Vẽ các slot và item
        mouse_pos = pygame.mouse.get_pos()
        for i in range(self.rows * self.cols):
            row = i // self.cols
            col = i % self.cols
            x = self.x + self.padding + col * (self.slot_size + self.gap)
            y = self.y + self.padding + 50 + row * (self.slot_size + self.gap)  # +50 cho tiêu đề
            
            # Xác định loại slot (thông thường hay hotbar)
            is_hotbar_slot = self.is_hotbar_slot(i)
            
            # Chọn bề mặt slot dựa trên trạng thái và loại
            if i == self.hovered_slot:
                # Slot được hover
                slot_img = self.hotbar_slot_hover if is_hotbar_slot else self.slot_hover
            elif self.dragging and i == self.get_nearest_slot(mouse_pos):
                # Slot gần nhất khi đang kéo
                slot_img = self.slot_selected
            else:
                # Slot thông thường
                slot_img = self.hotbar_slot_surface if is_hotbar_slot else self.slot_surface
            
            # Hiệu ứng nhấp nháy cho slot đích khi kéo thả
            if self.dragging and i == self.get_nearest_slot(mouse_pos):
                if (self.animation_time < 0.4):  # Nhấp nháy trong nửa đầu chu kỳ
                    self.display_surface.blit(slot_img, (x, y))
                    # Vẽ hiệu ứng phát sáng xung quanh slot
                    highlight_rect = pygame.Rect(x - 3, y - 3, self.slot_size + 6, self.slot_size + 6)
                    brightness = int(200 + 55 * (0.4 - self.animation_time) / 0.4)  # Từ 200-255 và ngược lại
                    
                    # Màu khác cho hotbar slot
                    highlight_color = (brightness, brightness, 100) if not is_hotbar_slot else (100, 100, brightness)
                    pygame.draw.rect(self.display_surface, highlight_color, 
                                  highlight_rect, 3, border_radius=6)
            else:
                self.display_surface.blit(slot_img, (x, y))
            
            # Vẽ item nếu có
            if i < len(self.player.inventory.items):
                item = self.player.inventory.items[i]
                if item is not None and (not self.dragging or i != self.dragged_origin):
                    try:
                        item_surface = pygame.image.load(f'{GRAPHICS_PATH}/items/{item.item_name}.png').convert_alpha()
                        item_surface = pygame.transform.scale(item_surface, (self.slot_size - 16, self.slot_size - 16))
                        self.display_surface.blit(item_surface, (x + 8, y + 8))
                        
                        # Vẽ số lượng với hiệu ứng đẹp hơn
                        if item.quantity > 1:
                            # Tạo nền cho số lượng
                            quantity_text = self.font.render(str(item.quantity), True, (255, 255, 255))
                            text_width = quantity_text.get_width()
                            text_height = quantity_text.get_height()
                            
                            # Vẽ nền tròn cho số lượng
                            bubble_radius = max(text_width, text_height) // 2 + 5
                            bubble_x = x + self.slot_size - bubble_radius - 2
                            bubble_y = y + self.slot_size - bubble_radius - 2
                            
                            # Vẽ bóng đổ
                            pygame.draw.circle(self.display_surface, (0, 0, 0, 150), 
                                            (bubble_x + 2, bubble_y + 2), bubble_radius)
                            
                            # Vẽ nền chính - màu khác nhau cho các loại slot
                            if is_hotbar_slot:
                                bubble_color = (80, 80, 180)  # Màu xanh dương cho hotbar
                                bubble_border = (120, 120, 220)
                            else:
                                bubble_color = (60, 60, 180)  # Màu mặc định
                                bubble_border = (100, 100, 220)
                            
                            pygame.draw.circle(self.display_surface, bubble_color, 
                                            (bubble_x, bubble_y), bubble_radius)
                            
                            # Vẽ viền
                            pygame.draw.circle(self.display_surface, bubble_border, 
                                            (bubble_x, bubble_y), bubble_radius, 2)
                            
                            # Vẽ số lượng
                            text_x = bubble_x - text_width // 2
                            text_y = bubble_y - text_height // 2
                            self.display_surface.blit(quantity_text, (text_x, text_y))
                    except FileNotFoundError:
                        print(f"Cảnh báo: Không tìm thấy hình ảnh cho vật phẩm {item.item_name}")
        
        # Vẽ item đang kéo
        if self.dragging and self.dragged_item:
            try:
                # Điều chỉnh kích thước dựa trên hiệu ứng phóng to
                drag_size = int((self.slot_size - 16) * self.drag_scale)
                item_surface = pygame.image.load(f'{GRAPHICS_PATH}/items/{self.dragged_item.item_name}.png').convert_alpha()
                item_surface = pygame.transform.scale(item_surface, (drag_size, drag_size))
                
                # Tính vị trí giữa mục và thêm độ lệch từ lúc bắt đầu kéo
                center_offset = drag_size // 2
                x = mouse_pos[0] - center_offset - (self.drag_offset[0] if self.drag_offset else 0)
                y = mouse_pos[1] - center_offset - (self.drag_offset[1] if self.drag_offset else 0)
                
                # Vẽ bóng đổ cho item đang kéo
                shadow_surface = pygame.Surface((drag_size, drag_size), pygame.SRCALPHA)
                shadow_surface.blit(item_surface, (0, 0))
                shadow_surface.fill((0, 0, 0, 100), None, pygame.BLEND_RGBA_MULT)
                self.display_surface.blit(shadow_surface, (x + 4, y + 4))
                
                # Vẽ item đang kéo
                self.display_surface.blit(item_surface, (x, y))
                
                # Vẽ số lượng nếu > 1
                if self.dragged_item.quantity > 1:
                    # Tạo nền cho số lượng
                    quantity_text = self.font.render(str(self.dragged_item.quantity), True, (255, 255, 255))
                    text_width = quantity_text.get_width()
                    text_height = quantity_text.get_height()
                    
                    # Vẽ nền tròn cho số lượng
                    bubble_radius = max(text_width, text_height) // 2 + 5
                    bubble_x = x + drag_size - bubble_radius + 5
                    bubble_y = y + drag_size - bubble_radius + 5
                    
                    # Vẽ bóng đổ
                    pygame.draw.circle(self.display_surface, (0, 0, 0, 150), 
                                    (bubble_x + 2, bubble_y + 2), bubble_radius)
                    
                    # Vẽ nền chính
                    bubble_color = (80, 80, 180) if self.is_hotbar_slot(self.dragged_origin) else (60, 60, 180)
                    pygame.draw.circle(self.display_surface, bubble_color, 
                                     (bubble_x, bubble_y), bubble_radius)
                    
                    # Vẽ viền
                    bubble_border = (120, 120, 220) if self.is_hotbar_slot(self.dragged_origin) else (100, 100, 220)
                    pygame.draw.circle(self.display_surface, bubble_border, 
                                     (bubble_x, bubble_y), bubble_radius, 2)
                    
                    # Vẽ số lượng
                    text_x = bubble_x - text_width // 2
                    text_y = bubble_y - text_height // 2
                    self.display_surface.blit(quantity_text, (text_x, text_y))
                    
            except FileNotFoundError:
                print(f"Cảnh báo: Không tìm thấy hình ảnh cho vật phẩm đang kéo {self.dragged_item.item_name}")

        # Vẽ tooltip
        if self.show_tooltip:
            self.draw_tooltip(self.tooltip_item, mouse_pos)