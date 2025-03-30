import pygame
from datetime import datetime
from settings import GRAPHICS_PATH, SCREEN_WIDTH, SCREEN_HEIGHT, FONT_PATH
from scripts.ui.button import Button

class MissionUI:
    def __init__(self, mission_manager):
        self.mission_manager = mission_manager
        
        # Fonts
        self.title_font = pygame.font.Font(f"{FONT_PATH}/LycheeSoda.ttf", 28)
        self.header_font = pygame.font.Font(f"{FONT_PATH}/LycheeSoda.ttf", 22)
        self.font = pygame.font.Font(f"{FONT_PATH}/LycheeSoda.ttf", 18)
        self.small_font = pygame.font.Font(f"{FONT_PATH}/LycheeSoda.ttf", 14)
        
        # Panel dimensions - use relative positioning based on screen size
        panel_width = min(380, SCREEN_WIDTH * 0.35)  # Max 35% of screen width
        panel_height = min(460, SCREEN_HEIGHT * 0.7)  # Max 70% of screen height
        self.bg_rect = pygame.Rect(20, 20, panel_width, panel_height)
        self.bg_color = (30, 30, 30, 220)
        self.highlight_color = (60, 60, 80, 250)
        self.category_btn_color = (80, 80, 100)
        self.category_btn_selected_color = (100, 100, 140)
        
        # Mission list and selection
        self.mission_list = []
        self.selected_mission = None
        self.selected_index = -1
        self.scroll_offset = 0
        self.max_visible_missions = 10
        self.entry_height = 36
        
        # Display state
        self.is_visible = True
        self.show_completed = False
        self.current_category = "all"  # all, story, daily, weekly, chained, one_time
        
        # Calculate button sizes based on panel width
        btn_width = (self.bg_rect.width - 60) / 5  # 5 buttons with 10px margins
        btn_y = self.bg_rect.y + 40
        
        # Filter buttons - positioned dynamically based on panel width
        self.category_buttons = {
            "all": pygame.Rect(self.bg_rect.x + 10, btn_y, btn_width, 25),
            "story": pygame.Rect(self.bg_rect.x + 10 + btn_width + 5, btn_y, btn_width, 25),
            "daily": pygame.Rect(self.bg_rect.x + 10 + (btn_width + 5) * 2, btn_y, btn_width, 25),
            "weekly": pygame.Rect(self.bg_rect.x + 10 + (btn_width + 5) * 3, btn_y, btn_width, 25),
            "one_time": pygame.Rect(self.bg_rect.x + 10 + (btn_width + 5) * 4, btn_y, btn_width, 25)
        }
        
        # Toggle completed missions button
        self.completed_toggle_rect = pygame.Rect(self.bg_rect.x + 10, self.bg_rect.y + self.bg_rect.height - 30, 180, 25)
        
        # Load icons
        self.mission_icons = {
            "daily": pygame.image.load(f"{GRAPHICS_PATH}/ui/mission/daily_icon.png").convert_alpha() if pygame.image.get_extended() else None,
            "weekly": pygame.image.load(f"{GRAPHICS_PATH}/ui/mission/weekly_icon.png").convert_alpha() if pygame.image.get_extended() else None,
            "story": pygame.image.load(f"{GRAPHICS_PATH}/ui/mission/story_icon.png").convert_alpha() if pygame.image.get_extended() else None,
            "chained": pygame.image.load(f"{GRAPHICS_PATH}/ui/mission/chained_icon.png").convert_alpha() if pygame.image.get_extended() else None,
            "one_time": pygame.image.load(f"{GRAPHICS_PATH}/ui/mission/one_time_icon.png").convert_alpha() if pygame.image.get_extended() else None
        }
        
        # Scale icons if loaded
        for key, icon in self.mission_icons.items():
            if icon:
                self.mission_icons[key] = pygame.transform.scale(icon, (20, 20))
        
        # Fallback colors for icons
        self.mission_type_colors = {
            "daily": (100, 149, 237),    # Cornflower blue
            "weekly": (147, 112, 219),   # Medium purple
            "story": (220, 20, 60),      # Crimson
            "chained": (255, 165, 0),    # Orange
            "one_time": (46, 139, 87)    # Sea green
        }
        
        # Reward icon
        self.reward_icon = pygame.image.load(f"{GRAPHICS_PATH}/items/coins.png").convert_alpha() if pygame.image.get_extended() else None
        if self.reward_icon:
            self.reward_icon = pygame.transform.scale(self.reward_icon, (20, 20))
        
        # Toggle button
        self.toggle_button_img = pygame.image.load(f"{GRAPHICS_PATH}/ui/mission_toggle.png").convert_alpha()
        self.toggle_button_img = pygame.transform.scale(self.toggle_button_img, (32, 42))
        self.toggle_button_img = pygame.transform.flip(self.toggle_button_img, True, False)
        # CHANGED: Initial position for toggle button will be updated in update()
        self.toggle_button_rect = self.toggle_button_img.get_rect(topright=(0, 0))
        # Animation for sliding panel
        self.target_x = self.bg_rect.x
        self.current_x = self.bg_rect.x
        self.animation_speed = 1200  # pixels per second
        
        # Scroll buttons
        self.scroll_up_rect = pygame.Rect(0, 0, 20, 20)
        self.scroll_down_rect = pygame.Rect(0, 0, 20, 20)
        
        # Initial update of all UI element positions
        self.update(0)
        
        # Update mission list
        self.update_mission_list()

    def update_mission_list(self):
        """Filter and sort missions based on current category and completion status"""
        self.mission_list = []
        for mission in self.mission_manager.missions.values():
            # Skip completed missions if not showing them
            if not self.show_completed and mission.status == "completed":
                continue
                
            # Filter by category
            if self.current_category != "all" and mission.type != self.current_category:
                continue
                
            self.mission_list.append(mission)
        
        # Sort missions: active first, then by type importance, then by ID
        def mission_sort_key(mission):
            type_priority = {
                "story": 0,
                "chained": 1,
                "daily": 2,
                "weekly": 3,
                "one_time": 4
            }
            status_priority = 0 if mission.status == "active" else 1
            return (status_priority, type_priority.get(mission.type, 99), mission.mission_id)
            
        self.mission_list.sort(key=mission_sort_key)
        
        # Reset selection if needed
        if self.selected_index >= len(self.mission_list):
            self.selected_index = -1
            self.selected_mission = None

    def toggle_visibility(self):
        """Toggle the visibility of the mission panel"""
        self.is_visible = not self.is_visible
        # Set target position for animation
        if self.is_visible:
            self.target_x = 20  # open position
        else:
            self.target_x = -self.bg_rect.width - 10  # closed position (off-screen)

    def toggle_completed(self):
        """Toggle showing completed missions"""
        self.show_completed = not self.show_completed
        self.update_mission_list()

    def set_category(self, category):
        """Set the mission category filter"""
        if category in self.category_buttons.keys():
            self.current_category = category
            self.update_mission_list()
            self.scroll_offset = 0

    def select_mission(self, index):
        """Select a mission by index"""
        if 0 <= index < len(self.mission_list):
            self.selected_index = index
            self.selected_mission = self.mission_list[index]
        else:
            self.selected_index = -1
            self.selected_mission = None

    def handle_click(self, mouse_pos):
        """Handle mouse clicks on UI elements"""
        # Check toggle button first (always visible)
        if self.toggle_button_rect.collidepoint(mouse_pos):
            self.toggle_visibility()
            return True
            
        # Only process other clicks if visible and not animating
        if not self.is_visible or self.current_x != self.target_x:
            return False
            
        # Check category buttons - FIXED: now uses the current bg_rect position
        for category, rect in self.category_buttons.items():
            # Create temporary rect with current position for more accurate detection
            current_rect = pygame.Rect(
                self.bg_rect.x + 10 + list(self.category_buttons.keys()).index(category) * (rect.width + 5),
                rect.y,
                rect.width,
                rect.height
            )
            
            if current_rect.collidepoint(mouse_pos):
                self.set_category(category)
                return True
                
        # Check completed toggle
        current_toggle_rect = pygame.Rect(
            self.bg_rect.x + 10,
            self.bg_rect.y + self.bg_rect.height - 30,
            self.completed_toggle_rect.width,
            self.completed_toggle_rect.height
        )
        
        if current_toggle_rect.collidepoint(mouse_pos):
            self.toggle_completed()
            return True
            
        # Check scroll buttons with current positions
        current_scroll_up = pygame.Rect(
            self.bg_rect.right - 30,
            self.bg_rect.y + 70,
            20, 20
        )
        
        if current_scroll_up.collidepoint(mouse_pos) and self.scroll_offset > 0:
            self.scroll_offset -= 1
            return True
            
        current_scroll_down = pygame.Rect(
            self.bg_rect.right - 30,
            self.bg_rect.bottom - 60,
            20, 20
        )
        
        if current_scroll_down.collidepoint(mouse_pos) and self.scroll_offset < max(0, len(self.mission_list) - self.max_visible_missions):
            self.scroll_offset += 1
            return True
            
        # Check mission selection - FIXED: using current panel position
        mission_area_start = self.bg_rect.y + 70
        mission_area_end = mission_area_start + self.max_visible_missions * self.entry_height
        mission_area_left = self.bg_rect.x + 10
        mission_area_right = self.bg_rect.right - 40
        
        if (mission_area_left <= mouse_pos[0] <= mission_area_right and
            mission_area_start <= mouse_pos[1] <= mission_area_end):
            
            # Calculate which mission was clicked
            clicked_index = (mouse_pos[1] - mission_area_start) // self.entry_height + self.scroll_offset
            if 0 <= clicked_index < len(self.mission_list):
                self.select_mission(clicked_index)
                return True
                
        return False

    def update(self, dt):
        """Update the mission UI state"""
        # Animate panel sliding
        if self.current_x != self.target_x:
            direction = 1 if self.target_x > self.current_x else -1
            move_amount = self.animation_speed * dt
            self.current_x += direction * move_amount
            
            # Check if reached or passed target
            if (direction == 1 and self.current_x >= self.target_x) or \
               (direction == -1 and self.current_x <= self.target_x):
                self.current_x = self.target_x
                
        # Update background rect position
        self.bg_rect.x = int(self.current_x)
        
        # Update all interactive element positions based on the current panel position
        
        # CHANGED: Update toggle button position - follows panel when open, stays visible when closed
        if self.is_visible:
            # When visible, place toggle button at right edge of panel
            self.toggle_button_rect.topright = (self.bg_rect.right + 30, self.bg_rect.y)
        else:
            # When hidden, place toggle button at visible edge of screen
            self.toggle_button_rect.topleft = (5, self.bg_rect.y)
            
        # Update category button positions - now evenly spaced based on panel width
        btn_width = (self.bg_rect.width - 60) / 5  # 5 buttons with margins
        for i, category in enumerate(self.category_buttons.keys()):
            self.category_buttons[category].x = self.bg_rect.x + 10 + i * (btn_width + 5)
            self.category_buttons[category].width = btn_width
        
        # Update other UI elements
        self.completed_toggle_rect.x = self.bg_rect.x + 10
        self.scroll_up_rect.x = self.bg_rect.right - 30
        self.scroll_up_rect.y = self.bg_rect.y + 70  # Fixed position
        self.scroll_down_rect.x = self.bg_rect.right - 30
        self.scroll_down_rect.y = self.bg_rect.bottom - 60  # Fixed position

    def draw(self, display_surface):
        """Draw the mission UI"""
        # Always draw toggle button
        display_surface.blit(self.toggle_button_img, self.toggle_button_rect)
        
        # Only draw panel if visible or animating
        if self.current_x > -self.bg_rect.width:
            # Draw semi-transparent background
            overlay = pygame.Surface((self.bg_rect.width, self.bg_rect.height), pygame.SRCALPHA)
            overlay.fill(self.bg_color)
            display_surface.blit(overlay, (self.bg_rect.x, self.bg_rect.y))
            
            # Draw title
            title = self.title_font.render("Missions", True, (255, 220, 100))
            display_surface.blit(title, (self.bg_rect.x + 10, self.bg_rect.y + 10))
            
            # Draw category buttons
            for category, rect in self.category_buttons.items():
                color = self.category_btn_selected_color if category == self.current_category else self.category_btn_color
                pygame.draw.rect(display_surface, color, rect, 0, 5)
                pygame.draw.rect(display_surface, (200, 200, 200), rect, 1, 5)
                
                # Draw category label (truncate if needed)
                category_text = category.capitalize()
                if self.small_font.size(category_text)[0] > rect.width - 6:
                    if category == "one_time":
                        category_text = "One"
                    else:
                        category_text = category_text[:4] + ".."
                        
                category_label = self.small_font.render(category_text, True, (255, 255, 255))
                label_rect = category_label.get_rect(center=rect.center)
                display_surface.blit(category_label, label_rect)
            
            # Draw mission list area background
            list_area = pygame.Rect(self.bg_rect.x + 10, self.bg_rect.y + 70, 
                                  self.bg_rect.width - 20, self.max_visible_missions * self.entry_height)
            pygame.draw.rect(display_surface, (40, 40, 50, 200), list_area, 0, 5)
            
            # Draw missions
            visible_missions = self.mission_list[self.scroll_offset:self.scroll_offset + self.max_visible_missions]
            for i, mission in enumerate(visible_missions):
                mission_idx = i + self.scroll_offset
                y_pos = self.bg_rect.y + 70 + i * self.entry_height
                
                # Highlight selected mission
                if mission_idx == self.selected_index:
                    highlight_rect = pygame.Rect(self.bg_rect.x + 10, y_pos, list_area.width, self.entry_height)
                    pygame.draw.rect(display_surface, self.highlight_color, highlight_rect, 0, 3)
                
                # Draw mission type indicator (icon or colored circle)
                if mission.type in self.mission_icons and self.mission_icons[mission.type]:
                    display_surface.blit(self.mission_icons[mission.type], (self.bg_rect.x + 15, y_pos + 8))
                else:
                    pygame.draw.circle(display_surface, self.mission_type_colors.get(mission.type, (150, 150, 150)), 
                                      (self.bg_rect.x + 25, y_pos + 18), 8)
                
                # Draw mission name with status color
                name_color = (255, 255, 255) if mission.status == "active" else (150, 150, 150)
                if mission.status == "completed":
                    name_color = (100, 255, 100)
                    
                # Calculate available width for mission name based on panel size
                available_width = self.bg_rect.width - 120  # Adjust based on other elements
                mission_name = mission.name
                if self.font.size(mission_name)[0] > available_width:
                    # Truncate name if too long
                    while self.font.size(mission_name + "...")[0] > available_width and len(mission_name) > 5:
                        mission_name = mission_name[:-1]
                    mission_name += "..."
                    
                name_text = self.font.render(mission_name, True, name_color)
                display_surface.blit(name_text, (self.bg_rect.x + 40, y_pos + 8))
                
                # Draw progress indicator
                progress_text = f"{mission.progress}/{mission.required_progress}"
                progress_color = (200, 200, 200)
                if mission.status == "completed":
                    progress_text = "Done"
                    progress_color = (100, 255, 100)
                    
                progress_surf = self.small_font.render(progress_text, True, progress_color)
                progress_rect = progress_surf.get_rect(right=self.bg_rect.right - 15, centery=y_pos + 18)
                display_surface.blit(progress_surf, progress_rect)
            
            # Draw scroll indicators if needed
            if self.scroll_offset > 0:
                pygame.draw.polygon(display_surface, (200, 200, 200), 
                                   [(self.scroll_up_rect.x, self.scroll_up_rect.y + 10),
                                    (self.scroll_up_rect.x + 10, self.scroll_up_rect.y),
                                    (self.scroll_up_rect.x + 20, self.scroll_up_rect.y + 10)])
                                    
            if self.scroll_offset < max(0, len(self.mission_list) - self.max_visible_missions):
                pygame.draw.polygon(display_surface, (200, 200, 200), 
                                   [(self.scroll_down_rect.x, self.scroll_down_rect.y),
                                    (self.scroll_down_rect.x + 10, self.scroll_down_rect.y + 10),
                                    (self.scroll_down_rect.x + 20, self.scroll_down_rect.y)])
            
            # Draw completed toggle button
            toggle_color = (100, 100, 140) if self.show_completed else (80, 80, 100)
            pygame.draw.rect(display_surface, toggle_color, self.completed_toggle_rect, 0, 5)
            pygame.draw.rect(display_surface, (200, 200, 200), self.completed_toggle_rect, 1, 5)
            
            toggle_text = "Hide Completed" if self.show_completed else "Show Completed"
            if self.bg_rect.width < 350: 
                toggle_text = "Hide Done" if self.show_completed else "Show Done"
                
            toggle_surf = self.small_font.render(toggle_text, True, (255, 255, 255))
            toggle_rect = toggle_surf.get_rect(center=self.completed_toggle_rect.center)
            display_surface.blit(toggle_surf, toggle_rect)
            
            # Draw mission details if a mission is selected
            if self.selected_mission:
                self._draw_mission_details(display_surface)

    def _draw_mission_details(self, display_surface):
        """Draw detailed information for the selected mission"""
        mission = self.selected_mission
        
        # Make sure the details section fits within the screen height
        max_details_height = min(120, SCREEN_HEIGHT - (self.bg_rect.y + 70 + self.max_visible_missions * self.entry_height + 15))
        if max_details_height < 80:  # Too small to show details meaningfully
            return
        
        # Details area - positioned below the mission list
        details_rect = pygame.Rect(
            self.bg_rect.x + 10, 
            self.bg_rect.y + 70 + self.max_visible_missions * self.entry_height + 10,
            self.bg_rect.width - 20, 
            max_details_height
        )
        pygame.draw.rect(display_surface, (50, 50, 60, 230), details_rect, 0, 5)
        
        # Mission name (header)
        header_y = details_rect.y + 10
        type_color = self.mission_type_colors.get(mission.type, (150, 150, 150))
        
        # Mission type indicator
        if mission.type in self.mission_icons and self.mission_icons[mission.type]:
            display_surface.blit(self.mission_icons[mission.type], (details_rect.x + 10, header_y))
        else:
            pygame.draw.circle(display_surface, type_color, (details_rect.x + 20, header_y + 10), 8)
        
        # Mission name - handle long names by truncating
        name_width = details_rect.width - 45  # Account for icon and padding
        name = mission.name
        if self.header_font.size(name)[0] > name_width:
            while self.header_font.size(name + "...")[0] > name_width and len(name) > 10:
                name = name[:-1]
            name += "..."
        
        name_surf = self.header_font.render(name, True, (255, 220, 150))
        display_surface.blit(name_surf, (details_rect.x + 35, header_y))
        
        # Mission type text
        type_text = mission.type.replace("_", " ").capitalize()
        type_surf = self.small_font.render(type_text, True, type_color)
        display_surface.blit(type_surf, (details_rect.x + 35, header_y + 25))
        
        # Mission description - fit to available space
        desc_y = header_y + 45
        # Adjust text wrapping to fit details area width
        desc_lines = self._wrap_text(mission.description, self.font, details_rect.width - 20)
        
        # Limit lines based on available height
        max_desc_lines = max(1, min(2, (details_rect.height - 75) // 20))
        for i, line in enumerate(desc_lines[:max_desc_lines]):
            desc_surf = self.font.render(line, True, (220, 220, 220))
            display_surface.blit(desc_surf, (details_rect.x + 10, desc_y + i * 20))
        
        # Progress bar - positioned based on details area
        progress_y = details_rect.y + details_rect.height - 30
        progress_bg = pygame.Rect(details_rect.x + 10, progress_y, details_rect.width - 20, 15)
        pygame.draw.rect(display_surface, (60, 60, 70), progress_bg, 0, 5)
        
        # Calculate progress percentage and draw filled bar
        progress_pct = min(100, int((mission.progress / max(1, mission.required_progress)) * 100))
        if progress_pct > 0:
            progress_fill = pygame.Rect(details_rect.x + 10, progress_y, 
                                      (details_rect.width - 20) * progress_pct // 100, 15)
            if mission.status == "completed":
                pygame.draw.rect(display_surface, (100, 200, 100), progress_fill, 0, 5)
            else:
                pygame.draw.rect(display_surface, (100, 150, 250), progress_fill, 0, 5)
        
        # Progress text
        progress_text = f"{progress_pct}% - {mission.progress}/{mission.required_progress}"
        if mission.status == "completed":
            progress_text = "Completed!"
            
        prog_surf = self.small_font.render(progress_text, True, (255, 255, 255))
        prog_rect = prog_surf.get_rect(center=progress_bg.center)
        display_surface.blit(prog_surf, prog_rect)
        
        # Reward information - adjustable based on space
        reward_y = progress_y - 20
        
        # Reward info
        reward_text = f"Reward: {mission.reward_quantity} {mission.reward_item}"
        if self.font.size(reward_text)[0] > details_rect.width - 20:
            # Truncate or simplify if too long
            reward_text = f"{mission.reward_quantity} {mission.reward_item}"
            
        reward_surf = self.font.render(reward_text, True, (220, 180, 80))
        display_surface.blit(reward_surf, (details_rect.x + 10, reward_y))
        
        # Draw reward icon if available and space permits
        if self.reward_icon and reward_surf.get_width() + 25 < details_rect.width:
            display_surface.blit(self.reward_icon, (details_rect.x + 10 + reward_surf.get_width() + 5, reward_y))
        
        # NPC assigned info - only if space permits
        if details_rect.width > 250:
            npc_text = f"From: {mission.npc_assigned}"
            npc_surf = self.small_font.render(npc_text, True, (180, 180, 220))
            npc_x = max(details_rect.x + 10, details_rect.right - npc_surf.get_width() - 10)
            display_surface.blit(npc_surf, (npc_x, reward_y - 50))

    def _wrap_text(self, text, font, max_width):
        """Split text into lines that fit within max_width"""
        if not text:
            return ["No description"]
            
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Try adding a new word to the current line
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                # Start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # If a single word is too long, truncate it
                    truncated = word
                    while font.size(truncated + '...')[0] > max_width and len(truncated) > 3:
                        truncated = truncated[:-1]
                    lines.append(truncated + '...')
                    current_line = []
                
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines if lines else ["No description"]

