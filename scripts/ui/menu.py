import sys
import pygame
import pygame.locals
from scripts.db.item_db import ItemDatabase, Item 
from scripts.helpers.support import import_folder
from scripts.ui.button import Button
from settings import *
from scripts.helpers.timer import Timer
from scripts.db.settings_db import SettingsDB
from scripts.db.player_db import PlayerDatabase
import copy
from settings import set_global_volume  # existing imports
import time

big_button_path = f"{GRAPHICS_PATH}/ui/button/90x27"
medium_button_path = f"{GRAPHICS_PATH}/ui/button/66x21"
small_button_path = f"{GRAPHICS_PATH}/ui/button/22x24"

class MainMenu:
	def __init__(self, screen):
		self.screen = screen
		self.font = pygame.font.Font(f'{FONT_PATH}/LycheeSoda.ttf', 50)

		set_global_volume(global_volume)
		self.running = True

		self.bg_images = import_folder(f'{GRAPHICS_PATH}/ui/main_menu_bg/')
		
		self.current_frame = 0
		self.animation_speed = 0.09
		self.animation_timer = 0
		
		scale = 2.5
		self.scaled_frames = []
		for frame in self.bg_images:
			image_width = frame.get_width()
			image_height = frame.get_height()
			scaled_frame = pygame.transform.scale(frame, (int(image_width * scale), int(image_height * scale)))
			self.scaled_frames.append(scaled_frame)

		def start_game():
			# Thay vì đặt self.running = False trực tiếp
			# Đặt một cờ để chuyển sang màn hình chọn nhân vật
			self.show_character_select = True
			self.running = False
		
		def open_settings():
			self.open_settings_menu()
		
		def exit_game():
			print('Exiting game!')
			pygame.quit()
			sys.exit()

		self.start_image = pygame.image.load(f'{big_button_path}/play_button.png').convert_alpha()
		self.settings_image = pygame.image.load(f'{big_button_path}/settings_button.png').convert_alpha()
		self.exit_image = pygame.image.load(f'{big_button_path}/exit_button.png').convert_alpha()

		self.start_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 65, self.start_image, 2.3, start_game)
		self.settings_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.settings_image, 2.3,  open_settings)
		self.exit_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120, self.exit_image, 2.3,  exit_game)

		self.show_character_select = False  # Thêm thuộc tính này

	def update(self, dt):
		# Update animation
		self.animation_timer += dt
		if self.animation_timer >= self.animation_speed:
			self.current_frame = (self.current_frame + 1) % len(self.scaled_frames)
			self.animation_timer = 0

		# Update buttons
		mouse_pos = pygame.mouse.get_pos()
		self.start_button.update(mouse_pos)
		self.settings_button.update(mouse_pos)
		self.exit_button.update(mouse_pos)

	def draw_menu(self):
		# Draw background
		self.screen.blit(self.scaled_frames[self.current_frame], (0,0))

		# Draw title
		title_text = self.font.render("Sprout Land", True, (255, 255, 255))
		title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
		self.screen.blit(title_text, title_rect)

			# Draw buttons
		self.start_button.draw(self.screen)
		self.settings_button.draw(self.screen)
		self.exit_button.draw(self.screen)

	def open_settings_menu(self):
		settings_menu = SettingsMenu(pygame.display.get_surface())
		settings_menu.running = True
		# Vòng lặp riêng cho settings; thoát khi nhấn Escape
		while settings_menu.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit(); sys.exit()
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					settings_menu.running = False
				settings_menu.handle_event(event)
			settings_menu.draw()
			pygame.display.update()

	def run(self, dt):
		self.update(dt)
		self.draw_menu()

class PauseMenu:
	def __init__(self, screen):
		self.screen = screen
		self.active = False
		self.resume_clicked = False
		self.to_home_active = False

		# Load background with transparency
		self.pause_bg = pygame.image.load(f'{GRAPHICS_PATH}/ui/pause_bg.png').convert_alpha()
		bg_scale = 3 
		self.pause_bg = pygame.transform.scale(
			self.pause_bg, 
			(int(self.pause_bg.get_width() * bg_scale),
			 int(self.pause_bg.get_height() * bg_scale))
		)
		self.pause_rect = self.pause_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

		# Load button images
		self.resume_image = pygame.image.load(f'{big_button_path}/resume_button.png').convert_alpha()
		self.exit_to_home_image = pygame.image.load(f'{big_button_path}/home_button.png').convert_alpha()

		# Create buttons with timers
		self.resume_button = Button(
			SCREEN_WIDTH // 2, 
			SCREEN_HEIGHT // 2 - 30,
			self.resume_image,
			2.1,
			self.toggle_pause
		)
		
		self.exit_to_home_button = Button(
			SCREEN_WIDTH // 2,
			SCREEN_HEIGHT // 2 + 30 ,
			self.exit_to_home_image,
			2.1,
			self.exit_to_home
		)

	def toggle_pause(self):
		self.active = False
		self.resume_clicked = True

	def exit_to_home(self):
		self.to_home_active = True
		self.active = False

	def update(self, dt):
		"""Update button states"""
		mouse_pos = pygame.mouse.get_pos()
		
		# Update all buttons
		self.resume_button.update(mouse_pos)
		self.exit_to_home_button.update(mouse_pos)

	def draw(self):
		"""Draw pause menu elements"""
		# Draw semi-transparent overlay
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(128)
		self.screen.blit(overlay, (0, 0))
		
		# Draw pause menu background
		self.screen.blit(self.pause_bg, self.pause_rect)
		
		# Draw buttons
		self.resume_button.draw(self.screen)
		self.exit_to_home_button.draw(self.screen)

	def run(self, dt):
		"""Run pause menu with proper state management"""
		self.active = True
		self.resume_clicked = False
		
		# Update and draw
		self.update(dt)
		self.draw()

		# Return state for main game loop
		if self.to_home_active:
			return "home"
		return None

class ShopMenu:
	def __init__(self, player, toggle_menu):
		self.player = player
		self.toggle_menu = toggle_menu
		self.display_surface = pygame.display.get_surface()
		self.font = pygame.font.Font(f'{FONT_PATH}/LycheeSoda.ttf', 30)
		self.items_data = self.load_items_from_db()

		# Options
		self.width = 600
		self.space = 12
		self.padding = 10

		# Entries
		self.trade_options_dict = {}
		for item in self.items_data:
			if item.item_name not in self.trade_options_dict:
				self.trade_options_dict[item.item_name] = item

		self.trade_options = list(self.trade_options_dict.values()) 
		self.batch_trade = False
		
		# Thêm biến điều khiển cuộn
		self.visible_items = 6  # Số lượng items hiện cùng lúc
		self.scroll_offset = 0  # Vị trí bắt đầu hiển thị
		self.scrolling = False  # Đánh dấu đang cuộn
		self.scroll_drag_start = 0  # Vị trí bắt đầu kéo
		self.need_scroll = len(self.trade_options) > self.visible_items  # Kiểm tra có cần cuộn không

		self.setup()

		# Movement
		self.index = 0
		self.timer = Timer(200)

		# Scaled icons (adjust the size multiplier as needed)
		scale_factor = 0.5
		self.icons = {}
		for item in self.trade_options:
			original_img = pygame.image.load(f'{GRAPHICS_PATH}/items/{item.item_name.lower()}.png').convert_alpha()
			scaled_width = int(original_img.get_width() * scale_factor)
			scaled_height = int(original_img.get_height() * scale_factor)
			self.icons[item.item_name] = pygame.transform.scale(original_img, (scaled_width, scaled_height))
		original_money = pygame.image.load(f'{GRAPHICS_PATH}/items/coins.png').convert_alpha()
		money_scaled_width = int(original_money.get_width() * scale_factor)
		money_scaled_height = int(original_money.get_height() * scale_factor)
		self.money_icon = pygame.transform.scale(original_money, (money_scaled_width, money_scaled_height))		

		self.last_mouse_pos = pygame.mouse.get_pos()
		self.mouse_moved = False
		self.selected_item = None
		self.buy_button_hover = False
		self.sell_button_hover = False
		self.hover_index = -1

	def load_items_from_db(self):
		return ItemDatabase.get_all_items()

	def display_money(self):
		text_surf = self.font.render(f'{self.player.inventory.get_item('coins').quantity}', False, 'Black')
		
		# Calculate positions and sizes for the combined background
		padding = 15  # Padding around the elements
		icon_text_spacing = 10  # Space between icon and text
		
		# Position the background at the top center of the screen
		bg_width = text_surf.get_width() + self.money_icon.get_width() + icon_text_spacing + (padding * 2)
		bg_height = max(text_surf.get_height(), self.money_icon.get_height()) + (padding * 2)
		bg_left = SCREEN_WIDTH / 2 + bg_width + 100
		bg_top = 20
		
		# Create and draw the background rectangle
		bg_rect = pygame.Rect(bg_left, bg_top, bg_width, bg_height)
		pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 0, 8)
		pygame.draw.rect(self.display_surface, (0, 0, 0), bg_rect, 3, 8)
		
		# Position the icon to the left inside the rectangle
		icon_rect = self.money_icon.get_rect(
			midleft=(bg_rect.left + padding, bg_rect.centery)
		)
		self.display_surface.blit(self.money_icon, icon_rect)
		
		# Position the text to the right of the icon
		text_rect = text_surf.get_rect(
			midleft=(icon_rect.right + icon_text_spacing, bg_rect.centery)
		)
		self.display_surface.blit(text_surf, text_rect)

	def buy_seletected_item(self):
		"""Handle buying items with batch support"""
		if not self.selected_item:
			return

		amount = 10 if self.batch_trade else 1
		total_cost = self.selected_item.get_buy_price() * amount

		if self.player.inventory.get_item('coins').quantity >= total_cost:			
			self.player.add_item(self.selected_item, amount)
			self.player.remove_item('coins', total_cost)
			# Play purchase sound or show feedback here

		if hasattr(self.player, 'mission_manager') and self.player.mission_manager:
			self.player.mission_manager.update_missions_by_action('buy', self.selected_item.item_name.replace(' seeds', ''), amount)
			print(self.selected_item.item_name)


	def sell_selected_item(self):
		"""Handle selling items with batch support"""
		if not self.selected_item:
			return

		current_item = self.player.inventory.get_item(self.selected_item.item_name)
		if not current_item:
			return

		amount = 10 if self.batch_trade else 1
		if current_item.quantity >= amount:
			self.player.remove_item(self.selected_item.item_name, amount)
			# self.player.money += self.selected_item.get_sell_price() * amount
				
			self.player.remove_item('coins', -self.selected_item.get_sell_price() * amount)
			# Play sell sound or show feedback here

		if hasattr(self.player, 'mission_manager') and self.player.mission_manager:
			self.player.mission_manager.update_missions_by_action('sell', self.selected_item.item_name, amount)


	def setup(self):
		self.text_surfs = []
		self.buy_buttons = []
		self.sell_buttons = []
		
		# Tính toán chiều cao của một mục
		for item in self.trade_options:
			text_surf = self.font.render(item.item_name, False, 'Black')
			self.text_surfs.append(text_surf)
		
		# Điều chỉnh tính toán chiều cao dựa trên số lượng hiển thị tối đa
		self.item_height = self.text_surfs[0].get_height() + (self.padding * 2)
		self.total_item_height = self.item_height + self.space
		
		# Điều chỉnh tổng chiều cao khi có nhiều mục
		display_count = min(len(self.trade_options), self.visible_items)
		self.total_height = display_count * self.total_item_height - self.space  # Trừ khoảng trống cuối cùng
		
		self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
		self.main_rect = pygame.Rect(SCREEN_WIDTH - self.width - 100, self.menu_top, self.width, self.total_height)
		
		# Tạo các thành phần của thanh cuộn
		if self.need_scroll:
			self.scroll_track_width = 20
			self.scroll_track_rect = pygame.Rect(
				self.main_rect.right + 10, 
				self.main_rect.top,
				self.scroll_track_width,
				self.total_height
			)
			
			# Tính toán kích thước của thanh kéo (handle)
			handle_ratio = min(1.0, self.visible_items / len(self.trade_options))
			self.scroll_handle_height = max(30, int(self.scroll_track_rect.height * handle_ratio))
			self.scroll_handle_rect = pygame.Rect(
				self.scroll_track_rect.left,
				self.scroll_track_rect.top,
				self.scroll_track_width,
				self.scroll_handle_height
			)
		
		# Header row text surfaces
		self.header_name = self.font.render('Bonnie The Trader', False, 'Dark Green')
		self.header_price = self.font.render('Sell/Buy', False, 'Black')
		self.header_amount = self.font.render('Amount', False, 'Black')

		# Button
		buy_btn_surf = pygame.image.load(f'{GRAPHICS_PATH}/ui/shop_menu/buy_button_off.png').convert_alpha()
		sell_btn_surf = pygame.image.load(f'{GRAPHICS_PATH}/ui/shop_menu/sell_button_off.png').convert_alpha()
		# Button
		buy_btn_surf_on = pygame.image.load(f'{GRAPHICS_PATH}/ui/shop_menu/buy_button_on.png').convert_alpha()
		sell_btn_surf_on = pygame.image.load(f'{GRAPHICS_PATH}/ui/shop_menu/sell_button_on.png').convert_alpha()
		
		buy_button = Button(0, 0, buy_btn_surf, 1.5, self.buy_seletected_item, None, None, buy_btn_surf_on)
		sell_button = Button(0, 0, sell_btn_surf, 1.5, self.sell_selected_item, None, None, sell_btn_surf_on)

		self.buy_buttons.append(buy_button)
		self.sell_buttons.append(sell_button)

	def handle_scroll(self, event):
		"""Xử lý các sự kiện cuộn"""
		if not self.need_scroll:
			return
			
		# Xử lý cuộn chuột
		if event.type == pygame.MOUSEWHEEL:
			direction = -event.y  # Đảo ngược hướng cuộn để cảm thấy tự nhiên hơn
			max_offset = max(0, len(self.trade_options) - self.visible_items)
			self.scroll_offset = max(0, min(self.scroll_offset + direction, max_offset))
			self.update_scroll_handle_position()
			
		# Xử lý kéo thanh cuộn
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1 and self.scroll_track_rect.collidepoint(event.pos):
				self.scrolling = True
				# Xác định chính xác vị trí bắt đầu kéo
				if self.scroll_handle_rect.collidepoint(event.pos):
					self.scroll_drag_start = event.pos[1] - self.scroll_handle_rect.top
				else:
					# Nhấp vào đường cuộn - di chuyển handle đến gần vị trí này
					self.scroll_handle_rect.centery = event.pos[1]
					self.scroll_drag_start = self.scroll_handle_height // 2
					# Cập nhật vị trí cuộn
					self.update_scroll_offset_from_handle()
				
		elif event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1:
				self.scrolling = False
				
		elif event.type == pygame.MOUSEMOTION:
			if self.scrolling:
				# Di chuyển thanh kéo theo chuột
				new_top = event.pos[1] - self.scroll_drag_start
				# Giới hạn trong phạm vi đường cuộn
				new_top = max(self.scroll_track_rect.top, 
							 min(new_top, self.scroll_track_rect.bottom - self.scroll_handle_height))
				self.scroll_handle_rect.top = new_top
				# Cập nhật vị trí cuộn dựa trên vị trí thanh kéo
				self.update_scroll_offset_from_handle()
	
	def update_scroll_handle_position(self):
		"""Cập nhật vị trí thanh kéo dựa trên scroll_offset"""
		if not self.need_scroll:
			return
			
		max_offset = max(1, len(self.trade_options) - self.visible_items)
		scroll_ratio = self.scroll_offset / max_offset
		
		# Tính toán vị trí dựa trên tỷ lệ cuộn
		handle_travel = self.scroll_track_rect.height - self.scroll_handle_height
		self.scroll_handle_rect.top = int(self.scroll_track_rect.top + handle_travel * scroll_ratio)
	
	def update_scroll_offset_from_handle(self):
		"""Cập nhật scroll_offset dựa trên vị trí của thanh kéo"""
		if not self.need_scroll:
			return
			
		# Tính tỷ lệ vị trí của handle trong track
		handle_travel = self.scroll_track_rect.height - self.scroll_handle_height
		if handle_travel <= 0:
			scroll_ratio = 0
		else:
			scroll_ratio = (self.scroll_handle_rect.top - self.scroll_track_rect.top) / handle_travel
		
		# Chuyển đổi tỷ lệ này thành vị trí cuộn
		max_offset = max(0, len(self.trade_options) - self.visible_items)
		self.scroll_offset = min(max_offset, round(scroll_ratio * max_offset))

	def show_entry(self, text_surf, amount, price, top, selected, icon):
		bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2))

		# Background
		pygame.draw.rect(self.display_surface, (230, 230, 230), bg_rect, 0, 6)

		# Icon - adjust positioning for larger icons
		icon_rect = icon.get_rect(midleft=(self.main_rect.left + 20, bg_rect.centery))
		self.display_surface.blit(icon, icon_rect)

		# Item Name - increased offset from icon
		text_rect = text_surf.get_rect(midleft=(icon_rect.right + 15, bg_rect.centery))
		self.display_surface.blit(text_surf, text_rect)

		# Item Amount
		amount_surf = self.font.render(str(amount), False, 'Black')
		amount_rect = amount_surf.get_rect(center=(self.main_rect.centerx + 150, bg_rect.centery))
		self.display_surface.blit(amount_surf, amount_rect)

		# Item Price
		price_surf = self.font.render(str(price), False, 'Black')
		price_rect = price_surf.get_rect(center=(self.main_rect.centerx, bg_rect.centery))
		self.display_surface.blit(price_surf, price_rect) 

	   
		self.buy_buttons[0].rect.center = (bg_rect.right - 30, bg_rect.centery)
		self.sell_buttons[0].rect.center = (bg_rect.right - self.sell_buttons[0].image.get_width() * 2, bg_rect.centery)

		# Position the money icon next to price
		money_and_text_padding = 5
		icon_rect = self.money_icon.get_rect(midleft=(price_rect.right + money_and_text_padding, bg_rect.centery))
		self.display_surface.blit(self.money_icon, icon_rect)
		
		# Highlight Selected Item
		if selected:
			self.selected_item = self.trade_options[self.index]
			pygame.draw.rect(self.display_surface, (255, 215, 0), bg_rect, 4, 6)  
			pygame.draw.rect(self.display_surface, (0, 0, 0), bg_rect.inflate(4, 4), 2, 6)  
			
			# Draw buttons
			self.buy_buttons[0].rect.center = (bg_rect.right - 30, bg_rect.centery)
			self.sell_buttons[0].rect.center = (bg_rect.right - self.sell_buttons[0].image.get_width() * 2, bg_rect.centery)
			
			# Update button states for current item
			mouse_pos = pygame.mouse.get_pos()
			self.buy_buttons[0].update(mouse_pos)
			self.sell_buttons[0].update(mouse_pos)
			
			
			# Draw buttons first
			self.buy_buttons[0].draw(self.display_surface)
			self.sell_buttons[0].draw(self.display_surface)


	def display_header(self):
		# Create a header row above the items
		padding = 40
		header_height = self.font.get_height() + (self.padding * 2)
		header_top = self.main_rect.top - header_height - self.space
		header_rect = pygame.Rect(self.main_rect.left - padding / 2, header_top, self.width + padding, header_height)
		
		# Draw header background
		pygame.draw.rect(self.display_surface, (200, 200, 200), header_rect, 0, 6)
		pygame.draw.rect(self.display_surface, (0, 0, 0), header_rect, 2, 6)
		
		# Position and draw the "Name" header
		item_rect = self.header_name.get_rect(midleft=(self.main_rect.left, header_rect.centery))
		self.display_surface.blit(self.header_name, item_rect)
		
		# Position and draw the "Price" header
		price_rect = self.header_price.get_rect(center=(self.main_rect.centerx, header_rect.centery))
		self.display_surface.blit(self.header_price, price_rect)
		
		# Position and draw the "Amount" header
		amount_rect = self.header_amount.get_rect(center=(self.main_rect.centerx + 150, header_rect.centery))
		self.display_surface.blit(self.header_amount, amount_rect)

	def update(self, dt):
		self.timer.update()
		
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == keys_bind['action']['batch trade']:
					self.batch_trade = True
			if event.type == pygame.KEYUP:
				if event.key == keys_bind['action']['batch trade']:
					self.batch_trade = False
			
			# Xử lý sự kiện cuộn
			self.handle_scroll(event)
		
		# Semi-transparent background
		menu_bg = pygame.Surface((self.main_rect.width + 20, self.main_rect.height + 20), pygame.SRCALPHA)
		menu_bg.fill((50, 50, 50, 180)) 
		self.display_surface.blit(menu_bg, (self.main_rect.left - 10, self.main_rect.top - 10))
		
		# Display header and money
		self.display_header()
		self.display_money()
		
		# Update mouse position and hovering
		mouse_pos = pygame.mouse.get_pos()
		
		# Draw items and handle mouse hover - CHỈ HIỂN THỊ CÁC MỤC TRONG PHẠM VI CUỘN
		visible_range = range(self.scroll_offset, 
							 min(self.scroll_offset + self.visible_items, len(self.text_surfs)))
		
		for idx, text_index in enumerate(visible_range):
			# Tính toán vị trí top dựa trên chỉ số hiển thị, không phải chỉ số thực tế
			top = self.main_rect.top + idx * (self.text_surfs[text_index].get_height() + (self.padding * 2) + self.space)
			item_name = self.trade_options[text_index].item_name
			
			# Tính toán vị trí entry trong viewport
			entry_rect = pygame.Rect(
				self.main_rect.left, 
				top, 
				self.width, 
				self.text_surfs[text_index].get_height() + (self.padding * 2)
			)
			
			# Kiểm tra hover chuột
			if entry_rect.collidepoint(mouse_pos):
				self.hover_index = text_index
				self.index = text_index
			
			# Lấy số lượng item
			amount = 0
			for inv_item in self.player.inventory.items:
				if isinstance(inv_item, Item) and inv_item.item_name == item_name:
					amount = inv_item.quantity
					break

			price = f'{self.trade_options[text_index].get_sell_price()}/{self.trade_options[text_index].get_buy_price()}'
			item_icon = self.icons[item_name]

			# Vẽ entry
			self.show_entry(
				top=top,
				text_surf=self.text_surfs[text_index],
				amount=amount,
				price=price,
				selected=self.index == text_index,
				icon=item_icon
			)
		
		# Vẽ thanh cuộn nếu cần
		if self.need_scroll:
			# Vẽ đường cuộn
			pygame.draw.rect(self.display_surface, (100, 100, 100, 150), self.scroll_track_rect, 0, 5)
			
			# Vẽ thanh kéo với hiệu ứng sáng hơn nếu đang kéo
			handle_color = (200, 200, 200, 200) if self.scrolling else (150, 150, 150, 180)
			pygame.draw.rect(self.display_surface, handle_color, self.scroll_handle_rect, 0, 5)
			
			# Vẽ viền cho thanh kéo
			pygame.draw.rect(self.display_surface, (50, 50, 50, 150), self.scroll_handle_rect, 2, 5)
			
			# Vẽ các nút mũi tên ở đầu và cuối thanh cuộn
			arrow_size = 10
			# Mũi tên lên
			pygame.draw.polygon(self.display_surface, (200, 200, 200),
							 [(self.scroll_track_rect.centerx, self.scroll_track_rect.top + 5),
							  (self.scroll_track_rect.left + 5, self.scroll_track_rect.top + arrow_size + 5),
							  (self.scroll_track_rect.right - 5, self.scroll_track_rect.top + arrow_size + 5)])
			
			# Mũi tên xuống
			pygame.draw.polygon(self.display_surface, (200, 200, 200),
							 [(self.scroll_track_rect.centerx, self.scroll_track_rect.bottom - 5),
							  (self.scroll_track_rect.left + 5, self.scroll_track_rect.bottom - arrow_size - 5),
							  (self.scroll_track_rect.right - 5, self.scroll_track_rect.bottom - arrow_size - 5)])

class SettingsMenu:
	def __init__(self, display_surface):
		self.display_surface = display_surface
		self.width = 600
		self.height = 400
		self.paddingx = 130
		self.paddingy = 80
		self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 30)
		self.keys_bind = {}
		self.move_keybind_buttons = {}
		# Load current global volume from settings
		self.volume = SettingsDB.get_settings()['volume']
		self.old_volume = self.volume 
		
		self.volume_surfs = import_folder(f'{GRAPHICS_PATH}/ui/settings_menu/volume/levels/')
		self.muted = False
		
		# Instead of referencing KEY_BIND directly, create a deep copy
		self.keybinds = copy.deepcopy(keys_bind)
		# This copy is temporary and will be persisted only on confirm.
		self.keybind_buttons = {}
		self.selected_keybind = None
		start_y = self.paddingy + 300

		 # Vị trí khởi tạo theo chiều dọc cho cả hai cột
		start_y_move = self.paddingy + 100
		# Xác định vị trí cột: cột action giữ bên trái và cột move bên phải
		self.action_column_x = self.paddingx
		self.move_column_x = self.paddingx + 250
		
		self.keybind_image = pygame.image.load(f'{GRAPHICS_PATH}/ui/settings_menu/key_bind_text.png')
		self.keybind_surf = pygame.transform.scale(self.keybind_image, (100, 30))
		for action, key in self.keybinds['action'].items():
			keybind_rect = self.keybind_surf.get_rect(top = start_y, right = self.paddingx)
			self.keybind_buttons[action] = keybind_rect
			start_y += 50
				# Tạo ô cho keybind trong mục "move"
		for move, key in self.keybinds['move'].items():
			rect = self.keybind_surf.get_rect(top=start_y_move, left=self.move_column_x)
			self.move_keybind_buttons[move] = rect
			start_y_move += 50

		self.cursor_img = pygame.image.load(f"{GRAPHICS_PATH}/mouse/Triangle Mouse icon 1.png").convert_alpha()
		# Create the Back button (used to exit settings)
		self.back_surf = pygame.image.load(f"{small_button_path}/exit_button_off.png").convert_alpha()
		self.back_surf_scaled = pygame.transform.scale_by(self.back_surf, 1.6)
		self.back_button = Button(80, SCREEN_HEIGHT - 75, self.back_surf_scaled, 1.5, self.exit_settings)

		# Setup volume control buttons (code omitted for brevity)
		# Nút tăng âm lượng 
		self.volume_up_button_off_surf = pygame.image.load(f'{small_button_path}/volume_up_button_off.png')
		self.volume_up_button_on_surf = pygame.image.load(f'{small_button_path}/volume_up_button_on.png')
		
		# Nút giảm âm lượng
		self.volume_down_button_off_surf = pygame.image.load(f'{small_button_path}/volume_down_button_off.png')
		self.volume_down_button_on_surf = pygame.image.load(f'{small_button_path}/volume_down_button_on.png')
		
		self.volume_up_surf_off = pygame.transform.scale_by(self.volume_up_button_off_surf, 1.6)
		self.volume_down_surf_off = pygame.transform.scale_by(self.volume_down_button_off_surf, 1.6)
		
		self.volume_up_surf_on = pygame.transform.scale_by(self.volume_up_button_on_surf, 1.6)
		self.volume_down_surf_on = pygame.transform.scale_by(self.volume_down_button_on_surf, 1.6)
		
		# Nút tắt âm lượng
		# Vẽ trạng thái mute
		self.mute_surf_on = pygame.image.load(f'{small_button_path}/mute_button_on.png')
		self.mute_surf_off = pygame.image.load(f'{small_button_path}/mute_button_off.png')
		
		self.mute_surf_on = pygame.transform.scale_by(self.mute_surf_on, 1.6)
		self.mute_surf_off = pygame.transform.scale_by(self.mute_surf_off, 1.6)


		# Tạo nút
		self.volume_up_button = Button(0, 100, self.volume_up_surf_off, 1.5, self.increase_volume, pressed_image= self.volume_up_surf_on)
		self.volume_down_button = Button(0, 100, self.volume_down_surf_off, 1.5, self.decrease_volume,pressed_image= self.volume_down_surf_on)
		self.volume_mute_button = Button(0, 100, self.mute_surf_off, 1.5, self.mute_volume)
		
		self.running = True

	def increase_volume(self):
		if self.volume < 9:
			self.volume += 1
			self.muted = False

	def decrease_volume(self):
		if self.volume > 0:
			self.volume -= 1
		if self.volume == 0:
			self.muted = True
		else:
			self.muted = False

	def mute_volume(self):
		self.volume = 0
		self.muted = not self.muted
		if not self.muted:
			self.increase_volume()

	def exit_settings(self):
		# Backup current (original) keybinds in case the user cancels
		original_keybinds = copy.deepcopy(keys_bind)

		def on_confirm():
			# Save the modified keybinds along with volume to the database
			SettingsDB.save_setting(self.volume, self.keybinds)
			 # Immediately update the global KEY_BIND so new keys are used by the game
			global keys_bind
			keys_bind = self.keybinds
			set_global_volume(self.volume)
			print("Settings saved and new keybinds applied.")
			self.running = False  

		def on_cancel():
			# Revert keybind changes by discarding the temporary changes
			self.keybinds = original_keybinds
			self.volume = self.old_volume
			set_global_volume(self.old_volume)
			print("Settings not saved.")
			

			self.running = False

		popup = ConfirmationPopup(self.display_surface, on_confirm, on_cancel)
		while popup.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit(); sys.exit()
				popup.handle_event(event)
			popup.draw()
			pygame.display.update()

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			mouse_pos = event.pos
			# Kiểm tra cột action
			for action, rect in self.keybind_buttons.items():
				if rect.collidepoint(mouse_pos):
					self.selected_keybind = ('action', action)
					print(f"Selected action keybind for {action}")
			# Kiểm tra cột move
			for move, rect in self.move_keybind_buttons.items():
				if rect.collidepoint(mouse_pos):
					self.selected_keybind = ('move', move)
					print(f"Selected move keybind for {move}")
		elif event.type == pygame.KEYDOWN:
			if self.selected_keybind is not None:
				column, key_category = self.selected_keybind
				self.keybinds[column][key_category] = event.key
				print(f"Keybind for {column} '{key_category}' changed to {pygame.key.name(event.key)}")
				self.selected_keybind = None

	def draw(self):
		mouse_pos = pygame.mouse.get_pos()
		# Draw a translucent background
		self.display_surface.fill((0, 0, 0))
		self.settings_surf = pygame.image.load(f'{GRAPHICS_PATH}/ui/settings_menu/settings_bg.png')
		self.settings_surf_scaled = pygame.transform.scale(self.settings_surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
		self.settings_rect = self.settings_surf_scaled.get_rect()
		self.display_surface.blit(self.settings_surf_scaled, self.settings_rect)
		
		# Draw keybind buttons
		for action, rect in self.keybind_buttons.items():
			# Render text surfaces
			key_name = pygame.key.name(self.keybinds['action'][action])
			key_action = self.font.render(f"{action}:", False, (243,229,194))
			key_text = self.font.render(f"{key_name}", False, (255, 255, 255))
			# Position action text
			keybind_action_rect = key_action.get_rect(top=rect.top, right=self.settings_rect.centerx - 400)
			
			# Get the width of the key text plus padding
			text_width = key_text.get_width()
			padding = 20  # Padding on both sides
			
			# Scale background surface based on text width
			keybind_surf_scaled = pygame.transform.scale(
				self.keybind_surf,
				(max(100,text_width) + padding, 30)  # Height remains fixed at 30
			)
			
			# Position background and text
			keybind_background_rect = keybind_surf_scaled.get_rect(
				top=rect.top,
				left=keybind_action_rect.right + 10
			)
			
			# Center the key text in its background
			keybind_key = key_text.get_rect(
				center=keybind_background_rect.center
			)
			rect.centerx = keybind_background_rect.centerx
			# Draw everything
			self.display_surface.blit(key_action, keybind_action_rect)
			self.display_surface.blit(keybind_surf_scaled, keybind_background_rect)
			self.display_surface.blit(key_text, keybind_key)
			# pygame.draw.rect(self.display_surface, (255, 255, 255), rect, 2)
			if self.selected_keybind and self.selected_keybind == ('action', action):
				pygame.draw.rect(self.display_surface, (247, 235, 170), keybind_background_rect, 3)
		# Vẽ cột keybind cho move
		for move, rect in self.move_keybind_buttons.items():
			key_name = pygame.key.name(self.keybinds['move'][move])
			key_move_surf = self.font.render(f"move {move}:", False, (243,229,194))
			key_text_surf = self.font.render(f"{key_name}", False, (255, 255, 255))
			# Đặt text (đặt theo cột move)
			move_rect = key_move_surf.get_rect(top=rect.top, right=self.settings_rect.centerx - 400)
			text_width = key_text_surf.get_width()
			padding = 20
			bg_width = max(100, text_width) + padding
			keybind_bg = pygame.transform.scale(self.keybind_surf, (bg_width, 30))
			bg_rect = keybind_bg.get_rect(top=rect.top, left=move_rect.right + 10)
			key_text_rect = key_text_surf.get_rect(center=bg_rect.center)
			self.display_surface.blit(key_move_surf, move_rect)
			self.display_surface.blit(keybind_bg, bg_rect)
			self.display_surface.blit(key_text_surf, key_text_rect)
			rect.centerx = bg_rect.centerx

			# pygame.draw.rect(self.display_surface, (255, 255, 255), rect, 2)
			if self.selected_keybind and self.selected_keybind == ('move', move):
				pygame.draw.rect(self.display_surface, (247, 235, 170), bg_rect, 3)
		keybind_title = self.font.render("Key Bindings", False, (118, 109, 170))
		keybind_title_rect = keybind_title.get_rect(centerx=self.settings_rect.centerx - 400, top=self.paddingy + 50)
		self.display_surface.blit(keybind_title, keybind_title_rect)
		volume_title = self.font.render("Volume", False, (118, 109, 170))
		volume_title_rect = volume_title.get_rect(centerx=self.settings_rect.centerx, top= 50)
		self.display_surface.blit(volume_title, volume_title_rect)
		# Draw volume and volume buttons (code omitted for brevity)
		# Tạo thanh âm lượng
		self.volume_surf = self.volume_surfs[self.volume]
		self.volume_surf_scaled = pygame.transform.scale_by(self.volume_surf, 4)
		self.volume_rect = self.volume_surf_scaled.get_rect(centerx = self.settings_rect.centerx, centery = 120)
		
		# Cho nó ở 2 bên cạnh của thanh âm lượng
		if self.muted:
			self.volume_mute_button.image = pygame.transform.scale_by(self.mute_surf_on, 1.6)
		else:
			self.volume_mute_button.image =  pygame.transform.scale_by(self.mute_surf_off, 1.6)
		
		self.volume_up_button.rect.left = self.volume_rect.right + 5
		self.volume_down_button.rect.right = self.volume_rect.left - 5
		self.volume_mute_button.rect.left = self.volume_up_button.rect.right + 5
		
		self.volume_up_button.rect.top = self.volume_rect.top -	2 
		self.volume_down_button.rect.top = self.volume_up_button.rect.top
		self.volume_mute_button.rect.top = self.volume_up_button.rect.top
		
		self.volume_up_button.draw(self.display_surface)
		self.volume_down_button.draw(self.display_surface)
		self.volume_mute_button.draw(self.display_surface)
		
		self.volume_up_button.update(mouse_pos)
		self.volume_down_button.update(mouse_pos)
		self.volume_mute_button.update(mouse_pos)
		
		self.display_surface.blit(self.volume_surf_scaled, self.volume_rect)

		self.back_button.update(mouse_pos)
		self.back_button.draw(self.display_surface)
		self.display_surface.blit(self.cursor_img, mouse_pos)
		
		# Optionally update global volume for sounds
		set_global_volume(self.volume)

class ConfirmationPopup:
	def __init__(self, display_surface, on_confirm, on_cancel):
		self.display_surface = display_surface
		self.on_confirm = on_confirm
		self.on_cancel = on_cancel
		self.font = pygame.font.Font(f'{FONT_PATH}/LycheeSoda.ttf', 30)
		self.message = "Save changes to settings?"
		self.message_surf = self.font.render(self.message, True, (255, 255, 255))
		self.message_rect = self.message_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))

		self.cursor_img = pygame.image.load(f"{GRAPHICS_PATH}/mouse/Triangle Mouse icon 1.png").convert_alpha()
		# Create Yes and No buttons. Adjust image paths as needed.
		yes_image = pygame.image.load(f'{GRAPHICS_PATH}/ui/confirm_popup/button_white_up.png').convert_alpha()
		no_image = pygame.image.load(f'{GRAPHICS_PATH}/ui/confirm_popup/button_Orange_up.png').convert_alpha()
		self.yes_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, yes_image, 2.3, self.confirm)
		self.no_button = Button(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50, no_image, 2.3, self.cancel)
		self.running = True

	def confirm(self):
		self.on_confirm()
		self.running = False

	def cancel(self):
		self.on_cancel()
		self.running = False

	def handle_event(self, event):
		mouse_pos = pygame.mouse.get_pos()
		self.yes_button.update(mouse_pos)
		self.no_button.update(mouse_pos)
		# Let the buttons process events as needed
		# (If using edge detection in update, they are already handling mouse press.)
	
	def draw(self):
		mouse_pos = pygame.mouse.get_pos()
		# Draw translucent overlay
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 128))
		self.display_surface.blit(overlay, (0, 0))
		# Draw the confirmation message centered on screen
		self.display_surface.blit(self.message_surf, self.message_rect)
		# Draw the Yes and No buttons
		self.yes_button.draw(self.display_surface)
		self.no_button.draw(self.display_surface)
		self.display_surface.blit(self.cursor_img, mouse_pos)

class CharacterSelectUI:
	def __init__(self, display_surface, on_select_callback, on_cancel_callback):
		self.display_surface = display_surface
		self.on_select_callback = on_select_callback  # Gọi khi nhân vật được chọn
		self.on_cancel_callback = on_cancel_callback  # Gọi khi hủy/quay lại
		
		# Fonts
		self.title_font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 48)
		self.header_font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 32)
		self.font = pygame.font.Font(f'{FONT_PATH}/Lycheesoda.ttf', 24)
		
		# Load danh sách nhân vật đã lưu
		self.characters = PlayerDatabase.get_all_players()
		self.selected_index = 0 if self.characters else -1
		
		# Trạng thái UI
		self.active = True
		self.create_new_mode = False  # Chế độ tạo nhân vật mới
		self.name_input = ""  # Nhập tên nhân vật mới
		self.input_active = False
		
		# Thành phần UI
		self.bg_color = (20, 20, 30, 240)
		
		# Load hình ảnh nút
		self.new_btn_img = pygame.image.load(f'{medium_button_path}/new_button.png').convert_alpha()
		self.select_btn_img = pygame.image.load(f'{medium_button_path}/select_button.png').convert_alpha() 
		self.back_btn_img = pygame.image.load(f'{medium_button_path}/back_button.png').convert_alpha()
		self.delete_btn_img = pygame.image.load(f'{small_button_path}/delete_button.png').convert_alpha()
		self.delete_btn_img = pygame.transform.scale(self.delete_btn_img, (30, 30))
		
		# Tạo nút
		btn_scale = 2
		btn_y = SCREEN_HEIGHT - 100
		
		self.new_button = Button(SCREEN_WIDTH//4, btn_y, self.new_btn_img, btn_scale, self.toggle_creation_mode)
		self.select_button = Button(SCREEN_WIDTH//2, btn_y, self.select_btn_img, btn_scale, self.select_character)
		self.back_button = Button(3*SCREEN_WIDTH//4, btn_y, self.back_btn_img, btn_scale, self.on_cancel_callback)
		
		# Kích thước thẻ nhân vật
		self.card_width = 600
		self.card_height = 100
		self.card_padding = 20
		self.scroll_offset = 0
		self.visible_cards = 4

		self.showing_delete_confirm = False
		self.delete_confirm_index = -1

		# Thêm biến cho xem trước nhân vật
		self.preview_character = None
		self.avatar = []
		
		# Kích thước khung xem trước
		self.preview_size = (120, 120)
		
	def toggle_creation_mode(self):
		"""Chuyển đổi giữa chế độ chọn và tạo nhân vật"""
		self.create_new_mode = not self.create_new_mode
		self.name_input = ""
		self.input_active = self.create_new_mode
	
	def select_character(self):
		"""Chọn nhân vật hiện tại và quay lại game chính"""
		if self.create_new_mode and self.name_input.strip():
			# Tạo nhân vật mới với tên đã nhập
			player_id = PlayerDatabase.create_player(self.name_input.strip())
			self.on_select_callback(player_id)
		elif self.selected_index >= 0 and self.selected_index < len(self.characters):
			# Chọn nhân vật có sẵn
			player_id = self.characters[self.selected_index]['player_id']
			self.on_select_callback(player_id)
		
	def delete_character(self, index):
		"""Hiển thị hộp xác nhận trước khi xóa nhân vật"""
		if 0 <= index < len(self.characters):
			self.showing_delete_confirm = True
			self.delete_confirm_index = index
	
	def confirm_delete(self):
		"""Xóa nhân vật sau khi xác nhận"""
		if self.delete_confirm_index >= 0 and self.delete_confirm_index < len(self.characters):
			player_id = self.characters[self.delete_confirm_index]['player_id']
			PlayerDatabase.delete_player(player_id)
			# Tải lại danh sách nhân vật sau khi xóa
			self.characters = PlayerDatabase.get_all_players()
			# Điều chỉnh chỉ số được chọn nếu cần
			if self.selected_index >= len(self.characters):
				self.selected_index = max(0, len(self.characters) - 1)
			self.showing_delete_confirm = False
			self.delete_confirm_index = -1
	
	def cancel_delete(self):
		"""Hủy bỏ việc xóa nhân vật"""
		self.showing_delete_confirm = False
		self.delete_confirm_index = -1

	def load_character_preview(self, character_id):
		"""Tải hình ảnh xem trước cho nhân vật"""
		# Giả định rằng bạn có đường dẫn đến sprite sheet cho nhân vật
		# Đây chỉ là một ví dụ, cần điều chỉnh cho phù hợp với cấu trúc dự án của bạn
		try:
			# Cố gắng tải hình ảnh xem trước
			character_data = PlayerDatabase.get_player_info(character_id)
			if character_data:
				# Giả sử có một đường dẫn avatar hoặc sprite sheet trong dữ liệu nhân vật
				# Hoặc sử dụng một sprite sheet mặc định
				character_sprites = pygame.image.load(f"{GRAPHICS_PATH}/character/bonnie.png").convert_alpha()
				if character_sprites:
					self.avatar = character_sprites
					self.preview_character = character_id
					return True
		except Exception as e:
			print(f"Lỗi khi tải preview nhân vật: {e}")
		
		# Nếu không thể tải, sử dụng một hình ảnh giữ chỗ
		fallback_image = pygame.Surface(self.preview_size)
		fallback_image.fill((100, 100, 150))
		self.avatar = [fallback_image]
		return False
		


	def handle_event(self, event):
		"""Xử lý sự kiện đầu vào"""
		if not self.active:
			return False
			
		# Xử lý xác nhận xóa
		if self.showing_delete_confirm and event.type == pygame.MOUSEBUTTONDOWN:
			mouse_pos = pygame.mouse.get_pos()
			

			
			# Vị trí nút xác nhận và hủy
			confirm_width, confirm_height = 400, 200
			confirm_rect = pygame.Rect(
				SCREEN_WIDTH//2 - confirm_width//2,
				SCREEN_HEIGHT//2 - confirm_height//2,
				confirm_width,
				confirm_height
			)
			
			yes_button_rect = pygame.Rect(confirm_rect.left + 80, confirm_rect.bottom - 60, 100, 40)
			no_button_rect = pygame.Rect(confirm_rect.right - 180, confirm_rect.bottom - 60, 100, 40)
			
			if yes_button_rect.collidepoint(mouse_pos):
				self.confirm_delete()
				return True
			elif no_button_rect.collidepoint(mouse_pos):
				self.cancel_delete()
				return True
			
			# Nếu người dùng nhấp bên ngoài hộp xác nhận, hủy thao tác
			if not confirm_rect.collidepoint(mouse_pos):
				self.cancel_delete()
				return True
				
			return True
			
		# Các xử lý sự kiện khác chỉ khi không hiển thị hộp xác nhận
		if not self.showing_delete_confirm:
			# Xử lý phím tắt và điều hướng bàn phím
			if event.type == pygame.KEYDOWN:
				# Trong chế độ tạo mới
				if self.create_new_mode and self.input_active:
					if event.key == pygame.K_BACKSPACE:
						self.name_input = self.name_input[:-1]
					elif event.key == pygame.K_RETURN:
						self.select_character()
					elif event.key == pygame.K_ESCAPE:
						self.toggle_creation_mode()  # Quay lại chế độ chọn
					elif len(self.name_input) < 20:  # Giới hạn độ dài tên
						self.name_input += event.unicode
				# Trong chế độ chọn
				elif not self.create_new_mode:
					if event.key == pygame.K_UP:
						# Di chuyển lên trong danh sách
						if self.selected_index > 0:
							self.selected_index -= 1
							# Điều chỉnh cuộn nếu cần
							if self.selected_index < self.scroll_offset:
								self.scroll_offset = self.selected_index
					elif event.key == pygame.K_DOWN:
						# Di chuyển xuống trong danh sách
						if self.selected_index < len(self.characters) - 1:
							self.selected_index += 1
							# Điều chỉnh cuộn nếu cần
							if self.selected_index >= self.scroll_offset + self.visible_cards:
								self.scroll_offset = self.selected_index - self.visible_cards + 1
					elif event.key == pygame.K_RETURN:
						# Chọn nhân vật hiện tại
						self.select_character()
					elif event.key == pygame.K_n:
						# Tạo nhân vật mới
						self.toggle_creation_mode()
					elif event.key == pygame.K_DELETE and self.selected_index >= 0:
						# Xóa nhân vật hiện tại
						self.delete_character(self.selected_index)
					elif event.key == pygame.K_ESCAPE:
						# Quay lại menu trước
						self.on_cancel_callback()
						
			# Xử lý nhấp chuột
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = event.pos
				
				# Kiểm tra chọn thẻ nhân vật
				if not self.create_new_mode:
					for i in range(min(len(self.characters), self.visible_cards)):
						idx = i + self.scroll_offset
						if idx >= len(self.characters):
							break
							
						card_rect = self.get_card_rect(i)
						# Tạo delete_rect cho mỗi card
						delete_rect = pygame.Rect(
							card_rect.right - 30, 
							card_rect.top + 10, 
							40, 40
						)
						
						# Kiểm tra click vào nút xóa trước
						if delete_rect.collidepoint(mouse_pos):
							self.delete_character(idx)
							return True
						# Nếu không phải nút xóa, kiểm tra click vào card
						elif card_rect.collidepoint(mouse_pos):
							self.selected_index = idx
							return True
				
				# Kiểm tra nhấp vào vùng nhập văn bản trong chế độ tạo
				if self.create_new_mode:
					input_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 40)
					self.input_active = input_rect.collidepoint(mouse_pos)
			
			# Xử lý cuộn danh sách nhân vật
			elif event.type == pygame.MOUSEWHEEL and not self.create_new_mode:
				max_offset = max(0, len(self.characters) - self.visible_cards)
				self.scroll_offset = max(0, min(self.scroll_offset - event.y, max_offset))
				
			return False
		
	def get_card_rect(self, index):
		"""Lấy hình chữ nhật cho thẻ nhân vật tại chỉ số đã cho"""
		y = 150 + index * (self.card_height + self.card_padding)
		return pygame.Rect(
			SCREEN_WIDTH//2 - self.card_width//2,
			y,
			self.card_width,
			self.card_height
		)
		
	def update(self, dt):
		"""Cập nhật trạng thái UI"""
		mouse_pos = pygame.mouse.get_pos()
		
		# Cập nhật các nút
		self.new_button.update(mouse_pos)
		self.select_button.update(mouse_pos)
		self.back_button.update(mouse_pos)
		
		# Cập nhật hoạt ảnh xem trước nhân vật
		if self.selected_index >= 0 and self.selected_index < len(self.characters):
			char_id = self.characters[self.selected_index]['player_id']
			if self.preview_character != char_id:
				self.load_character_preview(char_id)
		
	def draw(self):
		"""Vẽ giao diện chọn nhân vật"""
		if not self.active:
			return
			
		# Vẽ nền bán trong suốt
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill(self.bg_color)
		self.display_surface.blit(overlay, (0, 0))
		
		# Vẽ tiêu đề
		title = self.title_font.render("World Selection", True, (240, 230, 140))
		title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 70))
		self.display_surface.blit(title, title_rect)
		
		if self.create_new_mode:
			self.draw_creation_ui()
		else:
			self.draw_selection_ui()
			
		# Vẽ các nút
		self.new_button.draw(self.display_surface)
		self.select_button.draw(self.display_surface)
		self.back_button.draw(self.display_surface)
		
		# Vẽ hộp xác nhận xóa nếu đang hiển thị
		if self.showing_delete_confirm:
			self.draw_delete_confirmation()
			
	def draw_selection_ui(self):
		"""Vẽ giao diện chọn nhân vật"""
		# Vẽ hướng dẫn
		if not self.characters:
			no_chars = self.font.render("Can't find your world, create one!", True, (200, 200, 200))
			no_chars_rect = no_chars.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
			self.display_surface.blit(no_chars, no_chars_rect)
			return
		
		# Vẽ xem trước nhân vật được chọn
		if (self.selected_index >= 0 and self.selected_index < len(self.characters) and 
			self.avatar and not self.showing_delete_confirm):
			preview_image = self.avatar
			# Đặt khung xem trước ở bên phải danh sách nhân vật
			self.preview_rect = pygame.Rect(
				SCREEN_WIDTH//2 + self.card_width//2 + 100,
				SCREEN_HEIGHT//2 - 150,
				150,
				150
			)
			
			# Vẽ nền cho khung xem trước
			pygame.draw.rect(self.display_surface, (60, 60, 80), self.preview_rect, 0, 10)
			pygame.draw.rect(self.display_surface, (140, 140, 160), self.preview_rect, 2, 10)
			
			# Vẽ hình ảnh xem trước được căn giữa
			scaled_preview = pygame.transform.scale(preview_image, (120, 120))
			# preview_img_rect = scaled_preview.get_rect(center=preview_rect.center)
			# self.display_surface.blit(scaled_preview, preview_img_rect)
			
			# Vẽ tiêu đề xem trước
			preview_title = self.font.render("Preview", True, (220, 220, 220))
			preview_title_rect = preview_title.get_rect(midbottom=(self.preview_rect.centerx, self.preview_rect.top - 10))
			self.display_surface.blit(preview_title, preview_title_rect)
			
			# Vẽ thêm thông tin nhân vật 
			if self.selected_index < len(self.characters):
				char = self.characters[self.selected_index]
				char_details = [
					f"ID: {char['player_id'][:8]}...",
					f"Last played: {char.get('last_played', 'Chưa chơi')}",
				]
				
				detail_y = self.preview_rect.bottom + 20
				for detail in char_details:
					detail_surf = self.font.render(detail, True, (200, 200, 200))
					detail_rect = detail_surf.get_rect(midtop=(self.preview_rect.centerx, detail_y))
					self.display_surface.blit(detail_surf, detail_rect)
					detail_y += 30
			
		# Vẽ các thẻ nhân vật và phần còn lại như đã có
		for i in range(min(len(self.characters), self.visible_cards)):
			idx = i + self.scroll_offset
			if idx >= len(self.characters):
				break
				
			char = self.characters[idx]
			card_rect = self.get_card_rect(i)
			
			# Vẽ nền thẻ
			card_color = (60, 60, 80) if idx == self.selected_index else (40, 40, 60)
			pygame.draw.rect(self.display_surface, card_color, card_rect, 0, 10)
			pygame.draw.rect(self.display_surface, (140, 140, 160), card_rect, 2, 10)
			
			# Vẽ tên nhân vật
			name_text = self.font.render(char['player_name'], True, (255, 255, 255))
			self.display_surface.blit(name_text, (card_rect.x + 20, card_rect.y + 15))
			
			# Vẽ thông tin nhân vật
			last_played = char.get('last_played', 'Not played yet')
			info_text = self.font.render(f"Last played: {last_played}", True, (200, 200, 200))
			self.display_surface.blit(info_text, (card_rect.x + 20, card_rect.y + 55))
			
			# Vẽ nút xóa
			self.delete_rect = self.delete_btn_img.get_rect(topright=(card_rect.right - 10, card_rect.top + 10))
			self.display_surface.blit(self.delete_btn_img, self.delete_rect)
			
			# Vẽ xem trước nhân vật nếu được chọn
			if idx == self.selected_index and self.avatar:
				self.preview_rect = pygame.Rect(self.preview_rect.left + 15, self.preview_rect.top + 15, *self.preview_size)
				preview_avatar = self.avatar
				scaled_preview = pygame.transform.scale(preview_avatar, self.preview_size)
				self.display_surface.blit(scaled_preview, self.preview_rect)
		
		# Vẽ chỉ báo cuộn nếu cần
		if self.scroll_offset > 0:
			pygame.draw.polygon(self.display_surface, (200, 200, 200), 
							  [(SCREEN_WIDTH//2, 120), 
							   (SCREEN_WIDTH//2 - 10, 130), 
							   (SCREEN_WIDTH//2 + 10, 130)])
		
		if self.scroll_offset < len(self.characters) - self.visible_cards:
			bottom_y = 150 + self.visible_cards * (self.card_height + self.card_padding) + 10
			pygame.draw.polygon(self.display_surface, (200, 200, 200), 
							  [(SCREEN_WIDTH//2, bottom_y), 
							   (SCREEN_WIDTH//2 - 10, bottom_y - 10), 
							   (SCREEN_WIDTH//2 + 10, bottom_y - 10)])
			
	def draw_creation_ui(self):
		"""Vẽ giao diện tạo nhân vật"""
		# Vẽ hướng dẫn
		instruction = self.header_font.render("Enter world name:", True, (220, 220, 220))
		instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
		self.display_surface.blit(instruction, instruction_rect)
		
		# Vẽ hộp nhập liệu
		input_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 40)
		input_color = (80, 80, 100) if self.input_active else (60, 60, 80)
		pygame.draw.rect(self.display_surface, input_color, input_rect, 0, 5)
		pygame.draw.rect(self.display_surface, (160, 160, 180), input_rect, 2, 5)
		
		# Vẽ văn bản nhập vào
		input_text = self.font.render(self.name_input, True, (255, 255, 255))
		input_text_rect = input_text.get_rect(midleft=(input_rect.left + 10, input_rect.centery))
		self.display_surface.blit(input_text, input_text_rect)
		
		# Vẽ con trỏ nhấp nháy nếu đang nhập
		if self.input_active and time.time() % 1 > 0.5:
			cursor_x = input_text_rect.right + 2
			if cursor_x - input_rect.left > 280:  # Ngăn con trỏ ra khỏi hộp nhập liệu
				cursor_x = input_rect.left + 280
			pygame.draw.line(self.display_surface, (255, 255, 255), 
						   (cursor_x, input_rect.top + 10), 
						   (cursor_x, input_rect.bottom - 10), 2)
	
	def draw_delete_confirmation(self):
		"""Vẽ hộp xác nhận xóa nhân vật"""
		if not self.showing_delete_confirm:
			return
			
		# Lấy tên nhân vật cần xóa
		char_name = self.characters[self.delete_confirm_index]['player_name']
		
		# Vẽ nền mờ che phủ
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 180))
		self.display_surface.blit(overlay, (0, 0))
		
		# Vẽ hộp xác nhận
		confirm_width, confirm_height = 400, 200
		confirm_rect = pygame.Rect(
			SCREEN_WIDTH//2 - confirm_width//2,
			SCREEN_HEIGHT//2 - confirm_height//2,
			confirm_width,
			confirm_height
		)
		pygame.draw.rect(self.display_surface, (50, 50, 70), confirm_rect, 0, 15)
		pygame.draw.rect(self.display_surface, (120, 120, 140), confirm_rect, 3, 15)
		
		# Vẽ tiêu đề và nội dung
		title = self.header_font.render("Delete Confirmation", True, (220, 220, 100))
		title_rect = title.get_rect(center=(SCREEN_WIDTH//2, confirm_rect.top + 40))
		self.display_surface.blit(title, title_rect)
		
		message = self.font.render(f"Do you want to delete '{char_name}'?", True, (220, 220, 220))
		message_rect = message.get_rect(center=(SCREEN_WIDTH//2, confirm_rect.top + 90))
		self.display_surface.blit(message, message_rect)
		
		# Vẽ nút xác nhận và hủy
		yes_button_rect = pygame.Rect(confirm_rect.left + 80, confirm_rect.bottom - 60, 100, 40)
		no_button_rect = pygame.Rect(confirm_rect.right - 180, confirm_rect.bottom - 60, 100, 40)
		
		# Kiểm tra chuột có trỏ vào nút không
		mouse_pos = pygame.mouse.get_pos()
		yes_hover = yes_button_rect.collidepoint(mouse_pos)
		no_hover = no_button_rect.collidepoint(mouse_pos)
		
		# Vẽ nút với màu sắc phù hợp
		yes_color = (200, 60, 60) if yes_hover else (160, 60, 60)
		no_color = (80, 100, 120) if no_hover else (60, 80, 100)
		
		pygame.draw.rect(self.display_surface, yes_color, yes_button_rect, 0, 5)
		pygame.draw.rect(self.display_surface, no_color, no_button_rect, 0, 5)
		
		# Vẽ chữ trên nút
		yes_text = self.font.render("Delete", True, (255, 255, 255))
		no_text = self.font.render("Cancle", True, (255, 255, 255))
		
		yes_text_rect = yes_text.get_rect(center=yes_button_rect.center)
		no_text_rect = no_text.get_rect(center=no_button_rect.center)
		
		self.display_surface.blit(yes_text, yes_text_rect)
		self.display_surface.blit(no_text, no_text_rect)

