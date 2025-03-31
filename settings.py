import pygame
from pygame.math import Vector2
# screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64
FPS = 60


# assets path
GRAPHICS_PATH  = 'assets/graphics'
AUDIO_PATH = 'assets/audio'
MAPS_PATH = 'assets/data'
FONT_PATH = 'assets/font'





PLAYER_TOOL_OFFSET = {
	'left': Vector2(-50,40),
	'right': Vector2(50,40),
	'up': Vector2(0,-10),
	'down': Vector2(0,50)
}


LAYERS = {
	'water': 0,
	'ground': 1,
	'soil': 2,
	'soil water': 3,
	'rain floor': 4,
	'house bottom': 5,
	'ground plant': 6,
	'main': 7,
	'house top': 8,
	'fruit': 9,
	'rain drops': 10
}


DIALOG = {
	'bonnie': {
	   'gretting': [
			"If you’re looking to trade, I’m always open. I’ve got some great deals and rare items!",
			"Feel free to pick whatever you like, or if you’ve got something to trade, we can work out a deal!",
			"Don’t be shy, let me know what you want and we’ll make it happen!"
		],
		'goodbye': [
			"Don’t forget to come back when you need anything else, I’m always getting new stock!",
			"I hope you found what you needed. Don’t hesitate to return if you need more!",
			"Thanks for stopping by, see you again soon!"
		]
	}
	
}	

SEED_PROP = {
	'thirsty': 12 * 60 * 1000, # 0.5 ngày in-game
}

# debug nên cho = 1 sẽ sửa lại sau
GROW_SPEED = { 
	'corn': 1, 
	'tomato': 1, 
	'carrot': 1,
	'wheat': 1,
	# note: thêm cây 
}

SLEEP_PROP = {
	'duration': {
		'day' : 2 * 60, # 2 tiếng 
		'night': 6 * 60 # 6 tiếng
	},
	'threshold': {
		'day': 4, # Trước 4h sáng sẽ được ngủ 6 tiếng
		'night': 18 # Sau 6h sáng sẽ được ngủ 6 tiếng
	}

}


RAIN_PROP = {
	'chance': 0.005, # 0.5% mỗi frame để thay đổi thời tiết
	'duration': {
		'min': 20 * 1000 , # Ít nhất mưa kéo dài 20 giây 
		'max': 60 * 1000 # Dài nhất mưa kéo dài 60 giây
	},
}

SOIL_PROP = {
	'dryout': 1000 * 3#12 * 60 * 1000  # 0.5 ngày in-game
}

TREE_ATTR = {
	'Small': {
		'health': 5,
		'wood': 1
	},
	'Medium': {
		'health': 8,
		'wood': 3
	},
}


DEFAULT_KEY_BIND = {
	'move': {
		'up': pygame.K_w,
		'down': pygame.K_s,
		'left': pygame.K_a,
		'right': pygame.K_d
	},
	'action': {
		'use tool': pygame.K_SPACE,
		'use seed': pygame.K_r,
		'interact': pygame.K_q,
		'batch trade': pygame.K_LSHIFT,
		'toggle inventory': pygame.K_e
	}
}

from scripts.db.settings_db import SettingsDB
settings_data = SettingsDB.get_settings()
keys_bind = settings_data['keys_bind']

def update_key_bind(new_keybind):
    global keys_bind
    keys_bind = new_keybind

pygame.mixer.init()

default_volume = 3
global_volume = settings_data['volume']

collect_item_sound = pygame.mixer.Sound(f'{AUDIO_PATH}/success.wav')
background_music = pygame.mixer.Sound(f'{AUDIO_PATH}/bg.mp3')
chopping_sound =  pygame.mixer.Sound(f'{AUDIO_PATH}/axe.mp3')
tilt_sound = pygame.mixer.Sound(f'{AUDIO_PATH}/hoe.wav')
watering_sound =  pygame.mixer.Sound(f'{AUDIO_PATH}/water.mp3')
plant_seed_sound = pygame.mixer.Sound(f'{AUDIO_PATH}/plant.wav')
char_sound = pygame.mixer.Sound(f'{AUDIO_PATH}/dialog_char.mp3')
            
sounds = [
		background_music,
		collect_item_sound,
		chopping_sound, 
		tilt_sound,
		watering_sound,
		plant_seed_sound
		]

# For example, in settings.py
def set_global_volume(new_volume):
	global global_volume
	global_volume = new_volume    # new_volume should be between 0 and 10, for example.
	# Normalize the value for set_volume (expects a value between 0.0 and 1.0)
	norm_volume = global_volume / 10.0
	for sound in sounds:
		sound.set_volume(norm_volume)

