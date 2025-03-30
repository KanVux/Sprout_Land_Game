import pygame
from settings import *

class Overlay:
    def __init__(self, player):
        self.display_surface = pygame.display.get_surface()
        self.player = player
        
        # Nhập các tài nguyên
        overlay_path = f'{GRAPHICS_PATH}/overlay/'
        self.tools_surface = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools}
        self.hotbar_surface = {}
      
        # Tải các thành phần giao diện
        self.highlight_surface = pygame.image.load(f'{overlay_path}hotbar/hotbar_selected_highlight.png').convert_alpha()
        hotbar_bg = pygame.image.load(f'{overlay_path}hotbar/hotbar_bg.png').convert_alpha()
        self.slot_background = pygame.image.load(f'{overlay_path}hotbar/hotbar_slot.png').convert_alpha()
        
        # Thanh công cụ nền
        self.hotbar_background = hotbar_bg
        
        # Cài đặt thanh công cụ
        self.hotbar_width = self.hotbar_background.get_width()
        self.hotbar_height = self.hotbar_background.get_height()
        self.slot_size = 70 # Đảm bảo ô vừa theo chiều dọc
        
        # Khởi tạo danh sách vật phẩm trước
        self.items = self.player.tools +  self.player.hotbar  # Kết hợp công cụ và hạt giống
        
        # Tính khoảng cách đều nhau
        self.total_items = len(self.items)
        total_padding = self.hotbar_width - (2 * 20) - (self.total_items * self.slot_size)
        self.slot_padding = total_padding // (self.total_items - 1)
        
        # Vị trí thanh công cụ ở giữa dưới màn hình
        self.hotbar_x = (SCREEN_WIDTH - self.hotbar_width) // 2
        self.hotbar_y = SCREEN_HEIGHT - self.hotbar_height - 10
        
        # Bề mặt cho overlay
        self.overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Thêm biến để theo dõi trạng thái kéo chuột giữa
        self.middle_mouse_scrolling = False
        self.last_mouse_x = 0
        self.scroll_sensitivity = 20  # Ngưỡng pixel để đổi công cụ
        self.scroll_cooldown = 0  # Thời gian chờ giữa các lần cuộn
        self.scroll_highlight_timer = 0  # Đếm thời gian hiệu ứng đánh dấu
        self.scroll_highlight_duration = 0.3  # Thời gian hiển thị hiệu ứng đánh dấu
        
        # Thiết lập chỉ số được chọn ban đầu dựa trên công cụ của người chơi
        if player.selected_tool in player.tools:
            self.selected_index = player.tools.index(player.selected_tool)
        elif player.selected_item in player.hotbar:
            self.selected_index = len(player.tools) + player.hotbar.index(player.selected_item)
        
        # Tải bề mặt hạt giống ban đầu
        self.update_hotbar_surfaces()

    def update_selected_index(self, new_index):
        """Cập nhật chỉ số được chọn và công cụ/hạt giống của người chơi"""
        if self.player.timers['tool use'].active:
            return False

        old_index = self.selected_index
        self.selected_index = new_index % len(self.items)
        selected_item = self.items[self.selected_index]
        
        # Chỉ cập nhật nếu chỉ số thực sự thay đổi
        if old_index != self.selected_index:
            if selected_item in self.player.tools:
                self.player.selected_tool = selected_item
                self.player.tool_index = self.player.tools.index(selected_item)
            else:
                self.player.selected_item = selected_item
                self.player.hotbar_index = self.player.hotbar.index(selected_item)
            return True
        return False

    def handle_input(self, event):
        if event.type == pygame.MOUSEWHEEL:
            # Cuộn qua các vật phẩm bằng bánh xe chuột
            self.selected_index = (self.selected_index - event.y) % len(self.items)
            # Cập nhật công cụ/hạt giống được chọn
            selected_item = self.items[self.selected_index]
            if selected_item in self.player.tools:
                self.player.selected_tool = selected_item
                self.player.tool_index = self.player.tools.index(selected_item)
            else:
                self.player.selected_item = selected_item
                self.player.hotbar_index = self.player.hotbar.index(selected_item)
            # Kích hoạt hiệu ứng đánh dấu khi chọn vật phẩm
            self.scroll_highlight_timer = self.scroll_highlight_duration

    def update_hotbar_surfaces(self):
        """Cập nhật bề mặt hạt giống dựa trên danh sách hạt giống của người chơi"""
        # Xóa và tạo lại các surface cho seeds
        self.hotbar_surface = {}
        
        # Tải lại hình ảnh cho tất cả hạt giống hiện tại
        for item in self.player.hotbar:
            try:
                self.hotbar_surface[item] = pygame.image.load(f'{GRAPHICS_PATH}/items/{item}.png').convert_alpha()
            except:
                print(f"Không thể tải hình ảnh cho vật phẩm: {item}")
        
        # Cập nhật danh sách vật phẩm
        self.items = self.player.tools + self.player.hotbar
        
        # Tính lại khoảng cách giữa các slot
        self.total_items = len(self.items)
        if self.total_items > 1:
            total_padding = self.hotbar_width - (2 * 20) - (self.total_items * self.slot_size)
            self.slot_padding = total_padding // (self.total_items - 1)

    def update_hotbar(self):
        """Cập nhật hotbar khi danh sách công cụ hoặc hạt giống thay đổi"""
        # Cập nhật bề mặt hạt giống
        self.update_hotbar_surfaces()
        
        # Đảm bảo chỉ số được chọn vẫn hợp lệ
        if self.selected_index >= len(self.items):
            self.selected_index = len(self.items) - 1
        
        # Cập nhật trạng thái lựa chọn của người chơi
        self.update_selected_index(self.selected_index)

    def draw_hotbar(self):
        # Vẽ nền thanh công cụ
        self.display_surface.blit(self.hotbar_background, (self.hotbar_x, self.hotbar_y))
        
        # Tính vị trí bắt đầu cho vật phẩm đầu tiên
        start_x = self.hotbar_x + 20  # Khoảng cách cố định từ cạnh trái
        start_y = self.hotbar_y + (self.hotbar_height - self.slot_size) // 2 + 10  # Căn giữa theo chiều dọc
        
        # Lấy vật phẩm đang được chọn để đánh dấu
        current_tool = self.player.selected_tool
        current_seed = self.player.selected_item
        
        # Vẽ ô công cụ và vật phẩm
        for index, item in enumerate(self.items):
            # Tính vị trí với khoảng cách đều
            item_x = start_x + index * (self.slot_size + self.slot_padding)
            item_y = start_y
            
            # Vẽ nền ô
            slot_rect = pygame.Rect(item_x, item_y, self.slot_size, self.slot_size)
            self.display_surface.blit(
                pygame.transform.scale(self.slot_background, (self.slot_size, self.slot_size)),
                slot_rect
            )
            
            # Vẽ đánh dấu cho mục đang chọn
            is_selected = (item == current_tool) or (item == current_seed)
            
            if is_selected:
                # Tạo hiệu ứng nhấp nháy nếu mới được chọn bằng chuột giữa
                scale_factor = 1.0
                if self.scroll_highlight_timer > 0:
                    # Hiệu ứng phóng to rồi thu nhỏ dần
                    progress = 1.0 - (self.scroll_highlight_timer / self.scroll_highlight_duration)
                    scale_bonus = (1.0 - progress) * 0.2  # Phóng to thêm 20% khi mới chọn
                    scale_factor = 1.0 + scale_bonus
                
                # Áp dụng tỷ lệ mới
                highlight_size = int((self.slot_size + 4) * scale_factor)
                highlight = pygame.transform.scale(
                    self.highlight_surface,
                    (highlight_size, highlight_size)
                )
                highlight_rect = highlight.get_rect(center=slot_rect.center)
                self.display_surface.blit(highlight, highlight_rect)
            
            # Vẽ vật phẩm với tỷ lệ nhất quán
            item_size = self.slot_size - 8  # Để lại khoảng trống trong ô
            if item in self.player.tools:
                item_surface = pygame.transform.scale(self.tools_surface[item], (item_size, item_size))
            else:
                item_surface = pygame.transform.scale(self.hotbar_surface[item], (item_size, item_size))
            
            # Hiệu ứng phóng to cho item được chọn khi cuộn
            if is_selected and self.scroll_highlight_timer > 0:
                # Tính toán tỷ lệ phóng to dựa trên thời gian đánh dấu
                progress = 1.0 - (self.scroll_highlight_timer / self.scroll_highlight_duration)
                scale_bonus = (1.0 - progress) * 0.15  # Phóng to thêm 15% khi mới chọn
                item_scale = 1.0 + scale_bonus
                
                # Áp dụng tỷ lệ mới
                scaled_size = int(item_size * item_scale)
                item_surface = pygame.transform.scale(item_surface, (scaled_size, scaled_size))
                
            item_rect = item_surface.get_rect(center=slot_rect.center)
            self.display_surface.blit(item_surface, item_rect)

    def display(self, dt=1/60):
        # Cập nhật thời gian chờ giữa các lần cuộn
        if self.scroll_cooldown > 0:
            self.scroll_cooldown -= dt
        
        # Cập nhật thời gian hiệu ứng đánh dấu
        if self.scroll_highlight_timer > 0:
            self.scroll_highlight_timer -= dt
        
        # Cập nhật chỉ số được chọn trước khi vẽ
        self.update_selected_index(self.selected_index)
        
        # Xóa bề mặt overlay
        self.overlay_surf.fill((0, 0, 0, 0))
        # Vẽ thanh công cụ
        self.draw_hotbar()
        self.update_hotbar()
        
        # Vẽ bề mặt overlay lên màn hình
        self.display_surface.blit(self.overlay_surf, (0, 0))

class Dialog:
    """Hệ thống hội thoại nâng cao cho tất cả NPC với kiểu dáng và tương tác tốt hơn"""
    def __init__(self, name, text, screen, avatar_path=None, npc_type=None):
        # Dữ liệu cơ bản
        self.name = name
        self.text = text
        self.screen = screen
        
        # Tính hệ số tỷ lệ dựa trên độ phân giải màn hình
        self.scale_factor = min(SCREEN_WIDTH / 1280, SCREEN_HEIGHT / 720)
        
        # Điều chỉnh font dựa trên kích thước màn hình
        font_size = int(20 * self.scale_factor)
        name_font_size = int(30 * self.scale_factor)
        
        self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', font_size)
        self.name_font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', name_font_size)
        
        # Tải tài nguyên giao diện hội thoại
        self.dialog_bg_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/dialog/dialog_bg.png').convert_alpha()
        self.dialog_text_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/dialog/dialog_text_box.png').convert_alpha()
        self.dialog_avatar_frame_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/dialog/dialog_avata_frame.png').convert_alpha()
        
        # Kiểu hội thoại dựa trên loại NPC
        self.npc_type = npc_type
        self.style = self._get_npc_style()
        
        # Avatar là tùy chọn
        self.avatar_surface = None
        if avatar_path:
            try:
                self.avatar_surface = pygame.image.load(avatar_path).convert_alpha()
            except:
                print(f"Không thể tải avatar từ: {avatar_path}")
        
        # Thông số đáp ứng - điều chỉnh dựa trên kích thước màn hình
        self.base_width = min(500 * self.scale_factor, SCREEN_WIDTH * 0.8)  # Tối đa 80% chiều rộng màn hình
        self.text_box_width = min(250 * self.scale_factor, self.base_width * 0.6)
        self.min_height = min(150 * self.scale_factor, SCREEN_HEIGHT * 0.2)
        
        # Vị trí - có thể tùy chỉnh
        self.position = "bottom"  # "top", "center", "bottom"
        self.dialog_bg_rect = self._calculate_dialog_position()
        self.dialog_text_rect = pygame.Rect(0, 0, self.text_box_width, self.min_height)
        
        # Thông số văn bản
        self.text_color = self.style['text_color']
        self.name_color = self.style['name_color']
        
        # Thông số hoạt ảnh
        self.current_text = ""
        self.text_index = 0
        self.animation_speed = 0.03  # Giá trị thấp hơn = nhanh hơn
        self.is_text_complete = False
        self.is_active = True
        self.next_indicator_visible = False
        self.animation_timer = 0
        
        # Đệm đáp ứng
        self.padding = {
            'text': int(30 * self.scale_factor),
            'box': int(20 * self.scale_factor),
        }
        
        # Hỗ trợ chuỗi hội thoại
        self.next_dialog = None
        self.dialog_chain = []
        self.current_dialog_index = 0
        
        # Hỗ trợ lựa chọn hội thoại
        self.choices = []
        self.selected_choice = 0
        self.in_choice_mode = False
        
        # Hiệu ứng âm thanh
        self.char_sound = None
        try:
            self.char_sound = pygame.mixer.Sound(f'{SOUND_PATH}/ui/dialog_char.wav')
            self.char_sound.set_volume(0.2)
        except:
            pass
            
        # Hỗ trợ kéo hội thoại
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # Hỗ trợ biểu cảm
        self.emote = None
        self.emote_surface = None
        self.emote_timer = 0
        self.emote_duration = 2.0  # số giây hiển thị biểu cảm
        
        # Hiệu ứng chuyển tiếp - TẮT
        self.fade_alpha = 0  # Bắt đầu hiển thị đầy đủ không làm mờ
        self.fade_in = False  # Tắt hiệu ứng hiện dần
        self.fade_out = False  # Tắt hiệu ứng ẩn dần
        self.fade_speed = 5  # Không sử dụng nhưng giữ để tương thích
        
        # Hoạt ảnh avatar
        self.avatar_bounce = 0
        self.avatar_bounce_dir = 1
        self.avatar_animation_speed = 0.1
        self.avatar_animation_timer = 0
        
        # Tương tác chuột
        self.next_indicator_rect = pygame.Rect(0, 0, 30, 30)
        
        # Tốc độ hiển thị văn bản
        self.typewriter_speeds = {
            "slow": 0.06,
            "normal": 0.03,
            "fast": 0.01,
            "instant": 0.001
        }
        
    def _get_npc_style(self):
        """Lấy kiểu hội thoại dựa trên loại NPC"""
        styles = {
            "mayor": {
                "text_color": (250, 250, 250),
                "name_color": (200, 170, 80),  # Vàng cho quyền lực
                "bg_color": (60, 40, 80, 220)
            },
            "trader": {
                "text_color": (250, 250, 250),
                "name_color": (80, 180, 80),  # Xanh lá cho thương mại
                "bg_color": (40, 60, 40, 220)
            },
            "farmer": {
                "text_color": (250, 250, 250),
                "name_color": (180, 120, 60),  # Nâu cho đất
                "bg_color": (60, 40, 20, 220)
            },
            "quest": {
                "text_color": (250, 250, 250),
                "name_color": (80, 120, 200),  # Xanh dương cho phiêu lưu
                "bg_color": (30, 40, 90, 220)
            },
            "special": {
                "text_color": (250, 250, 250),
                "name_color": (200, 100, 200),  # Tím cho đặc biệt
                "bg_color": (70, 30, 70, 220)
            },
        }
        
        # Kiểu mặc định
        default_style = {
            "text_color": (250, 250, 250),
            "name_color": (200, 100, 80),
            "bg_color": (30, 30, 40, 220)
        }
        
        return styles.get(self.npc_type, default_style)
    
    # Giữ tính toán vị trí hiện tại
    def _calculate_dialog_position(self):
        """Tính toán vị trí hội thoại dựa trên tùy chọn và kích thước màn hình"""
        if self.position == "top":
            return pygame.Rect(
                (SCREEN_WIDTH - self.base_width) // 2,
                20 * self.scale_factor,
                self.base_width,
                self.min_height
            )
        elif self.position == "center":
            return pygame.Rect(
                (SCREEN_WIDTH - self.base_width) // 2,
                (SCREEN_HEIGHT - self.min_height) // 2,
                self.base_width,
                self.min_height
            )
        else:  # bottom (mặc định)
            return pygame.Rect(
                50,
                50,
                self.base_width,
                self.min_height
            )
    
    def set_typing_speed(self, speed):
        """Đặt tốc độ hiển thị văn bản: 'slow', 'normal', 'fast', hoặc 'instant'"""
        if speed in self.typewriter_speeds:
            self.animation_speed = self.typewriter_speeds[speed]
        return self
    
    def set_emote(self, emote_name):
        """Thiết lập biểu cảm hiển thị trên avatar"""
        try:
            self.emote_surface = pygame.image.load(f'{GRAPHICS_PATH}/ui/emotes/{emote_name}.png').convert_alpha()
            self.emote = emote_name
            self.emote_timer = 0
        except:
            print(f"Không thể tải biểu cảm: {emote_name}")
        return self
        
    def set_position(self, position):
        """Đặt vị trí hội thoại: 'top', 'center', hoặc 'bottom'"""
        if position in ["top", "center", "bottom"]:
            self.position = position
            self.dialog_bg_rect = self._calculate_dialog_position()
            return True
        return False
        
    def add_dialog_to_chain(self, text):
        """Thêm hội thoại vào chuỗi cho hội thoại tuần tự"""
        self.dialog_chain.append(text)
        return self
        
    def set_choices(self, choices_list):
        """Thiết lập các lựa chọn hội thoại"""
        self.choices = choices_list
        self.in_choice_mode = True
        self.selected_choice = 0
        return self
    
    def handle_event(self, event):
        """Xử lý sự kiện đầu vào cho hội thoại"""
        if not self.is_active:
            return False
            
        # Kéo hộp hội thoại
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.dialog_bg_rect.collidepoint(event.pos):
                # Kiểm tra nếu nhấp vào chỉ báo tiếp theo
                if self.is_text_complete and self.next_indicator_rect.collidepoint(event.pos):
                    if self.in_choice_mode:
                        # Trả về lựa chọn đã chọn
                        choice = self.choices[self.selected_choice]
                        self.in_choice_mode = False
                        self.choices = []
                        return choice
                    else:
                        self.advance_dialog()
                        return True
                        
                # Kiểm tra nếu nhấp vào lựa chọn
                if self.in_choice_mode and self.is_text_complete:
                    choice_height = self.font.get_linesize()
                    choice_area_y = self.dialog_text_rect.top + self.padding['text'] + self.calculate_text_dimensions(self.current_text) + 20
                    
                    for i, choice in enumerate(self.choices):
                        choice_rect = pygame.Rect(
                            self.dialog_text_rect.left + self.padding['text'],
                            choice_area_y + i * choice_height,
                            self.text_box_width - (self.padding['text'] * 2),
                            choice_height
                        )
                        
                        if choice_rect.collidepoint(event.pos):
                            self.selected_choice = i
                            # Ngay lập tức chọn lựa chọn này
                            choice = self.choices[i]
                            self.in_choice_mode = False
                            self.choices = []
                            return choice
                
                # Nếu không nhấp vào chỉ báo tiếp theo hoặc lựa chọn, kéo hộp hội thoại
                self.dragging = True
                self.drag_offset = (
                    self.dialog_bg_rect.x - event.pos[0],
                    self.dialog_bg_rect.y - event.pos[1]
                )
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Cập nhật vị trí hội thoại khi kéo
                self.dialog_bg_rect.x = event.pos[0] + self.drag_offset[0]
                self.dialog_bg_rect.y = event.pos[1] + self.drag_offset[1]
                
                # Giữ hộp thoại trong giới hạn màn hình
                if self.dialog_bg_rect.left < 0:
                    self.dialog_bg_rect.left = 0
                if self.dialog_bg_rect.right > SCREEN_WIDTH:
                    self.dialog_bg_rect.right = SCREEN_WIDTH
                if self.dialog_bg_rect.top < 0:
                    self.dialog_bg_rect.top = 0
                if self.dialog_bg_rect.bottom > SCREEN_HEIGHT:
                    self.dialog_bg_rect.bottom = SCREEN_HEIGHT
                    
                return True
                
        # Con lăn chuột để điều hướng lựa chọn
        elif event.type == pygame.MOUSEWHEEL:
            if self.in_choice_mode and self.is_text_complete:
                delta = 1 if event.y < 0 else -1  # Đảo ngược hướng cho cảm giác tự nhiên
                self.selected_choice = (self.selected_choice + delta) % len(self.choices)
                return True
                
        # Tiến hội thoại bằng bàn phím
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if self.in_choice_mode and self.is_text_complete:
                    # Trả về lựa chọn đã chọn
                    choice = self.choices[self.selected_choice]
                    self.in_choice_mode = False
                    self.choices = []
                    return choice
                else:
                    self.advance_dialog()
                return True
                
            # Điều hướng lựa chọn
            elif self.in_choice_mode and self.is_text_complete:
                if event.key == pygame.K_UP:
                    self.selected_choice = (self.selected_choice - 1) % len(self.choices)
                    return True
                elif event.key == pygame.K_DOWN:
                    self.selected_choice = (self.selected_choice + 1) % len(self.choices)
                    return True
                    
        return False
    
    def update(self, dt):
        """Cập nhật hoạt ảnh và trạng thái hội thoại"""
        if not self.is_active:
            return
                
        # Cập nhật thời gian biểu cảm
        if self.emote_surface:
            self.emote_timer += dt
            if self.emote_timer >= self.emote_duration:
                self.emote = None
                self.emote_surface = None
                
        # Cập nhật hoạt ảnh avatar
        if self.avatar_surface:
            self.avatar_animation_timer += dt
            if self.avatar_animation_timer >= self.avatar_animation_speed:
                self.avatar_animation_timer = 0
                self.avatar_bounce += 0.5 * self.avatar_bounce_dir
                if abs(self.avatar_bounce) >= 2:
                    self.avatar_bounce_dir *= -1
                    
        # Hoạt ảnh văn bản
        if not self.is_text_complete:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                if self.text_index < len(self.text):
                    # Kiểm tra các ký tự điều khiển tốc độ văn bản
                    if self.text[self.text_index] == '{' and self.text_index + 1 < len(self.text):
                        if self.text[self.text_index+1] == 'p':  # Tạm dừng
                            self.animation_timer = -0.5  # Tạm dừng nửa giây
                            self.text_index += 2
                        elif self.text[self.text_index+1] == 'f':  # Nhanh
                            self.animation_speed = self.typewriter_speeds["fast"]
                            self.text_index += 2
                        elif self.text[self.text_index+1] == 's':  # Chậm
                            self.animation_speed = self.typewriter_speeds["slow"]
                            self.text_index += 2
                        elif self.text[self.text_index+1] == 'n':  # Bình thường
                            self.animation_speed = self.typewriter_speeds["normal"]
                            self.text_index += 2
                    
                    if self.text_index < len(self.text):
                        self.current_text += self.text[self.text_index]
                        self.text_index += 1
                        
                        # Phát âm thanh gõ mỗi 4 ký tự
                        if self.char_sound and self.text_index % 4 == 0:
                            self.char_sound.play()
                else:
                    self.is_text_complete = True
                    self.next_indicator_visible = True
        
        # Hoạt ảnh chỉ báo "tiếp theo"
        if self.is_text_complete:
            self.animation_timer += dt
            if self.animation_timer >= 0.5:  # Nhấp nháy nửa giây
                self.animation_timer = 0
                self.next_indicator_visible = not self.next_indicator_visible

    def draw(self):
        """Vẽ hộp hội thoại đáp ứng với lựa chọn có thể có"""
        if not self.is_active:
            return
            
        # Tính toán chiều cao văn bản để điều chỉnh kích thước
        if self.in_choice_mode and self.is_text_complete:
            # Thêm chiều cao cho lựa chọn
            total_text = self.current_text + "\n" + "\n".join([
                f"{'→ ' if i == self.selected_choice else '   '}{choice}" 
                for i, choice in enumerate(self.choices)
            ])
            text_height = self.calculate_text_dimensions(total_text)
        else:
            text_height = self.calculate_text_dimensions(self.current_text)
        
        # Tính toán chiều cao hộp với đệm
        text_box_height = max(self.min_height, text_height + (self.padding['text'] * 2))
        
        # Điều chỉnh nền hội thoại với kiểu tùy chỉnh
        total_height = text_box_height + self.padding['box'] * 2
        
        # Tạo nền màu tùy chỉnh theo kiểu NPC
        bg_surface = pygame.Surface((int(self.base_width), int(total_height)), pygame.SRCALPHA)
        bg_surface.fill(self.style['bg_color'])
        
        # Áp dụng góc bo tròn và viền
        radius = int(10 * self.scale_factor)
        rect = bg_surface.get_rect()
        pygame.draw.rect(bg_surface, self.style['bg_color'], rect, 0, radius)
        
        # Viền nổi bật cho hội thoại đặc biệt
        if self.npc_type in ["quest", "special"]:
            border_color = self.style['name_color']
            border_width = 2
        else:
            border_color = (100, 100, 100, 150)
            border_width = 1
            
        pygame.draw.rect(bg_surface, border_color, rect, int(border_width * self.scale_factor), radius)
        
        # Hiệu ứng phát sáng nhẹ bên trong
        if self.npc_type:
            glow_color = self.style['name_color']
            glow_alpha = 70
            glow_rect = rect.inflate(-4, -4)
            
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            glow_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(glow_surface, (*glow_color[:3], glow_alpha), glow_surface.get_rect(), 0, radius-1)
            
            # Áp dụng hiệu ứng làm mờ bằng cách thu nhỏ và phóng to (nếu đủ không gian)
            if glow_rect.width > 20 and glow_rect.height > 20:
                small_size = (glow_rect.width // 4, glow_rect.height // 4)
                blurred = pygame.transform.smoothscale(glow_surface, small_size)
                blurred = pygame.transform.smoothscale(blurred, (glow_rect.width, glow_rect.height))
                bg_surface.blit(blurred, (2, 2), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Nền hội thoại đã điều chỉnh tỷ lệ nếu sử dụng hình ảnh
        scaled_bg = pygame.transform.scale(
            self.dialog_bg_surface, 
            (int(self.base_width), int(total_height))
        )
        
        # Cập nhật kích thước khung hội thoại với kích thước mới
        self.dialog_bg_rect.width = self.base_width
        self.dialog_bg_rect.height = total_height
        
        # Điều chỉnh tỷ lệ hộp văn bản
        text_box_surface = pygame.transform.scale(
            self.dialog_text_surface,
            (int(self.text_box_width), int(text_box_height))
        )
        
        # Đặt vị trí hộp văn bản tương đối với nền hội thoại
        avatar_width = 0
        if self.avatar_surface:
            # Tính không gian cần thiết cho avatar
            avatar_width = self.dialog_bg_rect.width * 0.25
        
        # Đặt hộp văn bản bên phải avatar nếu có
        self.dialog_text_rect = text_box_surface.get_rect(
            midleft=(self.dialog_bg_rect.left + avatar_width + 20 * self.scale_factor,
                   self.dialog_bg_rect.centery)
        )

        # Vẽ nền hội thoại với kiểu tùy chỉnh hoặc hình ảnh
        if self.npc_type:
            self.screen.blit(bg_surface, self.dialog_bg_rect)
        else:
            self.screen.blit(scaled_bg, self.dialog_bg_rect)
        
        # Vẽ hộp văn bản
        self.screen.blit(text_box_surface, self.dialog_text_rect)

        # Vẽ avatar nếu có
        if self.avatar_surface:
            # Tính kích thước avatar tối ưu dựa trên kích thước hội thoại
            avatar_size = min(
                self.dialog_bg_rect.width * 0.2,
                self.dialog_bg_rect.height - 40 * self.scale_factor
            )
            
            # Tỷ lệ tối đa để tránh hiện tượng pixel hóa
            max_scale = 5
            base_size = self.avatar_surface.get_width()
            scale_ratio = min(avatar_size / base_size, max_scale)
            
            # Điều chỉnh tỷ lệ avatar với thêm đệm
            avatar_width = int(self.avatar_surface.get_width() * scale_ratio)
            avatar_height = int(self.avatar_surface.get_height() * scale_ratio)
            
            scaled_avatar = pygame.transform.scale(
                self.avatar_surface,
                (avatar_width, avatar_height)
            )
            
            # Định vị avatar với hoạt ảnh nẩy nhẹ
            avatar_x = self.dialog_bg_rect.left + self.dialog_bg_rect.width * 0.17  # Tăng từ 0.12 lên 0.15
            avatar_y = self.dialog_bg_rect.centery + self.avatar_bounce
            self.avatar_rect = scaled_avatar.get_rect(center=(avatar_x, avatar_y))
            
            # Vẽ avatar
            self.screen.blit(scaled_avatar, self.avatar_rect)
            
            # Điều chỉnh tỷ lệ và vị trí khung avatar với thêm đệm
            frame_padding = 30 * self.scale_factor  # Tăng đệm
            scaled_frame = pygame.transform.scale(
                self.dialog_avatar_frame_surface,
                (avatar_width + frame_padding, avatar_height + frame_padding)
            )
            frame_rect = scaled_frame.get_rect(center=self.avatar_rect.center)
            self.screen.blit(scaled_frame, frame_rect)
            
            # Lưu vị trí avatar để căn giữa tên
            self.avatar_center_x = avatar_x
            
            # Vẽ biểu cảm nếu đang hoạt động
            if self.emote_surface:
                emote_size = avatar_width * 0.8
                scaled_emote = pygame.transform.scale(
                    self.emote_surface,
                    (int(emote_size), int(emote_size))
                )
                emote_rect = scaled_emote.get_rect(
                    midbottom=(avatar_x, self.avatar_rect.top - 5)
                )
                self.screen.blit(scaled_emote, emote_rect)

        # Vẽ tên với kiểu - đã sửa để căn giữa trên avatar
        name_surface = self.name_font.render(self.name, True, self.name_color)

        # Đặt vị trí tên căn giữa trên avatar nếu avatar hiện diện
        if self.avatar_surface:
            name_x = self.avatar_center_x - name_surface.get_width() / 2  # Căn giữa trên avatar
            name_y = self.avatar_rect.top - 30 * self.scale_factor  # Đặt cao hơn trên avatar
        else:
            name_x = self.dialog_text_rect.left
            name_y = self.dialog_bg_rect.top + self.padding['box'] * 0.5

        # Vẽ nền tên để hiển thị tốt hơn
        name_bg = pygame.Surface((name_surface.get_width() + 20, name_surface.get_height() + 8), pygame.SRCALPHA)
        name_bg.fill((0, 0, 0, 180))
        name_bg_rect = name_bg.get_rect(center=(name_x + name_surface.get_width()/2, name_y + name_surface.get_height()/2))
        pygame.draw.rect(name_bg, (0, 0, 0, 180), name_bg.get_rect(), 0, 5)
        self.screen.blit(name_bg, name_bg_rect)

        # Vẽ hiệu ứng phát sáng cho tên
        name_glow = self.name_font.render(self.name, True, (*self.name_color[:3], 130))
        self.screen.blit(name_glow, (name_x + 1, name_y + 1))

        # Vẽ tên
        self.screen.blit(name_surface, (name_x, name_y))

        # Vẽ văn bản với ngắt dòng
        text_area_width = self.text_box_width - (self.padding['text'] * 2)
        text_start_x = self.dialog_text_rect.left + self.padding['text']
        text_start_y = self.dialog_text_rect.top + self.padding['text']
        
        # Vẽ văn bản thông thường
        self.render_text(self.current_text, text_start_x, text_start_y, text_area_width)

        # Vẽ lựa chọn nếu đang ở chế độ lựa chọn và văn bản đã hoàn thành
        if self.in_choice_mode and self.is_text_complete:
            choice_y = text_start_y + self.calculate_text_dimensions(self.current_text) + 20
            for i, choice in enumerate(self.choices):
                # Kiểu dáng khác nhau cho lựa chọn đã chọn
                if i == self.selected_choice:
                    color = (255, 255, 150)
                    prefix = "→ "
                    # Vẽ đánh dấu sau lựa chọn đã chọn
                    choice_width = self.font.size(prefix + choice)[0]
                    choice_height = self.font.get_linesize()
                    choice_bg = pygame.Surface((choice_width + 10, choice_height), pygame.SRCALPHA)
                    choice_bg.fill((255, 255, 255, 30))
                    self.screen.blit(choice_bg, (text_start_x - 5, choice_y))
                else:
                    color = (200, 200, 200)
                    prefix = "   "
                
                choice_text = prefix + choice
                choice_surf = self.font.render(choice_text, True, color)
                self.screen.blit(choice_surf, (text_start_x, choice_y))
                choice_y += self.font.get_linesize()

        # Vẽ chỉ báo tiếp theo với hình ảnh cải thiện nhưng kích thước nhỏ hơn
        if self.next_indicator_visible and not self.in_choice_mode:
            # Sử dụng chỉ báo nhỏ hơn
            indicator_size = int(12 * self.scale_factor)  # Giảm từ 20 xuống 12
            next_x = self.dialog_text_rect.right - self.padding['text']
            next_y = self.dialog_text_rect.bottom - self.padding['text']
            
            # Vẽ mũi tên nhấp nháy
            pulse = 0.7 + 0.3 * (1 if self.next_indicator_visible else 0)  # Nhịp đập giữa 0.7 và 1.0
            
            # Tạo tam giác chỉ báo
            points = [
                (next_x, next_y + indicator_size * pulse),
                (next_x - indicator_size * pulse, next_y),
                (next_x + indicator_size * pulse, next_y)
            ]
            
            # Vẽ bóng
            shadow_points = [(x+1, y+1) for x, y in points]  # Bù đắp bóng nhỏ hơn
            pygame.draw.polygon(self.screen, (0, 0, 0, 180), shadow_points)
            
            # Vẽ chỉ báo
            pygame.draw.polygon(self.screen, self.text_color, points)
            
            # Cập nhật rect chỉ báo cho phát hiện chuột
            self.next_indicator_rect = pygame.Rect(
                next_x - indicator_size, 
                next_y - indicator_size,
                indicator_size * 2,
                indicator_size * 2
            )

    # Các phương thức trợ giúp
    def calculate_text_dimensions(self, text):
        """Tính toán chiều cao cần thiết cho văn bản với chiều rộng cố định"""
        available_width = self.text_box_width - (self.padding['text'] * 2)
        lines = self.get_wrapped_text(text, available_width)
        text_height = len(lines) * self.font.get_linesize()
        return text_height

    def get_wrapped_text(self, text, max_width):
        """Phương thức trợ giúp lấy các dòng văn bản được bọc"""
        if not text:
            return [""]
            
        words = text.split(' ')
        lines = []
        current_line = words[0] if words else ""
        
        for word in words[1:]:
            test_line = current_line + ' ' + word
            # Kiểm tra xem thêm một từ có vượt quá chiều rộng không
            if self.font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        return lines
    
    def render_text(self, text, x, y, max_width):
        """Vẽ văn bản với ngắt dòng đơn giản"""
        lines = self.get_wrapped_text(text, max_width)
        line_height = self.font.get_linesize()
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.text_color)
            self.screen.blit(text_surface, (x, y + i * line_height))
    
    def advance_dialog(self):
        """Được gọi khi người chơi nhấn phím để tiến hội thoại"""
        if not self.is_text_complete:
            # Bỏ qua hoạt ảnh và hiển thị toàn bộ văn bản
            self.current_text = self.text
            self.is_text_complete = True
            self.next_indicator_visible = True
        elif self.current_dialog_index < len(self.dialog_chain):
            # Chuyển sang hội thoại tiếp theo trong chuỗi với hoạt ảnh
            self.text = self.dialog_chain[self.current_dialog_index]
            self.current_dialog_index += 1
            self.current_text = ""
            self.text_index = 0
            self.is_text_complete = False
            
            # Đặt lại tốc độ hoạt ảnh về mặc định
            self.animation_speed = self.typewriter_speeds["normal"]
        else:
            # Hội thoại hoàn thành, hủy kích hoạt ngay lập tức không làm mờ
            self.is_active = False
    
    def is_finished(self):
        """Kiểm tra xem hội thoại đã hoàn thành chưa"""
        return not self.is_active
        
    def get_rect(self):
        """Trả về hình chữ nhật của hội thoại để phát hiện va chạm"""
        return self.dialog_bg_rect

class Clock:
    def __init__(self, sky):
        self.display_surface = pygame.display.get_surface()
        self.sky = sky
        self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 32)
        self.day_counter = DayCounter()
        
        # Cài đặt vị trí
        self.paddingx = 20
        self.paddingy = 50
        self.position = (SCREEN_WIDTH - self.paddingx, self.paddingy)
        
    def display(self):
        # Lấy giờ và phút hiện tại
        total_hours = self.sky.time_of_day
        hours = int(total_hours)
        minutes = int((total_hours % 1) * 60)
        
        # Định dạng chuỗi thời gian (định dạng 12 giờ với AM/PM)
        period = "AM" if hours < 12 else "PM"
        if hours == 0:
            hours = 12
        elif hours > 12:
            hours -= 12
            
        time_str = f"{hours:02d}:{minutes:02d} {period}"
        
        # Tạo bề mặt văn bản
        text_surf = self.font.render(time_str, True, 'White')
        text_rect = text_surf.get_rect(topright=(self.position))
        
        # Thêm bóng để hiển thị tốt hơn
        shadow_surf = self.font.render(time_str, True, 'Black')
        shadow_rect = shadow_surf.get_rect(topright=(self.position[0] + 2, self.position[1] + 2))
        
        # Vẽ đồng hồ
        self.display_surface.blit(shadow_surf, shadow_rect)
        self.display_surface.blit(text_surf, text_rect)
        self.day_counter.display(self.display_surface)

class DayCounter:
    def __init__(self):
        self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 32)
        self.paddingx = 20
        self.paddingy = 20
        self.position = (SCREEN_WIDTH - self.paddingx, self.paddingy)
        self.day_count = 0

    def update(self, day_count):
        self.day_count = day_count

    def display(self, display_surface):
        text = f"Day: {self.day_count}"
        text_surf = self.font.render(text, False, (255,255,255))
        text_rect = text_surf.get_rect(topright=self.position)
        # Thêm bóng để hiển thị tốt hơn
        shadow_surf = self.font.render(text, True, 'Black')
        shadow_rect = shadow_surf.get_rect(topright=(self.position[0] + 2, self.position[1] + 2))
        
        display_surface.blit(shadow_surf, shadow_rect)
        display_surface.blit(text_surf, text_rect)

class FPSOverlay:
    def __init__(self):
        self.font = pygame.font.Font(None, 24)
    
    def draw(self, display_surface, clock):
        # Lấy FPS từ clock object
        fps = int(clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, (0, 255, 0))
        display_surface.blit(fps_text, (10, 10))
