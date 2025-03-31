from random import randint
import pygame
from scripts.models.mission import MissionManager
from scripts.db.item_db import ItemDatabase
import settings  # đảm bảo import module settings, thay vì “from settings import *”
from scripts import level
from scripts.models.sprites import Tree
from scripts.db.inventory_db import InventoryDatabase
from scripts.db.settings_db import SettingsDB
from scripts.helpers.support import *
from scripts.helpers.timer import Timer
from scripts.ui.inventory_ui import InventoryUI
from settings import *
class Player(pygame.sprite.Sprite):
	def __init__(self, pos, group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, toggle_shop, player_id):
		super().__init__(group)
		self.keys_bind = SettingsDB.get_settings()['keys_bind']
		
		self.mission_manager = MissionManager(player_id=1, player=self) 

		self.player_id = player_id

		self.import_assets()

		self.status = 'down_idle'
		self.frame_index = 0

		# General setup
		self.image = self.animations[self.status][self.frame_index]
		self.rect = self.image.get_rect(center = pos)
		self.z = LAYERS['main']
		
		# Movement attributes
		self.direction = pygame.math.Vector2()
		self.pos = pygame.math.Vector2(self.rect.center)
		self.speed = 200
		
		# Collision
		self.hitbox = self.rect.copy().inflate((-126, -80))
		self.collision_sprites = collision_sprites

		# Interaction
		self.tree_sprites = tree_sprites
		self.obstacle_sprites = collision_sprites
		self.interaction_sprites = interaction_sprites
		self.sleep = False
		self.soil_layer = soil_layer
		self.toggle_shop = toggle_shop

		# Timers
		self.timers = {
			'tool use' : Timer(500, self.use_tool),
			'tool switch' : Timer(200),
			'seed use': Timer(350, self.use_seed),
			'seed switch': Timer(200),
			'inventory open': Timer(200),
			'debug mode': Timer(200)
		}

		# Tools
		self.tools = ['axe', 'hoe', 'water']
		self.tool_index = 0
		self.selected_tool = self.tools[self.tool_index]

		# Inventory
		self.inventory = InventoryDatabase.get_player_inventory(player_id=self.player_id)

		if self.inventory.get_item('coins') is None:
			self.add_item(ItemDatabase.get_item_from_name('coins'), 0)

		self.hotbar = []
		for index, item in enumerate(self.inventory.items):
			if item is not None and index < 6 and item.item_name != 'coins':
				self.hotbar.append(item.item_name)

		if self.hotbar:
			self.hotbar_index = 0
			self.selected_item = self.hotbar[self.hotbar_index]
		else:
			self.hotbar_index = 0
			self.selected_item = None
		# Inventory UI
		self.inventory_ui = InventoryUI(self)
		
		# Add overlay after inventory UI
		from scripts.ui.overlay import Overlay
		self.overlay = Overlay(self)
		
		self.talking_to = None
		self.talking = False

	def save_inventory(self):
		"""Lưu inventory vào cơ sở dữ liệu"""
		items_info = [(item.item_name, item.quantity) for item in self.inventory.items if item is not None]
		print("📦 Inventory trước khi lưu:", items_info)
		return InventoryDatabase.save_inventory(self.player_id, self.inventory)
	
	def add_item(self, item_data, quantity=1):
		"""Thêm item vào inventory"""
		self.inventory.add_item(item_data, quantity)
		self.save_inventory()

	def remove_item(self, item_name, quantity=1):
		"""Sử dụng item trong inventory"""
		result = self.inventory.remove_item(item_name, quantity)
		if result:
			self.save_inventory()
		return result

	def has_item(self, item_name, quantity=1):
		"""Kiểm tra xem có đủ số lượng item không"""
		item = self.inventory.get_item(item_name)
		if item and item.quantity >= quantity:
			return True
		return False

	def get_item_quantity(self, item_name):
		"""Lấy số lượng của một item cụ thể"""
		item = self.inventory.get_item(item_name)
		return item.quantity if item else 0

	def use_tool(self):
		if self.selected_tool == 'hoe':
			self.soil_layer.get_hit(self.target_pos)
			print(self.target_pos // TILE_SIZE)
			
			# Cập nhật nhiệm vụ đào đất
			if hasattr(self, 'mission_manager') and self.mission_manager:
				self.mission_manager.update_missions_by_action('dig', None, 1)
		
		if self.selected_tool == 'axe':
			for tree in self.tree_sprites.sprites():
				if isinstance(tree, Tree):
					if tree.rect.collidepoint(self.target_pos) or tree.rect.inflate(10, 10).collidepoint(self.target_pos):
							tree.damage()
							if not tree.alive():
								if hasattr(self, 'mission_manager') and self.mission_manager:
									self.mission_manager.update_missions_by_action('chop', None, 1)

				else:
					print(f"Unexpected class: {type(tree)}")

		
		if self.selected_tool == 'water':
			self.soil_layer.water(self.target_pos)
			watering_sound.play()
			
			# Cập nhật nhiệm vụ tưới nước
			if hasattr(self, 'mission_manager') and self.mission_manager:
				self.mission_manager.update_missions_by_action('water', None, 1)
	
	def get_target_pos(self):
		self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]
   
	def use_seed(self):
		seed_name = f'{self.selected_item}'
		if self.has_item(seed_name):
			if self.soil_layer.plant_seed(self.target_pos, self.selected_item):
				self.remove_item(seed_name, 1)
				print(f'Used {seed_name}')
				# Cập nhật nhiệm vụ
				if hasattr(self, 'mission_manager') and self.mission_manager:
						self.mission_manager.update_missions_by_action('plant', seed_name.replace(' seeds', ''), 1)


	def import_assets(self):
		directions = ['down', 'up', 'left', 'right']
		actions = ['idle', 'move', 'hoe', 'axe', 'water']
		self.animations = { f'{direction}_{action}': [] for direction in directions for action in actions}
		
		for animation in self.animations.keys():
			full_path = f'{GRAPHICS_PATH}/character/' + animation
			self.animations[animation] = import_folder(full_path)

	def animate(self, dt):
		self.frame_index += 4 * dt
		if self.frame_index >= len(self.animations[self.status]):
			self.frame_index = 0
		self.image = self.animations[self.status][int(self.frame_index)]

	def update_hotbar(self):	
		self.hotbar = []
		for index, item in enumerate(self.inventory.items):
			if item is not None and index < 6 and item.item_name != 'coins':
				self.hotbar.append(item.item_name)

		if self.hotbar:
			if self.hotbar_index >= len(self.hotbar):
				self.hotbar_index = len(self.hotbar) - 1
			self.selected_item = self.hotbar[self.hotbar_index]
		else:
			self.selected_item = None

	def input(self):
		keys = pygame.key.get_pressed()
		self.direction.x = 0
		self.direction.y = 0
		if not self.timers['tool use'].active and not self.sleep:
			# Movement
			if keys[self.keys_bind['move']['up']]:
				self.direction.y = -1
				self.status = 'up_move'
			elif keys[self.keys_bind['move']['down']]:
				self.direction.y = 1
				self.status = 'down_move'
			if keys[self.keys_bind['move']['left']]:
				self.direction.x = -1
				self.status = 'left_move'
			elif keys[self.keys_bind['move']['right']]:
				self.direction.x = 1
				self.status = 'right_move'
			# Tools use
			if keys[self.keys_bind['action']['use tool']] or pygame.mouse.get_pressed()[0]:
				self.timers['tool use'].activate()
				self.direction = pygame.math.Vector2()
				self.frame_index = 0
			

			# Seed use
			if keys[self.keys_bind['action']['use seed']]:
				if self.selected_item.endswith('seeds'):
					self.timers['seed use'].activate()
					self.direction = pygame.math.Vector2()
					self.frame_index = 0

			# Interaction
			if keys[self.keys_bind['action']['interact']]:
				collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction_sprites, False)
				if collided_interaction_sprite:
					if collided_interaction_sprite[0].name == 'Trader':
						self.mission_manager.update_mission_progress(11, 1)
						self.toggle_shop()
					elif collided_interaction_sprite[0].name == 'Bed':
						self.status = 'left_idle'
						self.sleep = True
					elif collided_interaction_sprite[0].name == 'Mayor':
						self.talking_to = 'Mayor'
						self.talking = True
						self.mission_manager.update_mission_progress(10, 1)
						self.mission_manager.update_mission_progress(11, 1)

			if keys[self.keys_bind['action']['interact']] and self.groups()[0].debug_mode:
				self.toggle_shop()

			# Inventory UI toggle
			if keys[self.keys_bind['action']['toggle inventory']] and not self.timers['inventory open'].active:
				self.timers['inventory open'].activate()  # E để mở/đóng inventory
				self.inventory_ui.toggle()

			if keys[pygame.K_F1] and not self.timers['debug mode'].active:
				self.timers['debug mode'].activate()
				self.groups()[0].toggle_debug()

	def get_status(self):
		if self.direction.magnitude() == 0:
			self.status = self.status.split('_')[0] + '_idle'
		if self.timers['tool use'].active:
			self.status = self.status.split('_')[0] + f'_{self.selected_tool}'

	def update_timers(self):
		for timer in self.timers.values():
			timer.update()

	def collision(self, direction):
		# Check collision with both obstacles and trees
		for sprite in list(self.tree_sprites.sprites()) + list(self.obstacle_sprites.sprites()):
			if hasattr(sprite, 'hitbox'):
				if sprite.hitbox.colliderect(self.hitbox):
					if direction == 'horizontal':
						if self.direction.x > 0:  # Moving right
							self.hitbox.right = sprite.hitbox.left
						if self.direction.x < 0:  # Moving left
							self.hitbox.left = sprite.hitbox.right
						self.rect.centerx = self.hitbox.centerx
						self.pos.x = self.hitbox.centerx
					
					if direction == 'vertical':
						if self.direction.y > 0:  # Moving down
							self.hitbox.bottom = sprite.hitbox.top
						if self.direction.y < 0:  # Moving up
							self.hitbox.top = sprite.hitbox.bottom
						self.rect.centery = self.hitbox.centery
						self.pos.y = self.hitbox.centery

	def move(self, dt):
		if self.direction.magnitude() > 0:
			self.direction = self.direction.normalize()

		# Horizontal movement
		self.pos.x += self.direction.x * self.speed * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collision('horizontal')

		# Vertical movement
		self.pos.y += self.direction.y * self.speed * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collision('vertical')

	def update(self, dt):
		self.input()
		self.get_status()
		self.update_timers()
		self.get_target_pos()
		self.move(dt)
		self.animate(dt)
		# Draw inventory UI only
		self.inventory_ui.draw()
		self.update_hotbar()





