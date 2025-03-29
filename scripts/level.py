import pygame
from settings import *
from random import randint, random
from pytmx.util_pygame import load_pygame

from scripts.db.item_db import ItemDatabase
from scripts.db.player_db import PlayerDatabase

from scripts.ui.menu import ShopMenu
from scripts.ui.overlay import Overlay, Dialog, Clock
from scripts.ui.mission_ui import MissionUI

from scripts.helpers.support import *
from scripts.helpers.transition import Transition
from scripts.helpers.timer import Timer

from scripts.models.sky import Rain, Sky
from scripts.models.player import Player
from scripts.models.soil import SoildLayer
from scripts.models.mission import MissionManager 
from scripts.models.sprites import Generic, Interaction, Particle, Tree, Water, WildFlower


class Level:
	def __init__(self, player_id=None):
		# Get the display surface
		self.display_surface = pygame.display.get_surface()

		 # Dừng nhạc nền hiện tại nếu có
		pygame.mixer.stop()

		# Sprite groups
		self.all_sprites = CameraGroup()
		self.tree_sprites = pygame.sprite.Group()  # Only for trees
		self.obstacle_sprites = pygame.sprite.Group()  # For non-tree obstacles
		self.interaction_sprites = pygame.sprite.Group()

		self.soil_layer = SoildLayer(self.all_sprites, self.obstacle_sprites)
		self.player_id = player_id
		self.setup()
		# Sky
		self.rain = Rain(self.all_sprites)
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		self.sky = Sky()

		self.overlay = Overlay(self.player)
		self.transition = Transition(self.sleep, self.player)


		# Shop
		self.menu = ShopMenu(self.player, self.toggle_shop)
		self.shop_active = False


		# Sound
		background_music.play(loops = -1)

		# Spawn counter
		self.tree_spawn_counter = 0

		# Dialog
		self.dialog_index = randint(0,2)
		self.bonnie_the_trader_dialog = Dialog("bonnie", DIALOG['bonnie'].get('gretting')[self.dialog_index], self.display_surface, f'{GRAPHICS_PATH}/ui/dialog/avatar/bonnie.png')

		# Add time tracking
		self.time_elapsed = 0

		# Add clock
		self.clock = Clock(self.sky)

		# Sleep settings
		self.sky.reset_to_time(6) 
		self.day_sleep_duration = SLEEP_PROP['duration']['day']
		self.night_sleep_duration = SLEEP_PROP['duration']['night']  
		self.evening_threshold = SLEEP_PROP['threshold']['night']
		self.day_threshold = SLEEP_PROP['threshold']['day'] 

		# Rain settings
		self.rain_chance = RAIN_PROP['chance'] 
		self.min_rain_duration = RAIN_PROP['duration']['min']
		self.max_rain_duration = RAIN_PROP['duration']['max']
		self.rain_timer = 0
		self.rain_duration = 0
		self.rain_elapsed = 0  # biến tích lũy thời gian mưa (giây)
		self.rain_duration = 0  # thời gian mưa hiện tại (giây)



	def toggle_debug(self):
		self.all_sprites.toggle_debug()
		
	def setup(self):
		tmx_data = load_pygame(f'{MAPS_PATH}/map.tmx')

		# Background
		Generic(
			pos = (0,0),
			surf = pygame.image.load(f'{GRAPHICS_PATH}/world/ground.png').convert_alpha(),
			groups = self.all_sprites,
			z = LAYERS['ground'],
			)
		
		for layer in ['HouseFloor','HouseFurnitureBottom']:
			for x, y, surface in tmx_data.get_layer_by_name(layer).tiles():
				Generic(
					pos=(x * TILE_SIZE, y * TILE_SIZE),
					surf=surface,
					groups=[self.all_sprites],
					z=LAYERS['house bottom']
				)	

		# House and Furniture
		for layer in ['HouseWalls', 'HouseFurnitureTop']:
			for x, y, surface in tmx_data.get_layer_by_name(layer).tiles():
				Generic(
					pos=(x * TILE_SIZE, y * TILE_SIZE),
					surf=surface,
					groups=[self.all_sprites, self.obstacle_sprites],
					z= LAYERS['main']
				)


		# Fence
		for x, y, surface in tmx_data.get_layer_by_name('Fence').tiles():
			Generic(
				pos=(x * TILE_SIZE, y * TILE_SIZE),
				surf=surface,
				groups=[self.all_sprites, self.obstacle_sprites],
				z=LAYERS['main']
			)

		# Wildflowers
		for obj in tmx_data.get_layer_by_name('Decoration'):
			WildFlower(
				pos=(obj.x, obj.y),
				surf=obj.image,
				groups=[self.all_sprites, self.obstacle_sprites]
			)

		# Collision tiles
		for x, y, surface in tmx_data.get_layer_by_name('Collision').tiles():
			Generic(
				pos=(x * TILE_SIZE, y * TILE_SIZE),
				surf=pygame.Surface((TILE_SIZE, TILE_SIZE)),
				groups=[self.obstacle_sprites],
			)

		# Water
		water_frames = import_folder(f'{GRAPHICS_PATH}/water') 
		for x, y, surface in tmx_data.get_layer_by_name('Water').tiles():
			Water((x * TILE_SIZE, y * TILE_SIZE),
				water_frames, 
				self.all_sprites,
				)

		# Player
		for obj in tmx_data.get_layer_by_name('Player'):
			if obj.name == 'Start':
				self.player = Player(
					pos= (obj.x, obj.y),
					group= self.all_sprites,
					collision_sprites= self.obstacle_sprites,
					tree_sprites= self.tree_sprites,
					interaction_sprites= self.interaction_sprites,
					soil_layer= self.soil_layer,
					toggle_shop = self.toggle_shop,
					player_id=self.player_id
					)
				
			if obj.name == 'Bed':
				Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)
			if obj.name == 'Trader':
				Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)
			
		# Trees - only in tree_sprites
		for obj in tmx_data.get_layer_by_name('Trees'):
			if obj.type == "Tree":
				Tree(
					pos=(obj.x, obj.y),
					surf=obj.image,
					groups=[self.all_sprites, self.tree_sprites],  # Only tree_sprites, not collision_sprites
					name=obj.name,
					player_add=self.player_add,
					z=LAYERS['main']
				)

	def player_add(self, item_name, amount):
		item = ItemDatabase.get_item_from_name(item_name)
		self.player.add_item(item, amount)
		collect_item_sound.play()

		print(f"Collected {amount} of {item_name}")
		
		 # Cập nhật nhiệm vụ thu thập
		if hasattr(self.player, 'mission_manager') and self.player.mission_manager:
			self.player.mission_manager.update_missions_by_action('collect', item_name, amount)

	def toggle_shop(self):
		self.shop_active = not self.shop_active
		self.dialog_index = randint(0,2)
		self.bonnie_the_trader_dialog = Dialog('bonnie',DIALOG['bonnie'].get('gretting')[self.dialog_index],self.display_surface,f'{GRAPHICS_PATH}/ui/dialog/avatar/bonnie.png')
	
	def get_sleep_duration(self):
		"""Determine sleep duration based on time of day"""
		current_hour = self.sky.time_of_day
		# If it's evening/night (after 6 PM), sleep 6 hours
		if current_hour >= self.evening_threshold or current_hour <= self.day_threshold:
			return self.night_sleep_duration
		# During day, only sleep 2 hours
		else:
			return self.day_sleep_duration

	def sleep(self):
			"""Xử lý thời gian trôi qua khi người chơi ngủ"""
			# Lấy thời lượng ngủ (tính theo phút) từ hàm get_sleep_duration()
			sleep_minutes = self.get_sleep_duration()
			# Tính số giờ ngủ (ví dụ: 6 phút ngủ = 6/60 = 0.1 giờ)
			hours_passed = sleep_minutes / 60.0

			# Cập nhật thời gian trong Sky:
			new_time = self.sky.time_of_day + hours_passed
			additional_days = int(new_time // 24)
			self.sky.day_passed += additional_days
			self.sky.time_of_day = new_time % 24
			# Cập nhật màu sắc bầu trời theo thời gian mới
			self.sky.update_sky_color()
			
			# Tính thời gian ngủ đã trôi qua (ms) để cập nhật các hệ thống khác
			self.time_elapsed = sleep_minutes * 1000  # chuyển từ phút sang ms
			
			# Cập nhật cây trồng (plant) theo thời gian ngủ
			for plant in self.soil_layer.plant_sprites.sprites():
					# Giả lập quá trình trưởng thành theo từng giây của thời gian ngủ
					for _ in range(int(self.time_elapsed / 1000)):
							plant.grow()
			
			# Xóa nước trên đất sau khi ngủ
			self.soil_layer.remove_water()

			# Cập nhật cây (tree) theo thời gian ngủ:
			for tree in self.tree_sprites.sprites():
					if not tree.tree_alive:
							# Nếu cây đã chết, giảm thời gian respawn
							tree.respawn_timer = tree.respawn_time
							tree.respawn_timer -= self.time_elapsed
							if tree.respawn_timer <= 0:
									tree.regrow()
					else:
							# Nếu cây còn sống, cập nhật thời gian cho táo mọc
							tree.apple_timer -= self.time_elapsed
							if tree.apple_timer <= 0:
									tree.grow_apples(self.time_elapsed / 1000)
			
			# Cập nhật các timer của soil tiles
			if self.soil_layer.soil_timers:
					for pos, timer in list(self.soil_layer.soil_timers.items()):
							for _ in range(int(self.time_elapsed / 1000)):
									timer.update()
			
			# Có thể phát hiệu ứng chuyển màn (transition) nếu muốn
			self.transition.play()
			
			# Sau khi xử lý, đặt lại time_elapsed
			self.time_elapsed = 0

	def plant_collsion(self):
		if self.soil_layer.plant_sprites:
			for plant in self.soil_layer.plant_sprites.sprites():
				if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
					self.player_add(
						plant.plant_type,
						1
					)
					if hasattr(self.player, 'mission_manager') and self.player.mission_manager:
						self.player.mission_manager.update_missions_by_action('harvest', plant.plant_type.replace(' seeds', ''), 1)
					plant.kill()
					Particle(pos= plant.rect.topleft,
							surf= plant.image,
							groups= self.all_sprites,
							z= LAYERS['main'])
					
					self.soil_layer.grid[plant.rect.bottom // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

	def update_rain(self, dt):
			"""Cập nhật sự kiện mưa dựa trên dt (có thể tính cả khi ngủ)"""
			# Nếu đang mưa, tích lũy thời gian mưa
			if self.raining:
					self.rain_elapsed += dt
					if self.rain_elapsed >= self.rain_duration:
							self.raining = False
							self.soil_layer.raining = False
							self.soil_layer.remove_water()
							self.rain_elapsed = 0
			else:
					# Nếu không mưa, dựa vào dt xác suất để bắt đầu mưa
					# Có thể nhân thêm dt để xác suất được tỉ lệ với thời gian trôi qua
					if random() < self.rain_chance * dt:
							self.raining = True
							self.soil_layer.raining = True
							# Chọn thời gian mưa ngẫu nhiên (đơn vị giây)
							self.rain_duration = randint(self.min_rain_duration, self.max_rain_duration)
							self.rain_elapsed = 0
							self.soil_layer.water_all()

	def save_game(self):
		"""Save game data for the current player"""
		if not self.player_id:
			print("No player ID specified, cannot save game")
			return False
			
		try:
			player_data = {
				'position': self.player.pos,
				'game_time': self.sky.day_passed,
			}
			
			level_data = {
				'is_raining': self.raining,
				'soil_grid': self.soil_layer.grid,
				'planted_crops': [
					{
						'type': plant.plant_type,
						'position': (plant.rect.x, plant.rect.y),
						'age': plant.age,
						'watered': not plant.needs_water
					}
					for plant in self.soil_layer.plant_sprites.sprites()
				],
				'trees_state': [
					{
						'position': (tree.rect.topleft),  # Lưu topleft thay vì x,y
						'name': tree.name,
						'health': tree.health,
						'alive': tree.tree_alive,
						'apples': len(tree.apple_sprites.sprites()),
					}
					for tree in self.tree_sprites.sprites()
				],
				'water_grid': [
					(sprite.rect.x, sprite.rect.y)
					for sprite in self.soil_layer.water_sprites.sprites()
				],
				'time_of_day': self.sky.time_of_day
			}
			PlayerDatabase.save_game_state(self.player.player_id, player_data, level_data)
			return True
		except Exception as e:
			print(f"Error saving game: {e}")
			return False

	def load_game(self):
		"""Load game data for the current player"""

		if not self.player_id:
			print("No player ID specified, cannot load game")
			return False
		try:
			game_state = PlayerDatabase.load_game_state(self.player.player_id)
			if not game_state:
				return False

			self.player.pos = game_state['player']['position']
			self.time_elapsed = game_state['player']['game_time']
			
			self.rainning = game_state['level']['is_raining']
			self.sky.time_of_day = game_state['level']['time_of_day']

			# Lấy grid đã lưu
			self.soil_layer.grid = game_state['level']['soil_grid']
			
			# Đảm bảo rằng với mỗi ô có cây ('P') thì cũng có marker cày ('X')
			for row in enumerate(self.soil_layer.grid):
				for cell in enumerate(row):
					if 'P' in cell and 'X' not in cell:
						cell.append('X')

			# Tái tạo lại các sprite soil dựa trên grid
			self.recreate_soil_tiles()
			# Tái tạo các water tile nếu có marker 'W'
			self.soil_layer.recreate_water_tiles()

			self.planted_crops = game_state['level']['planted_crops']
			for plant in self.planted_crops:
				self.soil_layer.plant_seed_at(
					plant['position'],
					plant['type'],
					plant['age'],
					plant['watered']
				)

			# Tái tạo lại các sprite cây
			self.trees_state = game_state['level']['trees_state']
			self.recreate_tree(self.trees_state)

			self.sky.day_passed = game_state['player']['game_time']

			self.player.keys_bind = SettingsDB.get_settings()['keys_bind']
			return True
		except Exception as e:
			print(f"Error loading game: {e}")
			return False
	
	def recreate_tree(self, trees_states):
		"""Recreate all tree objects from saved game data without duplicate apples."""
		# Xóa toàn bộ tree sprite hiện có
		for tree in self.tree_sprites.sprites():
			tree.kill()
		for saved_tree in trees_states:
			pos = saved_tree['position']  # Đây giờ là topleft
			health = saved_tree['health']
			apple_count = saved_tree.get('apples', 0)
			alive = saved_tree.get('alive', True)
			tree_name = saved_tree.get('name', 'Oak')
			
			# Tạo tree bằng phương thức plant_tree_at
			tree = Tree.plant_tree_at(
				pos,
				apple_count,
				health,
				[self.all_sprites, self.tree_sprites],
				tree_name,
				self.player_add,
				)
			
			# Điều chỉnh lại vị trí chính xác sau khi tạo
			tree.rect.topleft = pos
			# Cập nhật hitbox để phù hợp với vị trí mới của cây
			if hasattr(tree, 'hitbox'):
				# Giữ nguyên offset giữa rect và hitbox
				hitbox_offset = pygame.math.Vector2(tree.hitbox.topleft) - pygame.math.Vector2(tree.rect.topleft)
				tree.hitbox.topleft = tree.rect.topleft + hitbox_offset
			
			# Cập nhật vị trí của táo nếu có
			tree.apple_sprites.update()
			
			# Nếu cây bị chết trong dữ liệu lưu, gọi die() để chuyển thành stump và xóa táo
			if not alive:
				tree.die()

	def recreate_plant(self, planted_crops):
		"""Recreate all plant objects from saved game data"""
		# Clear existing plant sprites and remove plant markers from the soil grid.
		for plant in self.soil_layer.plant_sprites.sprites():
			grid_x = plant.rect.centerx // TILE_SIZE
			grid_y = plant.rect.centery // TILE_SIZE
			if 'P' in self.soil_layer.grid[grid_y][grid_x]:
				self.soil_layer.grid[grid_y][grid_x].remove('P')
			plant.kill()
		
		# Loop through the saved planted crops and re-create them.
		for crop in planted_crops:
			plant_type = crop['type']
			pos = crop['position']  # Should be an (x, y) tuple (absolute coordinates)
			age = crop['age']
			watered = crop['watered']
			# Convert the saved position to tile origin coordinates.
			grid_x = pos[0] // TILE_SIZE
			grid_y = pos[1] // TILE_SIZE
			tile_origin = (grid_x * TILE_SIZE, grid_y * TILE_SIZE)
			
			# Create the plant using the soil_layer's planting method.
			self.soil_layer.plant_seed_at(tile_origin, plant_type, age, watered)

	def recreate_soil_tiles(self):
		for tile in self.soil_layer.soil_sprites.sprites():
			tile.kill()
		self.soil_layer.soil_sprites.empty()
			
			# Rebuild soil tiles based on the loaded grid
		self.soil_layer.create_soil_tiles()

		# Reinitialize soil timers for each tilled (X) tile if needed
		for row_index, row in enumerate(self.soil_layer.grid):
			for col_index, cell in enumerate(row):
				# If the cell is already tilled and has no active timer, set one up.
				if 'X' in cell and (col_index, row_index) not in self.soil_layer.soil_timers:
					self.soil_layer.soil_timers[(col_index, row_index)] = Timer(
						self.soil_layer.soil_duration,
						self.soil_layer.remove_soil_tile,
						col_index,
						row_index
					)
					self.soil_layer.soil_timers[(col_index, row_index)].activate()

	def cleanup(self):
		"""Dọn dẹp tài nguyên khi Level bị hủy"""
		# Dừng nhạc nền
		background_music.stop()
		
		# Xóa tất cả sprite để giải phóng bộ nhớ
		for sprite in self.all_sprites:
			sprite.kill()
		self.all_sprites.empty()
		self.tree_sprites.empty()
		self.obstacle_sprites.empty()
		self.interaction_sprites.empty()
		
		# Xóa các timer nếu có
		if hasattr(self.soil_layer, 'soil_timers'):
			self.soil_layer.soil_timers.clear()

	def run(self, dt):
		# Draw
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)

		# Update
		if not self.shop_active:
			self.all_sprites.update(dt)
			self.plant_collsion()
			self.soil_layer.update(dt)
			self.update_rain(dt)
			
		# Weather
		if self.raining and not self.shop_active:
			self.rain.update()
		self.sky.display(dt)
		self.overlay.display()
		self.clock.display()
		self.clock.day_counter.update(self.sky.day_passed)

		# Sleep
		if self.player.sleep:
			self.transition.play()

		# Dialog
		self.bonnie_the_trader_dialog.is_active = self.shop_active
		if self.bonnie_the_trader_dialog.is_active:
			self.bonnie_the_trader_dialog.update(dt)
			self.bonnie_the_trader_dialog.draw()
		

	
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.debug_mode = False

    def toggle_debug(self):
        """Toggle debug mode to show/hide hitboxes"""
        self.debug_mode = not self.debug_mode

    def custom_draw(self, player):
        # Calculate offset from player
        self.offset.x = player.rect.centerx - SCREEN_WIDTH // 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT // 2

        # Lấy danh sách sprite một lần, sau đó lọc các sprite trong vùng hiển thị
        sprites = self.sprites()
        visible_sprites = []
        for sprite in sprites:
            # Tính toán offset_rect cho từng sprite
            offset_rect = sprite.rect.copy()
            offset_rect.centerx -= self.offset.x
            offset_rect.centery -= self.offset.y

            # Kiểm tra xem sprite có nằm trong màn hình không
            if (offset_rect.right > 0 and offset_rect.left < SCREEN_WIDTH and
                offset_rect.bottom > 0 and offset_rect.top < SCREEN_HEIGHT):
                # Lưu dưới dạng tuple chứa: layer, sprite, và offset_rect đã tính toán
                # Giả sử sprite có thuộc tính 'z', nếu không có sẽ dùng giá trị mặc định
                layer = getattr(sprite, 'z', 0)
                visible_sprites.append((layer, sprite, offset_rect))

        # Sắp xếp các sprite theo layer (và sau đó theo vị trí y)
        visible_sprites.sort(key=lambda item: (item[0], item[2].centery))

        # Vẽ từng sprite
        for layer, sprite, offset_rect in visible_sprites:
            self.display_surface.blit(sprite.image, offset_rect)
            if self.debug_mode:
                pygame.draw.rect(self.display_surface, (255, 255, 255), offset_rect, 1)
                if hasattr(sprite, 'hitbox'):
                    hitbox_rect = sprite.hitbox.copy()
                    hitbox_rect.topleft = pygame.math.Vector2(hitbox_rect.topleft) - self.offset
                    # Chọn màu cho hitbox theo loại sprite
                    color = (255, 0, 0)  # Mặc định là đỏ
                    if isinstance(sprite, Player):
                        color = (0, 255, 0)
                    elif isinstance(sprite, Tree):
                        color = (255, 128, 0)
                    elif isinstance(sprite, Water):
                        color = (0, 0, 255)
                    elif isinstance(sprite, Generic):
                        color = (255, 255, 0)
                    elif isinstance(sprite, WildFlower):
                        color = (255, 0, 255)
                    pygame.draw.rect(self.display_surface, color, hitbox_rect, 2)
