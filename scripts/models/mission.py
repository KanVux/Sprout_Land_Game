from scripts.db.item_db import ItemDatabase
from scripts.db.mission_db import MissionDatabase
from datetime import date, datetime, timedelta

class Mission:
    def __init__(self, mission_id, name, description, mission_type, npc_assigned, reward_item, reward_quantity, required_progress):
        self.mission_id = mission_id
        self.name = name
        self.description = description
        self.type = mission_type  # 'one_time', 'daily', 'weekly', 'story', hoặc 'chained'
        self.npc_assigned = npc_assigned
        self.reward_item = reward_item
        self.reward_quantity = reward_quantity
        self.required_progress = required_progress
        
        # Trạng thái nhiệm vụ
        self.status = 'active'  # 'active', 'completed', 'failed', 'locked'
        self.progress = 0
        self.date_assigned = None
        self.date_completed = None
        self.prerequisite_missions = []  # Danh sách id các nhiệm vụ cần hoàn thành trước

        # Thêm các thuộc tính chi tiết hơn cho nhiệm vụ
        self.action_type = None  # Loại hành động cần thực hiện
        self.action_target = None  # Đối tượng của hành động
        self.action_location = None  # Địa điểm cần thực hiện (nếu có)
        self.reward_claimed = False  # Đánh dấu đã nhận phần thưởng
        self.reward_type = 'item'  # Loại phần thưởng: 'item', 'coins', 'xp'
        
        # Phân tích mô tả để lấy thông tin
        self._parse_description()

    def _parse_description(self):
        """Phân tích mô tả nhiệm vụ để xác định yêu cầu"""
        desc = self.description.lower()
        
        # Xác định loại hành động
        action_types = {
            'collect': ['collect', 'gather', 'find', 'pick up'],
            'plant': ['plant', 'grow', 'sow'],
            'harvest': ['harvest', 'reap', 'pick'],
            'talk': ['talk to', 'speak with', 'chat with'],
            'sell': ['sell', 'trade'],
            'buy': ['buy', 'purchase'],
            'craft': ['craft', 'make', 'create'],
            'chop': ['chop', 'cut down'],
            'water': ['water', 'irrigate'],
            'dig': ['dig', 'hoe', 'till']
        }
        
        for action, keywords in action_types.items():
            for keyword in keywords:
                if keyword in desc:
                    self.action_type = action
                    break
            if self.action_type:
                break
                
        # Tìm đối tượng hành động bằng cách tìm sau từ khóa
        if self.action_type:
            import re
            for keyword in action_types[self.action_type]:
                match = re.search(f"{keyword}\\s+([0-9]+)\\s+([a-z]+)", desc)
                if match:
                    self.action_target = match.group(2)
                    break

    def update_progress(self, amount):
        if self.status != 'active':
            return False
        
        old_progress = self.progress
        self.progress += amount
        
        # Kiểm tra nếu nhiệm vụ đã hoàn thành
        if self.progress >= self.required_progress:
            self.complete()
            # Trả về True và thông báo hoàn thành 
            return True, "completed"
        
        # Trả về True nếu có sự thay đổi tiến độ
        return old_progress != self.progress, "updated"
            
    def complete(self):
        self.status = 'completed'
        self.date_completed = datetime.now()
        # Đạt đến 100% tiến độ
        self.progress = self.required_progress
        return True
        
    def get_progress_percentage(self):
        """Lấy phần trăm tiến độ hoàn thành nhiệm vụ"""
        if self.required_progress <= 0:
            return 100 if self.status == 'completed' else 0
        return min(100, int((self.progress / self.required_progress) * 100))

class DailyMission(Mission):
    def check_reset(self):
        """Kiểm tra xem có cần reset nhiệm vụ hàng ngày không"""
        if not self.date_assigned:
            return False
            
        today = date.today()
        # Nếu ngày giao nhiệm vụ không phải ngày hôm nay, reset
        if self.date_assigned.date() < today:
            self.reset()
            return True
        return False
            
    def reset(self):
        """Reset nhiệm vụ hàng ngày"""
        self.status = 'active'
        self.progress = 0
        self.date_assigned = datetime.now()
        self.date_completed = None

class WeeklyMission(Mission):
    def check_reset(self):
        """Kiểm tra xem có cần reset nhiệm vụ hàng tuần không"""
        if not self.date_assigned:
            return False
            
        today = date.today()
        # Nếu ngày giao nhiệm vụ + 7 ngày < hôm nay, reset
        if self.date_assigned.date() + timedelta(days=7) <= today:
            self.reset()
            return True
        return False
            
    def reset(self):
        """Reset nhiệm vụ hàng tuần"""
        self.status = 'active'
        self.progress = 0
        self.date_assigned = datetime.now()
        self.date_completed = None

class StoryMission(Mission):
    """Nhiệm vụ cốt truyện - mở khóa theo tiến độ game"""
    def __init__(self, mission_id, name, description, mission_type, npc_assigned, reward_item, reward_quantity, required_progress, story_stage=0):
        super().__init__(mission_id, name, description, mission_type, npc_assigned, reward_item, reward_quantity, required_progress)
        self.story_stage = story_stage  # Giai đoạn cốt truyện

class ChainedMission(Mission):
    """Nhiệm vụ liên hoàn - phần tiếp theo của nhiệm vụ khác"""
    def __init__(self, mission_id, name, description, mission_type, npc_assigned, reward_item, reward_quantity, required_progress, previous_mission_id=None, next_mission_id=None):
        super().__init__(mission_id, name, description, mission_type, npc_assigned, reward_item, reward_quantity, required_progress)
        self.previous_mission_id = previous_mission_id  # ID nhiệm vụ trước đó trong chuỗi
        self.next_mission_id = next_mission_id  # ID nhiệm vụ tiếp theo trong chuỗi

class MissionManager:
    def __init__(self, player_id, player):
        self.player_id = player_id
        self.player = player  # Lưu tham chiếu đến player
        self.missions = {}  # mission_id -> Mission instance
        self.last_check_time = None  # Thời điểm cuối cùng kiểm tra reset
        self.active_notification = None  # Thông báo nhiệm vụ đang hiển thị
        self.completed_missions = []  # Danh sách nhiệm vụ hoàn thành chưa nhận thưởng
        
    def load_player_missions(self):
        """Load nhiệm vụ từ database cho người chơi."""
        data = MissionDatabase.get_player_missions(self.player_id)
        for row in data:
            mission = self._create_mission_from_data(row)
            self.missions[mission.mission_id] = mission
            
        # Kiểm tra để mở khóa các nhiệm vụ có điều kiện tiên quyết đã đáp ứng
        self._check_mission_prerequisites()
        
        # Sau khi load, kiểm tra reset nhiệm vụ hàng ngày/tuần
        self.check_periodic_missions()
            
    def _create_mission_from_data(self, row):
        """Tạo đối tượng Mission từ dữ liệu database."""
        if row['type'] == 'daily':
            mission = DailyMission(
                row['mission_id'], row['name'], row['description'], row['type'],
                row['npc_assigned'], row['reward_item'], row['reward_quantity'],
                row['required_progress']
            )
        elif row['type'] == 'weekly':
            mission = WeeklyMission(
                row['mission_id'], row['name'], row['description'], row['type'],
                row['npc_assigned'], row['reward_item'], row['reward_quantity'],
                row['required_progress']
            )
        elif row['type'] == 'story':
            mission = StoryMission(
                row['mission_id'], row['name'], row['description'], row['type'],
                row['npc_assigned'], row['reward_item'], row['reward_quantity'],
                row['required_progress'], 
                row.get('story_stage', 0)
            )
        elif row['type'] == 'chained':
            mission = ChainedMission(
                row['mission_id'], row['name'], row['description'], row['type'],
                row['npc_assigned'], row['reward_item'], row['reward_quantity'],
                row['required_progress'],
                row.get('previous_mission_id'),
                row.get('next_mission_id')
            )
        else:  # one_time và các loại khác
            mission = Mission(
                row['mission_id'], row['name'], row['description'], row['type'],
                row['npc_assigned'], row['reward_item'], row['reward_quantity'],
                row['required_progress']
            )
            
        # Cập nhật trạng thái nếu có dữ liệu từ player_missions
        if 'status' in row:
            mission.status = row['status']
        if 'progress' in row:
            mission.progress = row['progress']
        
        # Cập nhật ngày tháng nếu có
        if 'date_assigned' in row and row['date_assigned']:
            mission.date_assigned = row['date_assigned']
        if 'date_completed' in row and row['date_completed']:
            mission.date_completed = row['date_completed']
            
        # Các thuộc tính phụ thuộc loại nhiệm vụ
        if 'prerequisite_missions' in row and row['prerequisite_missions']:
            try:
                mission.prerequisite_missions = [int(x) for x in row['prerequisite_missions'].split(',')]
            except:
                mission.prerequisite_missions = []
                
        if 'reward_claimed' in row:
            mission.reward_claimed = row['reward_claimed']
        if 'reward_type' in row:
            mission.reward_type = row['reward_type']
                
        return mission

    def save_player_missions(self):
        """Lưu trạng thái nhiệm vụ của người chơi vào database."""
        for mission in self.missions.values():
            mission_data = {
                'mission_id': mission.mission_id,
                'status': mission.status,
                'progress': mission.progress,
                'date_assigned': mission.date_assigned or date.today(),
                'date_completed': mission.date_completed,
                'reward_claimed': mission.reward_claimed
            }
            MissionDatabase.save_player_mission(self.player_id, mission_data)

    def update_mission_progress(self, mission_id, amount):
        """Cập nhật tiến độ của một nhiệm vụ cụ thể."""
        if mission_id in self.missions:
            updated = self.missions[mission_id].update_progress(amount)
            if updated:
                self.save_player_missions()
                if self.missions[mission_id].status == 'completed':
                    self._check_mission_prerequisites()  # Kiểm tra mở khóa nhiệm vụ mới
                    return True  # Đã hoàn thành nhiệm vụ
            return updated
        return False

    def update_missions_by_action(self, action_type, target=None, amount=1, location=None):
        """
        Cập nhật tất cả nhiệm vụ dựa trên hành động người chơi.
        """
        updated_missions = []
        
        for mission_id, mission in self.missions.items():
            # Chỉ xem xét nhiệm vụ đang active
            if mission.status != 'active':
                continue
                
            # Phân tích mô tả nhiệm vụ để lấy yêu cầu
            requirements = self.extract_mission_requirements(mission_id)
            
            # Kiểm tra loại hành động
            mission_desc = mission.description.lower()
            action_keywords = {
                'collect': ['collect', 'gather', 'find', 'pick up'],
                'plant': ['plant', 'grow', 'sow'],
                'harvest': ['harvest', 'reap', 'pick'],
                'talk': ['talk to', 'speak with', 'chat with', 'meet'],
                'sell': ['sell', 'trade', 'exchange'],
                'buy': ['buy', 'purchase', 'acquire'],
                'craft': ['craft', 'make', 'create', 'build'],
                'upgrade': ['upgrade', 'improve', 'enhance'],
                'visit': ['visit', 'go to', 'travel to'],
                'water': ['water', 'irrigate'],
                'dig': ['dig', 'hoe', 'till'],
                'fish': ['fish', 'catch fish'],
                'feed': ['feed', 'give food to'],
                'cook': ['cook', 'prepare', 'bake'],
                'chop': ['chop', 'cut down', 'cut'],
                'interact': ['interact with', 'use', 'activate']
            }
            
            # Kiểm tra hành động phù hợp với từ khóa trong mô tả
            action_match = False
            if action_type in action_keywords:
                for keyword in action_keywords[action_type]:
                    if keyword in mission_desc:
                        action_match = True
                        break
            
            if not action_match:
                continue
            
            # THAY ĐỔI: Kiểm tra mục tiêu chung trước
            generic_targets = {
                'collect': ['item', 'items', 'thing', 'things', 'object', 'objects'],
                'plant': ['seed', 'seeds', 'crop', 'crops', 'plant', 'plants'],
                'harvest': ['crop', 'crops', 'plant', 'plants', 'vegetable', 'vegetables', 'fruit', 'fruits'],
                'chop': ['tree', 'trees', 'wood', 'woods'],
                'sell': ['item', 'items', 'thing', 'things', 'product', 'products']
            }
            
            # Kiểm tra xem nhiệm vụ có phải là mục tiêu chung
            is_generic_mission = False
            if requirements:
                req_item = requirements.get('item', '').lower()
                if action_type in generic_targets and req_item in generic_targets[action_type]:
                    is_generic_mission = True
            
            # Nếu là nhiệm vụ chung, bất kỳ mục tiêu nào phù hợp với action đều được chấp nhận
            if is_generic_mission:
                print(f"DEBUG: Generic mission detected! Updating mission {mission_id}: {mission.name}")
                result, status = mission.update_progress(amount)
                if result:
                    updated_missions.append(mission_id)
                    # Nếu nhiệm vụ vừa hoàn thành, tự động nhận thưởng
                    if status == "completed" and hasattr(self, 'player'):
                        success, message = self.claim_mission_reward(mission_id, self.player)
                        print(f"Mission {mission_id} completed! {message}")
                continue
                
            # Nếu không phải nhiệm vụ chung, kiểm tra mục tiêu cụ thể
            if target and requirements and requirements.get('item'):
                target_str = str(target).lower()
                req_item = requirements['item'].lower()
                
                # Xử lý tốt hơn với item nhiều từ
                target_words = target_str.split()
                req_words = req_item.split()
                
                # Trường hợp 1: Target chính xác bằng với requirement
                exact_match = (target_str == req_item)
                
                # Trường hợp 2: Target có chứa req_item
                # "carrot seeds" khớp với "carrot"
                contains_match = False
                if len(target_words) > 1 and len(req_words) == 1:
                    contains_match = req_words[0] in target_words
                
                # Trường hợp 3: Req_item có chứa target
                # "carrot" khớp với "carrot seeds"
                reverse_contains = False
                if len(req_words) > 1 and len(target_words) == 1:
                    reverse_contains = target_words[0] in req_words
                
                # Trường hợp 4: Loại bỏ 'seeds' từ cả hai và so sánh lại
                base_target = target_str.replace(" seeds", "")
                base_req = req_item.replace(" seeds", "")
                base_match = (base_target == base_req)
                
                # Trường hợp 5: Xử lý số ít vs số nhiều (carrot vs carrots)
                singular_plural_match = False
                # Nếu target là số ít và requirement là số nhiều (carrot vs carrots)
                if target_str + 's' == req_item:
                    singular_plural_match = True
                # Nếu target là số nhiều và requirement là số ít (carrots vs carrot)
                elif target_str.endswith('s') and target_str[:-1] == req_item:
                    singular_plural_match = True
                # Nếu base forms sau khi loại bỏ 's' giống nhau
                elif base_target.rstrip('s') == base_req.rstrip('s'):
                    singular_plural_match = True
                
                # Target chính xác khớp với yêu cầu làm nhiệm vụ
                target_match = exact_match or contains_match or reverse_contains or base_match or singular_plural_match
                
                if target_match:
                    print(f"DEBUG: Match detected! Target: {target_str}, Req: {req_item}, Match type: {"singular/plural" if singular_plural_match else "other"}")
                    result, status = mission.update_progress(amount)
                    if result:
                        updated_missions.append(mission_id)
                        # Nếu nhiệm vụ vừa hoàn thành, tự động nhận thưởng
                        if status == "completed" and hasattr(self, 'player'):
                            success, message = self.claim_mission_reward(mission_id, self.player)
                            print(f"Mission {mission_id} completed! {message}")
            # Trường hợp không có target hoặc không có requirement item
            elif not target and (not requirements or not requirements.get('item')):
                # Nhiệm vụ không yêu cầu target cụ thể (ví dụ: "dig 5 tiles")
                print(f"DEBUG: No target required! Updating mission {mission_id}: {mission.name}")
                result, status = mission.update_progress(amount)
                if result:
                    updated_missions.append(mission_id)
                    # Nếu nhiệm vụ vừa hoàn thành, tự động nhận thưởng
                    if status == "completed" and hasattr(self, 'player'):
                        success, message = self.claim_mission_reward(mission_id, self.player)
                        print(f"Mission {mission_id} completed! {message}")
        
        # Lưu lại nếu có bất kỳ thay đổi nào
        if updated_missions:
            self.save_player_missions()
            self._check_mission_prerequisites()
            
        return updated_missions

    def _check_mission_prerequisites(self):
        """Kiểm tra và mở khóa các nhiệm vụ nếu điều kiện tiên quyết đã được đáp ứng."""
        all_missions = MissionDatabase.get_all_missions()
        completed_mission_ids = [
            mission.mission_id for mission in self.missions.values() 
            if mission.status == 'completed'
        ]
        
        # Lấy tất cả nhiệm vụ chưa gán cho người chơi
        for mission_data in all_missions:
            if mission_data['mission_id'] not in self.missions:
                # Kiểm tra prerequisites
                prerequisites_met = True
                
                # Nếu có prerequisite_missions và không phải là chuỗi rỗng
                if 'prerequisite_missions' in mission_data and mission_data['prerequisite_missions']:
                    try:
                        prereq_ids = [int(x) for x in mission_data['prerequisite_missions'].split(',')]
                        # Kiểm tra xem tất cả các nhiệm vụ tiên quyết đã hoàn thành chưa
                        for prereq_id in prereq_ids:
                            if prereq_id not in completed_mission_ids:
                                prerequisites_met = False
                                break
                    except:
                        pass  # Bỏ qua lỗi định dạng
                        
                # Nếu đáp ứng điều kiện, gán nhiệm vụ mới
                if prerequisites_met:
                    mission = self._create_mission_from_data(mission_data)
                    self.assign_new_mission(mission)

    def assign_new_mission(self, mission):
        """Gán một nhiệm vụ mới cho người chơi."""
        if mission.mission_id not in self.missions:
            mission.date_assigned = datetime.now()
            self.missions[mission.mission_id] = mission
            
            mission_data = {
                'mission_id': mission.mission_id,
                'status': mission.status,
                'progress': mission.progress,
                'date_assigned': mission.date_assigned,
                'date_completed': mission.date_completed,
                'reward_claimed': mission.reward_claimed
            }
            MissionDatabase.save_player_mission(self.player_id, mission_data)
            return True
        return False

    def check_periodic_missions(self):
        """Kiểm tra và reset các nhiệm vụ hàng ngày/tuần nếu cần."""
        now = datetime.now()
        
        # Kiểm tra xem chúng ta đã kiểm tra gần đây chưa để tránh kiểm tra quá thường xuyên
        if self.last_check_time and (now - self.last_check_time).total_seconds() < 300:  # 5 phút
            return
            
        self.last_check_time = now
        missions_to_save = []
        
        for mission in self.missions.values():
            if isinstance(mission, DailyMission) and mission.check_reset():
                missions_to_save.append(mission)
            elif isinstance(mission, WeeklyMission) and mission.check_reset():
                missions_to_save.append(mission)
                
        if missions_to_save:
            self.save_player_missions()

    def get_completed_missions(self):
        """Lấy danh sách các nhiệm vụ đã hoàn thành."""
        return [mission for mission in self.missions.values() if mission.status == 'completed']
        
    def get_active_missions(self):
        """Lấy danh sách các nhiệm vụ đang active."""
        return [mission for mission in self.missions.values() if mission.status == 'active']
        
    def claim_mission_reward(self, mission_id, player):
        """Cấp phần thưởng cho nhiệm vụ đã hoàn thành"""
        if mission_id not in self.missions:
            return False, "Nhiệm vụ không tồn tại"
            
        mission = self.missions[mission_id]
        if mission.status != 'completed':
            return False, "Nhiệm vụ chưa hoàn thành"
            
        if mission.reward_claimed:
            return False, "Phần thưởng đã được nhận"
        
        # Cấp phần thưởng: tiền, vật phẩm hoặc điểm kinh nghiệm
        if mission.reward_type == 'coins':
            # Lấy item coins từ database
            coin_item = ItemDatabase.get_item_from_name('coins')
            player.add_item(coin_item, mission.reward_quantity)
            print(f"Nhận {mission.reward_quantity} coins từ nhiệm vụ {mission.name}")
        elif mission.reward_type == 'item':
            # Thêm vật phẩm vào inventory
            item = ItemDatabase.get_item_from_name(mission.reward_item)
            self.player.add_item(item, mission.reward_quantity)
            print(f"Nhận {mission.reward_quantity} {mission.reward_item} từ nhiệm vụ {mission.name}")
        elif mission.reward_type == 'xp':
            # Cấp điểm kinh nghiệm (nếu có hệ thống XP)
            if hasattr(player, 'add_xp'):
                player.add_xp(mission.reward_quantity)
            print(f"Nhận {mission.reward_quantity} XP từ nhiệm vụ {mission.name}")
        
        # Đánh dấu đã nhận phần thưởng
        mission.reward_claimed = True
        
        # Cập nhật trạng thái nhiệm vụ trong cơ sở dữ liệu
        mission_data = {
            'mission_id': mission.mission_id,
            'status': mission.status,
            'progress': mission.progress,
            'date_assigned': mission.date_assigned,
            'date_completed': mission.date_completed,
            'reward_claimed': True
        }
        MissionDatabase.save_player_mission(self.player_id, mission_data)
        
        return True, f"Đã nhận {mission.reward_quantity} {mission.reward_type}"

    def extract_mission_requirements(self, mission_id):
        """Trích xuất yêu cầu từ mô tả nhiệm vụ"""
        if mission_id not in self.missions:
            return None
            
        mission = self.missions[mission_id]
        desc = mission.description.lower()
        
        # Tìm hành động
        action_keywords = {
            'collect': ['collect', 'gather', 'find', 'pick up'],
            'plant': ['plant', 'grow', 'sow'],
            'harvest': ['harvest', 'reap', 'pick'],
            'talk': ['talk to', 'speak with', 'chat with', 'meet'],
            'sell': ['sell', 'trade', 'exchange'],
            'buy': ['buy', 'purchase', 'acquire'],
            'craft': ['craft', 'make', 'create', 'build'],
            'upgrade': ['upgrade', 'improve', 'enhance'],
            'visit': ['visit', 'go to', 'travel to'],
            'water': ['water', 'irrigate'],
            'dig': ['dig', 'hoe', 'till'],
            'fish': ['fish', 'catch fish'],
            'feed': ['feed', 'give food to'],
            'cook': ['cook', 'prepare', 'bake'],
            'chop': ['chop', 'cut down', 'cut'],
            'interact': ['interact with', 'use', 'activate']
        }
        
        action = None
        for act, keywords in action_keywords.items():
            for keyword in keywords:
                if keyword in desc:
                    action = act
                    break
            if action:
                break
        
        # Tìm số lượng và item
        import re
        
        # Danh sách các từ chỉ loại chung
        generic_terms = ['item', 'items', 'crop', 'crops', 'plant', 'plants', 
                        'vegetable', 'vegetables', 'fruit', 'fruits', 
                        'tree', 'trees', 'wood', 'woods', 'seed', 'seeds',
                        'thing', 'things', 'product', 'products', 'object', 'objects']
        
        # Danh sách cụm từ chỉ loại chung
        generic_phrases = [
            'items of any kind', 'any item', 'any items',
            'any crop', 'any crops', 'any plant', 'any plants',
            'any seed', 'any seeds', 'any product', 'any products',
            'anything', 'any kind of item', 'any kind of items'
        ]
        
        # Pattern 1: Số lượng + Item (ví dụ: "5 carrot seeds")
        match = re.search(r'(\d+)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)', desc)
        if match:
            quantity = int(match.group(1))
            full_item_phrase = match.group(2).strip()
            
            # THAY ĐỔI: Chỉ lấy từ đầu tiên làm item 
            # hoặc lấy từ sau "any" nếu có cấu trúc "any X"
            item_words = full_item_phrase.split()
            
            # Xử lý các trường hợp đặc biệt
            if "of any kind" in full_item_phrase:
                # Với "crops of any kind", chỉ lấy "crops"
                item_phrase = item_words[0]
                is_generic = True
            elif "any" in item_words and len(item_words) > 1:
                # Với "any crops", lấy từ sau "any"
                any_index = item_words.index("any")
                if any_index + 1 < len(item_words):
                    item_phrase = item_words[any_index + 1]
                    is_generic = True
                else:
                    item_phrase = item_words[0]
                    is_generic = False
            elif len(item_words) == 1:
                # Với từ đơn lẻ như "carrots"
                item_phrase = item_words[0]
                is_generic = item_phrase in generic_terms
            elif "seeds" in item_words[-1]:
                # Trường hợp "carrot seeds"
                item_phrase = " ".join(item_words[-2:]) if len(item_words) >= 2 else item_words[0]
                is_generic = False
            else:
                # Lấy từ đầu tiên làm mặc định
                item_phrase = item_words[0]
                is_generic = item_phrase in generic_terms
            
            # Kiểm tra từng từ đơn
            if not is_generic:
                if item_phrase in generic_terms:
                    is_generic = True
            
            # Chuẩn hóa item: loại bỏ 's' ở cuối nếu có
            if item_phrase.endswith('s') and not item_phrase.endswith('seeds'):
                item_phrase = item_phrase[:-1]  # chuyển 'carrots' -> 'carrot'

            return {
                'action': action,
                'quantity': quantity,
                'item': item_phrase,
                'original_desc': desc,
                'is_generic': is_generic
            }
        
        # Pattern 2: Item + Số lượng (ít phổ biến hơn)
        # Xử lý tương tự...
        match = re.search(r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d+)', desc)
        if match:
            full_item_phrase = match.group(1).strip()
            quantity = int(match.group(2))
            
            # Xử lý tương tự như trên
            item_words = full_item_phrase.split()
            
            # Xử lý các trường hợp đặc biệt tương tự như trên
            if "of any kind" in full_item_phrase:
                item_phrase = item_words[0]
                is_generic = True
            elif "any" in item_words and len(item_words) > 1:
                any_index = item_words.index("any")
                if any_index + 1 < len(item_words):
                    item_phrase = item_words[any_index + 1]
                    is_generic = True
                else:
                    item_phrase = item_words[0]
                    is_generic = False
            elif len(item_words) == 1:
                item_phrase = item_words[0]
                is_generic = item_phrase in generic_terms
            elif "seeds" in item_words[-1]:
                item_phrase = " ".join(item_words[-2:]) if len(item_words) >= 2 else item_words[0]
                is_generic = False
            else:
                item_phrase = item_words[0]
                is_generic = item_phrase in generic_terms
            
            # Kiểm tra từng từ đơn
            if not is_generic:
                if item_phrase in generic_terms:
                    is_generic = True
            
            # Chuẩn hóa item: loại bỏ 's' ở cuối nếu có
            if item_phrase.endswith('s') and not item_phrase.endswith('seeds'):
                item_phrase = item_phrase[:-1]  # chuyển 'carrots' -> 'carrot'

            return {
                'action': action,
                'quantity': quantity,
                'item': item_phrase,
                'original_desc': desc,
                'is_generic': is_generic
            }
        
        return None

    def handle_mission_complete(self, mission_id):
        """Xử lý khi một nhiệm vụ vừa hoàn thành"""
        if mission_id in self.missions and self.missions[mission_id].status == 'completed':
            # Lưu nhiệm vụ vào danh sách chờ nhận thưởng
            self.completed_missions.append(mission_id)
            return True
        return False

    def has_pending_rewards(self):
        """Kiểm tra xem có nhiệm vụ nào đã hoàn thành chưa nhận thưởng không"""
        for mission in self.missions.values():
            if mission.status == 'completed' and not mission.reward_claimed:
                return True
        return False

    def get_next_reward_mission(self):
        """Lấy nhiệm vụ tiếp theo trong hàng đợi nhận thưởng"""
        for mission in self.missions.values():
            if mission.status == 'completed' and not mission.reward_claimed:
                return mission
        return None

    def claim_next_reward(self):
        """Nhận thưởng cho nhiệm vụ tiếp theo trong hàng đợi"""
        if self.completed_missions and self.player:
            mission_id = self.completed_missions.pop(0)
            return self.claim_mission_reward(mission_id, self.player)
        return False, "Không còn nhiệm vụ nào chờ nhận thưởng"

