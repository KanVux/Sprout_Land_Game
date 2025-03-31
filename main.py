import pygame, sys
from scripts.helpers.timer import Timer
from settings import *
from scripts.level import Level
from scripts.ui.menu import MainMenu, PauseMenu, ShopMenu, CharacterSelectUI
from scripts.db.settings_db import SettingsDB
from scripts.ui.overlay import FPSOverlay
from scripts.models.mission import MissionManager
from scripts.ui.mission_ui import MissionUI

class Game:
	def __init__(self):
		pygame.init()
		
		
		self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
		pygame.display.set_caption('Sprout Land')
		
		set_global_volume(global_volume)
		# pygame.mouse.set_visible(False)
		self.default_cursor_img = pygame.image.load(f"{GRAPHICS_PATH}/mouse/Triangle Mouse icon 1.png").convert_alpha()	
		self.point_cursor_img = pygame.image.load(f"{GRAPHICS_PATH}/mouse/Catpaw pointing Mouse icon.png").convert_alpha()
		self.hold_cursor_img = pygame.image.load(f"{GRAPHICS_PATH}/mouse/Catpaw holding Mouse icon.png").convert_alpha()
	
		self.clock = pygame.time.Clock()

		self.player_id = None  # Lưu ID người chơi hiện tại
		self.main_menu_screen = MainMenu(self.screen)
		self.pause_menu_screen = PauseMenu(self.screen)
		self.character_select_ui = None  # Sẽ được khởi tạo khi cần thiết
		player_id = 1
		self.level = Level(str(player_id))
		self.shop_menu = ShopMenu(self.level.player, self.level.toggle_shop)

		self.timer = Timer(300)
		self.running = True
		self.paused = False
		self.game_state = "menu"  # "menu", "character_select", "game", "paused", "shop"
		pygame.event.set_grab(True)  # Keep mouse in window
		pygame.mouse.set_visible(False)  # Hide system cursor
		self.last_mouse_pos = pygame.mouse.get_pos()
		self.last_update = pygame.time.get_ticks()
		self.frame_time = 1000 // FPS  # Target frame time in ms

		# Tạo mission_manager và mission_ui sau khi level đã được khởi tạo
		# để có thể truy cập vào player
		self.mission_manager = MissionManager(player_id=self.level.player.player_id, player=self.level.player)
		self.mission_manager.load_player_missions()
		self.level.player.mission_manager = self.mission_manager
		
		# Tạo mission_ui
		self.mission_ui = MissionUI(self.mission_manager)
		
	def __del__(self):
		"""Destructor để dọn dẹp tài nguyên khi thoát game"""
		if hasattr(self, 'level') and self.level:
			self.level.cleanup()
		
	def run(self):
		fps_overlay = FPSOverlay()

		while self.running:
			dt = self.clock.tick(FPS) / 1000.0  # Tính dt từ clock.tick, FPS là số khung hình mục tiêu

			# Handle cursor position
			mouse_pos = pygame.mouse.get_pos()
			if self.level.player.inventory_ui.dragging:
				self.cursor_img = self.hold_cursor_img
			elif self.level.player.inventory_ui.hovering:
				self.cursor_img = self.point_cursor_img
			else:
				self.cursor_img = self.default_cursor_img
			self.cursor_rect = self.cursor_img.get_rect()
			self.cursor_rect.center = mouse_pos
			
			# Clear screen
			self.screen.fill('black')

			# Handle events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					continue

				# Xử lý sự kiện cho màn hình chọn nhân vật
				if self.game_state == "character_select" and self.character_select_ui:
					self.character_select_ui.handle_event(event)
					continue  # Bỏ qua các xử lý khác khi đang ở màn hình chọn nhân vật

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.handle_escape()
					elif self.game_state == "game":
						self.handle_game_input(event)

				# Xử lý các sự kiện chuột cho mission_ui
				if event.type == pygame.MOUSEBUTTONDOWN:
					if self.mission_ui.handle_click(event.pos):
						continue  # Sự kiện đã được xử lý bởi mission UI
				if event.type ==  pygame.MOUSEWHEEL:
					if self.game_state == "game":
						self.handle_hotbar_scroll(event)

			# Update game state
			self.update_game_state(dt, mouse_pos, pygame.mouse.get_pressed()[0])

			# Draw cursor and overlay FPS

			self.screen.blit(self.cursor_img, self.cursor_rect)
			if self.level.all_sprites.debug_mode:
				fps_overlay.draw(self.screen, self.clock)
			pygame.display.flip()

		
	def initialize_character_select(self):
		"""Khởi tạo giao diện chọn nhân vật"""
		
		def on_character_selected(player_id):
			"""Được gọi khi người chơi chọn hoặc tạo nhân vật"""
			self.player_id = player_id
			self.game_state = "game"
			
			 # Dọn dẹp Level cũ nếu đã có
			if hasattr(self, 'level') and self.level:
				self.level.cleanup()
			
			# Khởi tạo Level mới với player_id đã chọn
			self.level = Level(str(player_id))
			
			# Load dữ liệu game sau khi đã khởi tạo Level
			self.level.load_game()
			
			# Khởi tạo lại các component phụ thuộc vào Level
			self.shop_menu = ShopMenu(self.level.player, self.level.toggle_shop)
			self.mission_manager = MissionManager(player_id=player_id, player=self.level.player)
			self.mission_manager.load_player_missions()
			self.level.player.mission_manager = self.mission_manager
			self.mission_ui = MissionUI(self.mission_manager)
		
		def on_character_selection_cancelled():
			"""Được gọi khi người chơi hủy chọn nhân vật"""
			self.game_state = "menu"
			self.main_menu_screen.running = True
		# Khởi tạo UI chọn nhân vật
		self.character_select_ui = CharacterSelectUI(
			self.screen,
			on_select_callback=on_character_selected,
			on_cancel_callback=on_character_selection_cancelled
		)

	def handle_escape(self):
		"""Handle escape key press"""
		if self.game_state == "character_select":
			self.game_state = "menu"
			self.level.cleanup()
			self.main_menu_screen.running = True
		elif self.game_state == "game":
			self.game_state = "paused"
			self.reset_pause_menu()
		elif self.game_state == "shop":
			self.game_state = "game"
			self.level.shop_active = False

	def handle_game_input(self, event):
		"""Handle game state input"""
		if self.level.player.inventory_ui.active:
			self.level.player.inventory_ui.handle_click(event)
			return

		if event.type == pygame.KEYDOWN and not self.level.player.inventory_ui.active:
			self.handle_number_keys(event)


	def handle_hotbar_scroll(self, event):
		"""Handle hotbar scrolling"""
		player = self.level.player
		
		if not player.timers['tool switch'].active:
			# Update the hotbar index with scroll
			current_index = player.tool_index
			player.tool_index = (current_index - event.y) % len(player.tools)  # Note: invert the y value
			player.timers['tool switch'].activate()
			
			# Set the selected item
			if player.tools and player.tool_index < len(player.tools):
				player.selected_tool = player.tools[player.tool_index]

	def handle_number_keys(self, event):
		"""Handle number key input"""
		if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
			index = event.key - pygame.K_1
			self.level.player.hotbar_index = index

	def update_game_state(self, dt, mouse_pos, mouse_pressed):
		"""Update current game state"""
		if self.game_state == "menu":
			self.main_menu_screen.run(dt)
			if not self.main_menu_screen.running:
				if hasattr(self.main_menu_screen, 'show_character_select') and self.main_menu_screen.show_character_select:
					# Chuyển đến màn hình chọn nhân vật
					self.game_state = "character_select"
					self.initialize_character_select()
					self.main_menu_screen.show_character_select = False
				else:
					# Trường hợp khác (nếu có)
					self.game_state = "game"
					self.reset_pause_menu()
		
		elif self.game_state == "character_select":
			# Xử lý sự kiện và vẽ UI chọn nhân vật
			self.character_select_ui.update(dt)
			self.character_select_ui.draw()
		
		elif self.game_state == "paused":
			self.level.run(dt)
			result = self.pause_menu_screen.run(dt)
			if result == "home":
				self.game_state = "menu"
				if self.level.save_game():
					print('Game saved!')
				self.main_menu_screen.running = True
			elif not self.pause_menu_screen.active:
				self.game_state = "game"
		
		elif self.game_state == "shop":
			self.level.run(dt)
			self.shop_menu.update(dt)
				
		elif self.game_state == "game":
			# Update inventory
			if self.level.player.inventory_ui.active:
				self.level.player.inventory_ui.update(mouse_pos, mouse_pressed)
			self.level.run(dt)
			if self.level.shop_active:
				self.game_state = "shop"

			# Cập nhật và vẽ mission UI
			self.mission_manager.check_periodic_missions()
			self.mission_ui.update(dt)
			self.mission_ui.draw(self.screen)

		# Draw cursor last, after all other rendering
		self.screen.blit(self.cursor_img, self.cursor_rect)
		
		# Single update per frame
		pygame.display.flip()  # Use flip() instead of update()

	def reset_pause_menu(self):
		"""Reset pause menu state when returning from main menu"""
		self.pause_menu_screen.active = False
		self.pause_menu_screen.resume_clicked = False
		self.pause_menu_screen.to_home_active = False
				
if __name__ == '__main__':
	game = Game()
	game.run()
