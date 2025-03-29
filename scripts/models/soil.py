from random import choice
import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from scripts.helpers.support import *
from scripts.helpers.timer import *

class SoilTile(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
	def __init__(self, plant_type, groups, soil, check_watered):
		super().__init__(groups)
		self.plant_type = plant_type
		# Import folder cho loại cây; đảm bảo folder tồn tại và tên khớp
		self.frames = import_folder(f"{GRAPHICS_PATH}/fruit/{plant_type}")
		if not self.frames:
			raise ValueError(f"Không tìm thấy asset cho cây: {plant_type}")
		self.soil = soil
		self.check_watered = check_watered

		self.age = 0
		self.max_age = len(self.frames) - 1
		self.grow_speed = GROW_SPEED.get(plant_type, 0.05) / 1000
		self.harvestable = False

		self.last_watered = pygame.time.get_ticks()
		self.water_deadline = SEED_PROP.get('thirsty', 10 * 1000)
		self.needs_water = True

		self.image = self.frames[self.age]
		self.y_offset = -16 
		self.rect = pygame.Rect(0, 0, 0, 0) 
		
		# self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

		self.z = LAYERS['ground plant']
		self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.4, -self.rect.height * 0.4)

	def check_water_status(self):
		"""Check if plant has been watered and update status"""
		current_time = pygame.time.get_ticks()
		is_watered = self.check_watered
		if is_watered:
			self.last_watered = current_time
			self.needs_water = False
		else:
			# Check if too long without water
			time_since_water = current_time - self.last_watered
			if time_since_water >= self.water_deadline:
				# Plant dies from lack of water
				self.kill()
				self.soil.grid[self.soil.rect.y // TILE_SIZE][self.soil.rect.x // TILE_SIZE].remove('P')
				return False
			
			self.needs_water = True
		
		return True

	def grow(self):
		# First check water status
		if not self.check_water_status():
			return

		# Only grow if currently watered
		if not self.needs_water:
			if self.age >= self.max_age:
				self.z = LAYERS['main']
				self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.8)
				self.hitbox.bottom = self.rect.bottom
				self.age = self.max_age
				self.harvestable = True
			else:
				self.age += self.grow_speed
				self.image = self.frames[int(self.age)]
				self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

		# Update sprite position even if not growing
		self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoildLayer:
	def __init__(self, all_sprites, collision_sprites):
		
		self.all_sprites = all_sprites
		self.collision_sprites = collision_sprites
		self.soil_sprites = pygame.sprite.Group()
		self.water_sprites = pygame.sprite.Group()
		self.plant_sprites = pygame.sprite.Group()
		# Assets
		self.soil_surfs = import_folder_dict(f'{GRAPHICS_PATH}/soil/')
		self.water_surfs = import_folder(f'{GRAPHICS_PATH}/soil_water/')
		
		self.create_soil_grid()
		self.create_hit_rects()
		
		# Add soil timers
		self.soil_timers = {}  # Format: {(x,y): Timer()}
		self.soil_duration = SOIL_PROP.get('dryout', 5 * 1000)  


	def create_soil_grid(self):
		ground = pygame.image.load(f'{GRAPHICS_PATH}/world/ground.png')
		h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE
		
		self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)] 
		for x,y, _ in load_pygame(f'{MAPS_PATH}/map.tmx').get_layer_by_name('Farmable').tiles():
			self.grid[y][x].append('F')
	
	def create_hit_rects(self):
		self.hit_rects = []
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'F' in cell:
					x = index_col * TILE_SIZE
					y = index_row * TILE_SIZE
					rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
					self.hit_rects.append(rect)
	
	def get_hit(self, point):
		for rect in self.hit_rects:
			if rect.collidepoint(point):
				tilt_sound.play()
				x = rect.x // TILE_SIZE
				y = rect.y // TILE_SIZE

				if 'F' in self.grid[y][x] and not 'X' in self.grid[y][x]:
					self.grid[y][x].append('X')
					self.create_soil_tiles()
					if (x, y) not in self.soil_timers:
						# Chỉ tạo mới Timer khi chưa có timer cho tile này
						self.soil_timers[(x, y)] = Timer(self.soil_duration, self.remove_soil_tile, x, y)
						self.soil_timers[(x, y)].activate()

						if self.all_sprites.debug_mode:
							self.plant_seed_at(
								(x * TILE_SIZE, y * TILE_SIZE),
								'carrot',
								3,
								True
							)
				print(self.grid[y][x])
						
	def water(self, target_pos):
		for soil_prite in self.soil_sprites.sprites():
			if soil_prite.rect.collidepoint(target_pos):
				x = soil_prite.rect.x // TILE_SIZE
				y = soil_prite.rect.y // TILE_SIZE
				
				if 'W' not in self.grid[y][x]:
					self.grid[y][x].append('W')
					pos = soil_prite.rect.topleft
					surf = choice(self.water_surfs)
					WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

	def water_all(self):
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'X' in cell and 'W' not in cell:
					cell.append('W')
					x = index_col * TILE_SIZE
					y = index_row * TILE_SIZE
					WaterTile(
						pos= (x,y),
						surf= choice(self.water_surfs),
						groups=[self.all_sprites, self.water_sprites]
					)
	
	def remove_water(self):
		for sprite in self.water_sprites.sprites():
			sprite.kill()

		for row in self.grid:
			for cell in row:
				if 'W' in cell:
					cell.remove('W')

	def check_watered(self, pos):
		x = pos[0] // TILE_SIZE
		y = pos[1] // TILE_SIZE
		cell = self.grid[y][x]
		is_watered = 'W' in cell
		return is_watered

	def plant_seed(self, target_pos, seed_type):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):
				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE

				if 'P' not in self.grid[y][x]:
					# Remove timer when plant is added
					if (x,y) in self.soil_timers:
						del self.soil_timers[(x,y)]
					
					self.grid[y][x].append('P')
					Plant(
						plant_type= seed_type,
						soil= soil_sprite,
						groups= [self.all_sprites, self.plant_sprites, self.collision_sprites],
						check_watered= self.check_watered
					)
					plant_seed_sound.play()
					
					
					
					return True
		return False
	
	def update_plant(self):
		for plant in self.plant_sprites.sprites():
			# Store position before potential death
			x = plant.rect.centerx // TILE_SIZE
			y = plant.rect.centery // TILE_SIZE
			
			plant.grow()
			
			# If plant died, remove it from grid
			if plant not in self.plant_sprites:
				if 'P' in self.grid[y][x]:
					self.grid[y][x].remove('P')

	def create_soil_tiles(self):
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'X' in cell:

					t = 'X' in self.grid[index_row - 1][index_col]
					b = 'X' in self.grid[index_row + 1][index_col]
					r = 'X' in row[index_col + 1]
					l = 'X' in row[index_col - 1]

					tile_type = 'o'

					if all((t, b, r, l)): tile_type = 'x'
					
					if l and not any((t,r,b)): tile_type = 'r'
					if r and not any((t,l,b)): tile_type = 'l'
					if r and l and not any ((t, b)): tile_type = 'lr'

					if t and not any((r,l,b)): tile_type = 'b'
					if b and not any((r,l,t)): tile_type = 't'
					if t and b and not any((r,l)): tile_type = 'tb'

					if l and b and not any((r,t)): tile_type = 'tr'
					if r and b and not any((l,t)): tile_type = 'tl'
					if l and t and not any((r,b)): tile_type = 'br'
					if r and t and not any((l,b)): tile_type = 'bl'

					if all((t,b,r)) and not l: tile_type = 'tbr'
					if all((t,b,l)) and not r: tile_type = 'tbl'
					if all((l,r,t)) and not b: tile_type = 'lrb'
					if all((l,r,b)) and not t: tile_type = 'lrt'

					SoilTile(
						pos= (index_col * TILE_SIZE, index_row * TILE_SIZE),
						surf= self.soil_surfs[tile_type],
						groups= [self.all_sprites, self.soil_sprites])

	def remove_water_tile(self, x, y):
		if 'P' in self.grid[y][x]:
			return
				# Xóa sprite water
		for sprite in self.water_sprites.sprites():
			if sprite.rect.x // TILE_SIZE == x and sprite.rect.y // TILE_SIZE == y:
				sprite.kill()
		if 'W' in self.grid[y][x]:
			self.grid[y][x].remove('W')
			self.soil_timers[(x, y)] = Timer(self.soil_duration, self.remove_soil_tile, x, y)
			self.soil_timers[(x, y)].activate()

	def remove_soil_tile(self, x, y):
		"""Remove a soil tile at given coordinates"""

		if 'P' in self.grid[y][x]:
			return		
		
		if 'W' in self.grid[y][x]:
			self.remove_water_tile(x, y)
			return	
		
		# Xóa sprite soil
		for sprite in self.soil_sprites.sprites():
			if sprite.rect.x // TILE_SIZE == x and sprite.rect.y // TILE_SIZE == y:
				sprite.kill()

		# Cập nhật grid
		if 'X' in self.grid[y][x]:
			self.grid[y][x].remove('X')

		# Xóa timer
		if (x, y) in self.soil_timers:
			del self.soil_timers[(x, y)]  # Xóa timer khi đã xóa soil tile
		
		self.create_soil_tiles()

	def update(self, dt):
		"""Update soil layer state"""
		self.soil_sprites.update()
		self.update_plant()
		if self.raining:
			self.water_all()

		# Duyệt qua một bản sao của soil_timers để kiểm tra các timer đã hết hạn
		for pos, timer in list(self.soil_timers.items()):
			timer.update()

			# if not timer.active:
			# 	print(f"Timer for {pos} finished, removing soil tile")
			# 	self.remove_soil_tile(*pos)

			# 	# Xóa timer một cách an toàn
			# 	if pos in self.soil_timers:
			# 		del self.soil_timers[pos]  # Xóa timer khi đã xử lý

	def plant_seed_at(self, position, plant_type, age=0, watered=False):
		"""Trồng cây tại vị trí xác định với các thuộc tính đã cho.
		   Lưu ý: position được lưu từ cây (có y_offset) nên phải điều chỉnh về gốc tile."""
		# Giả sử y_offset mặc định của cây là -16 (có thể lấy từ Plant.y_offset)
		default_y_offset = 16  # Lấy giá trị dương của offset
	
		# Điều chỉnh position để lấy tile đúng (với bottom của tile)
		grid_x = position[0] // TILE_SIZE
		grid_y = (position[1] + default_y_offset) // TILE_SIZE
		desired_origin = (grid_x * TILE_SIZE, grid_y * TILE_SIZE)
	
		# Tìm soil sprite có gốc tile khớp desired_origin
		target_soil = None
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.topleft == desired_origin:
				target_soil = soil_sprite
				break
	
		if not target_soil:
			print(f"Không tìm thấy soil sprite cho tile ({grid_x}, {grid_y}).")
			return False
	
		# Kiểm tra marker cày
		if 'X' not in self.grid[grid_y][grid_x]:
			print(f"Tile ({grid_x}, {grid_y}) chưa cày, không cho trồng cây.")
			return False
	
		# Xóa cây cũ (nếu có) trong ô này
		for plant in self.plant_sprites.sprites():
			if (plant.rect.centerx // TILE_SIZE == grid_x and 
				plant.rect.centery // TILE_SIZE == grid_y):
				plant.kill()
	
		# Đánh dấu ô có cây nếu chưa có
		if 'P' not in self.grid[grid_y][grid_x]:
			self.grid[grid_y][grid_x].append('P')
	
		try:
			plant = Plant(
				plant_type=plant_type,
				groups=[self.all_sprites, self.plant_sprites, self.collision_sprites],
				soil=target_soil,
				check_watered=lambda pos=target_soil.rect.midbottom: self.check_watered(pos)
			)
		except Exception as e:
			print(f"Lỗi khi tạo plant {plant_type} tại tile ({grid_x}, {grid_y}): {e}")
			return False
	
		plant.age = age
		try:
			plant.image = plant.frames[int(age)]
		except Exception as e:
			print(f"Lỗi khi cập nhật hình cho {plant_type} với age {age}: {e}")
			return False
	
		# Định vị lại cây dựa trên gốc của soil sprite
		exact_pos = target_soil.rect.midbottom
		plant.rect = plant.image.get_rect(midbottom=exact_pos)
		plant.rect.y += plant.y_offset
	
		if watered:
			self.water((grid_x * TILE_SIZE, grid_y * TILE_SIZE))
		return True

	def recreate_water_tiles(self):
		"""Tái tạo water tile theo grid nếu có marker 'W'"""
		for row_index, row in enumerate(self.grid):
			for col_index, cell in enumerate(row):
				if 'W' in cell:
					# Xóa water sprite cũ của ô này (nếu có)
					for sprite in self.water_sprites.sprites():
						if sprite.rect.x // TILE_SIZE == col_index and sprite.rect.y // TILE_SIZE == row_index:
							sprite.kill()
					pos = (col_index * TILE_SIZE, row_index * TILE_SIZE)
					WaterTile(pos, choice(self.water_surfs), [self.all_sprites, self.water_sprites])








