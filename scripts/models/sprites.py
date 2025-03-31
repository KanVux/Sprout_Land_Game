import math
from random import choice, randint
import pygame
from settings import *
class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups, z = LAYERS['main']):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = z
		self.hitbox = self.rect.copy()
	
class Interaction(Generic):
	def __init__(self, pos, size, groups, name):
		surf = pygame.Surface(size)
		self.name = name
		super().__init__(pos, surf, groups)

class Water(Generic):
	def __init__(self, pos, frames, groups):
		# Animation setup
		self.frames = frames
		self.frame_index = 0

		super().__init__(
						pos,
						surf= self.frames[self.frame_index],
						groups= groups,
						z = LAYERS['water'],
						)
	
	def animate(self, dt):
		self.frame_index += 5 * dt
		if self.frame_index >= len(self.frames):
			self.frame_index = 0
		self.image = self.frames[int(self.frame_index)]
	
	def update(self, dt):
		self.animate(dt)

class WildFlower(Generic):
	def __init__(self, pos, surf, groups):     
		super().__init__(pos, surf, groups)
		self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)

class Particle(Generic):
	def __init__(self, pos, surf, groups, z, duration = 200):
		super().__init__(pos, surf, groups, z)
		self.start_time = pygame.time.get_ticks()
		self.duration = duration

		mask_surf = pygame.mask.from_surface(self.image)
		new_surf = mask_surf.to_surface()
		new_surf.set_colorkey((0,0,0))
		self.image = new_surf	
	
	def update(self, dt):
		current_time = pygame.time.get_ticks()
		if current_time - self.start_time > self.duration:
			self.kill()

class Apple(Generic):
	def __init__(self, pos, groups):
		# Tải hình ảnh và chuyển đổi alpha để tối ưu hiệu suất
		surf = pygame.image.load(f"{GRAPHICS_PATH}/fruit/apple.png").convert_alpha()
		super().__init__(pos, surf, groups, LAYERS['fruit'])
		self.all_sprite = groups[0]

		# Thêm hitbox nhỏ hơn để phát hiện va chạm chính xác hơn
		self.hitbox = self.rect.inflate(-5, -5)
		
		# Âm thanh khi thu thập táo
		# self.collect_sound = pygame.mixer.Sound(f"{AUDIO_PATH}/apple_collect.mp3")
		# self.collect_sound.set_volume(0.4)
		
	def collect(self, player_add):
		"""Phương thức mới để xử lý việc thu thập táo"""
		# self.collect_sound.play()
		player_add('apple', 1)
		self.kill()
	
	def drop(self):
		"""Xử lý hiệu ứng rơi cho táo."""

		self.kill()
		# Nếu cần, chuyển apple sang một group update rơi khác

class Tree(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups, name, player_add, z=LAYERS['main']):
		super().__init__(groups)
		
		# Basic setup
		self.image = surf
		self.rect = self.image.get_rect(topleft=pos)
		self.z = z
		self.name = name
		self.player_add = player_add
		self.all_sprite = groups[0]
		# Hitbox setup
		self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.6, -self.rect.height * 0.5)
		self.hitbox.y = self.rect.y + 50
		
		# tree attributes
		self.health = TREE_ATTR[name]['health']
		self.wood_yield = TREE_ATTR[name]['wood']

		
		self.max_health = self.health
		self.tree_alive = True
		stump_path = f'{GRAPHICS_PATH}/world/stumps/{"small" if self.name == "Small" else "large"}.png'
		self.stump_surf = pygame.image.load(stump_path)
		
		# Initialize apple attributes
		self.setup_apple_attributes()  # Add this line to call the setup method
	
		
	def setup_apple_attributes(self):
		"""Thiết lập các thuộc tính liên quan đến táo"""
		self.apple_sprites = pygame.sprite.Group()
		self.apple_surf = pygame.image.load(f'{GRAPHICS_PATH}/fruit/apple.png')
		
		# Thêm thời gian tái sinh táo
		self.apple_spawn_time = 60  # 60 giây
		self.apple_timer = randint(10, self.apple_spawn_time)  # Khởi tạo ngẫu nhiên
		
		# if self.tree_alive:
		# 	self.create_fruit()
		
		
		# Thêm hiệu ứng rung
		self.shake_timer = 0
		self.shake_duration = 0.3  # 0.3 giây
		self.offset = pygame.math.Vector2(0, 0)
		self.base_pos = pygame.math.Vector2(self.rect.topleft)
		
		# Thêm thời gian tái sinh cây
		self.respawn_time = 3 * 24 * 60 * 1000
		self.respawn_timer = 0
		
	
	def damage(self):
		"""Xử lý khi cây bị tấn công"""
		# Chỉ gây sát thương nếu cây còn sống
		if not self.tree_alive:
			return
			
		# Gây sát thương cho cây
		self.health -= 1
		
		# Phát âm thanh và hiệu ứng rung
		if self.health >= 0:
			chopping_sound.play()
			self.shake_timer = self.shake_duration
		
		# Rụng táo ngẫu nhiên
		if len(self.apple_sprites.sprites()) > 0:
				random_apple = choice(self.apple_sprites.sprites())
				if isinstance(random_apple, Apple):
					random_apple.collect(self.player_add)
					Particle(
						pos=random_apple.rect.topleft,
						surf=random_apple.image,
						groups=self.all_sprite,
						z=LAYERS['fruit'],
						duration=300
					)
		# Đảm bảo số táo không vượt quá máu hiện tại sau khi bị tấn công
		self.adjust_apples_to_health()
		
		# Kiểm tra nếu cây chết
		if self.health <= 0:
			# self.fall_sound.play()  # Phát âm thanh cây đổ
			self.player_add('wood', self.wood_yield)  # Thêm gỗ dựa vào loại cây
			self.die()
				
	def adjust_apples_to_health(self):
		"""Điều chỉnh số táo không vượt quá máu hiện tại của cây"""
		current_apples = len(self.apple_sprites.sprites())
		
		# Nếu số táo nhiều hơn máu hiện tại, loại bỏ táo thừa
		while current_apples > self.health and current_apples > 0:
				random_apple = choice(self.apple_sprites.sprites())
				if isinstance(random_apple, Apple):
					random_apple.collect(self.player_add)
					current_apples -= 1
		
	def shake(self):
		"""Phương thức mới để rung cây khi tương tác"""
		if self.tree_alive:
			self.shake_timer = self.shake_duration
			
			# Có cơ hội rơi táo khi rung cây
			if len(self.apple_sprites.sprites()) > 0 and randint(0, 2) == 0:
				random_apple = choice(self.apple_sprites.sprites())
				if isinstance(random_apple, Apple):
					random_apple.collect(self.player_add)
	
	def update_shake(self, dt):
		"""Cập nhật hiệu ứng rung cây"""
		if self.shake_timer > 0:
			self.shake_timer -= dt
			intensity = (self.shake_timer / self.shake_duration) * 4
			self.offset.x = math.sin(pygame.time.get_ticks() * 0.05) * intensity
			self.rect.topleft = self.base_pos + self.offset
			
	def check_death(self):
		"""Kiểm ra cây chết hay chưa"""
		if self.health <= 0:
			self.die()
	
	def regrow(self):
		"""Phương thức mới cho cây tái sinh"""
		if not self.tree_alive:
			self.tree_alive = True
			self.health = self.max_health
			
			# Add back to tree_sprites
			self.add(self.groups()[1])  # Add back to tree_sprites
			
			self.image = pygame.image.load(f'{GRAPHICS_PATH}/objects/tree_{self.name.lower()}.png').convert_alpha()
			self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
			self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.6, -self.rect.height * 0.5)
			self.hitbox.y = self.rect.y + 50
			self.base_pos = pygame.math.Vector2(self.rect.topleft)
			
			# Tạo táo mới khi cây mọc lại
			self.create_fruit()
	
	def update_respawn(self, dt):
		"""Cập nhật thời gian tái sinh"""
		if not self.tree_alive and self.respawn_timer > 0:
			self.respawn_timer -= dt
			if self.respawn_timer <= 0:
				self.regrow()
	
	def grow_apples(self, dt):
		"""Phương thức mới để táo tự mọc lại theo thời gian"""
		if self.tree_alive and len(self.apple_sprites.sprites()) < self.health - 1:
			self.apple_timer -= dt
			if self.apple_timer <= 0:
				# Tạo một táo mới nếu số táo hiện tại < máu của cây
				if len(self.apple_sprites.sprites()) < self.health - 1:
					self.add_random_apple()
				# Đặt lại hẹn giờ
				self.apple_timer = self.apple_spawn_time
	
	def die(self):
		"""Xử lý khi cây chết"""
		if self.tree_alive:
			Particle(
				pos=self.rect.topleft, 
				surf=self.image, 
				groups=[self.all_sprite],
				z=LAYERS['fruit'], 
				duration=200
			)
			# Chuyển cây thành gỗ (stump)
			if self.name == 'Medium':
				self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.6, -self.rect.height * 0.7)
				self.hitbox.x = self.rect.x + 28
				self.hitbox.y = self.rect.y + 70
			elif self.name == 'Small':
				self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.58, -self.rect.height * 0.7)
				self.hitbox.x = self.rect.x + 21
				self.hitbox.y = self.rect.y + 70

			self.image = self.stump_surf
			stump_rect = self.image.get_rect()
			stump_rect.midbottom = self.rect.midbottom
			self.rect = stump_rect
			self.tree_alive = False

			# Thay vì empty() các táo, hãy gọi drop() để cho chúng rơi
			for apple in list(self.apple_sprites):
				apple.drop()  # Phương thức drop() sẽ xử lý hiệu ứng rơi, kiểm soát chuyển group, v.v.
			# Bạn có thể thiết lập lại self.apple_sprites = pygame.sprite.Group() nếu cần

			self.respawn_timer = self.respawn_time
	
	def get_random_upper_position(self):
		"""Tạo vị trí ngẫu nhiên ở nửa trên của sprite cây"""
		# Kích thước của táo để tránh đặt quá gần mép
		apple_size = 16  # Giả sử táo có kích thước 16x16 px
		padding = 5  # Padding để táo không xuất hiện quá sát mép
		
		# Chỉ lấy nửa trên của sprite cây
		top_half_height = self.rect.height * 0.5
		
		# Tạo vị trí ngẫu nhiên trong khoảng an toàn
		x = randint(padding, self.rect.width - apple_size - padding)
		y = randint(padding, int(top_half_height) - apple_size - padding)
		
		return (x, y)

	def add_random_apple(self):
		"""Thêm một táo ngẫu nhiên vào vị trí ngẫu nhiên ở nửa trên của cây"""
		# Kiểm tra nếu số táo đã đạt giới hạn (bằng máu hiện tại)
		if len(self.apple_sprites.sprites()) >= self.health:
			return
			
		# Tạo vị trí ngẫu nhiên cho táo mới
		random_pos = self.get_random_upper_position()
		
		# Kiểm tra vị trí mới không chồng lên táo hiện có
		is_valid_position = True
		min_distance = 20  # Khoảng cách tối thiểu giữa các táo
		
		for apple in self.apple_sprites:
			# Tính khoảng cách từ vị trí mới đến táo hiện có
			apple_rel_pos = (apple.rect.x - self.rect.x, apple.rect.y - self.rect.y)
			distance = math.sqrt((random_pos[0] - apple_rel_pos[0])**2 + (random_pos[1] - apple_rel_pos[1])**2)
			
			if distance < min_distance:
				is_valid_position = False
				break
		
		# Nếu vị trí hợp lệ, tạo táo mới
		if is_valid_position:
			x = random_pos[0] + self.rect.left
			y = random_pos[1] + self.rect.top
			Apple(
				pos=(x, y), 
				groups=[self.apple_sprites, self.all_sprite]
			)
		
	def update(self, dt):
		if self.tree_alive:
			self.apple_sprites.update(dt)
			self.check_death()
			self.grow_apples(dt)  # Thêm phương thức mọc táo mới vào update
		self.update_respawn(dt)
		self.update_shake(dt)

	def create_fruit(self):
		"""Tạo táo ban đầu cho cây, đảm bảo hitbox được khởi tạo chính xác."""
		self.apple_sprites.empty()
		
		if self.tree_alive and self.health > 0:
			# Tạo số táo ngẫu nhiên dựa trên health
			num_apples = randint(0, self.health - 1)
			attempts = 0
			apples_created = 0
			
			while apples_created < num_apples and attempts < 20:
				attempts += 1
				random_pos = self.get_random_upper_position()
				
				# Kiểm tra vị trí hợp lệ
				is_valid = True
				for apple in self.apple_sprites.sprites():
					apple_rel_pos = (apple.rect.x - self.rect.x, apple.rect.y - self.rect.y)
					distance = math.sqrt((random_pos[0] - apple_rel_pos[0])**2 + (random_pos[1] - apple_rel_pos[1])**2)
					if distance < 20:  # Khoảng cách tối thiểu giữa táo
						is_valid = False
						break
						
				if is_valid:
					x = random_pos[0] + self.rect.left
					y = random_pos[1] + self.rect.top
					# Tạo đối tượng Apple và đảm bảo nó được thêm vào cả group của táo và group tổng
					apple = Apple(pos=(x, y), groups=[self.apple_sprites, self.all_sprite])
					# Khởi tạo lại hitbox cho apple
					apple.hitbox = apple.rect.inflate(-5, -5)
					apples_created += 1

	def plant_tree_at(position, num_apple, health, groups, tree_name, player_add):
		tree_image = pygame.image.load(f"{GRAPHICS_PATH}/world/objects/tree_{tree_name.lower()}.png").convert_alpha()
		tree = Tree(
			pos=position,
			surf=tree_image,
			groups=groups,
			name=tree_name,
			player_add= player_add,
			z=LAYERS['main']
		)
		tree.rect.topleft = position
		tree.health = health
		return tree


