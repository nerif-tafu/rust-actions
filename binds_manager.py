import json
import os
import stat
import time
import logging
from typing import List, Dict, Tuple, Optional
from itertools import combinations

# Set up logging
logger = logging.getLogger(__name__)

class BindsManager:
    def __init__(self, keys_cfg_path: str = r"c:\Program Files (x86)\Steam\steamapps\common\Rust\cfg\keys.cfg"):
        self.keys_cfg_path = keys_cfg_path
        # Use Documents/Rust-Actions folder for data storage
        documents_path = os.path.expanduser("~/Documents")
        self.data_dir = os.path.join(documents_path, "Rust-Actions")
        self.item_database_path = os.path.join(self.data_dir, "itemDatabase.json")
        
        # Ensure the data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Available keys for binds
        self.available_keys = [
            'keypaddivide', 'keypadmultiply', 'keypadminus', 'keypadplus', 'keypadperiod',
            'keypad1', 'keypad2', 'keypad3', 'keypad4', 'keypad5', 'keypad6', 'keypad7', 'keypad8', 'keypad9', 'keypad0',
            'f13', 'f14', 'f15',
            'slash', 'period', 'comma', 'leftbracket', 'rightbracket'
        ]
        
        # Reserved ranges
        self.CRAFTING_BINDS_START = 0
        self.CRAFTING_BINDS_END = 2999  # 3000 slots for crafting (1500 items * 2 for craft/cancel)
        self.API_BINDS_START = 3000
        self.API_BINDS_END = 3999  # 1000 slots for API commands
        self.CHAT_BINDS_START = 4000
        self.CHAT_BINDS_END = 4999  # 1000 slots for chat/connection commands
        
        # Load item database
        self.item_database = self._load_item_database()
        self.craftable_items = self._get_craftable_items()
        
        # Generate key combinations
        self.key_combinations = self._generate_key_combinations()
        
        # Track used binds
        self.used_binds = set()
        self.bind_mapping = {}  # Maps item_id -> (craft_bind_index, cancel_bind_index)
        
        # Dynamic chat/connection bind management
        self.dynamic_binds = {}  # Maps string -> bind_index
        self.next_dynamic_bind = self.CHAT_BINDS_START
        self.dynamic_bind_order = []  # Track order for FIFO replacement
        
        # Load dynamic binds from keys.cfg (with migration from JSON if needed)
        self._load_dynamic_binds_from_keys_cfg()
        
        # One-time migration from old JSON file to keys.cfg
        self._migrate_dynamic_binds_from_json()
        
        # Initialize bind mappings for crafting items
        self._initialize_bind_mappings()
        
        # File permission management
        self._file_permissions_backup = None
        
    def _load_item_database(self) -> Dict:
        """Load the item database from JSON file."""
        try:
            with open(self.item_database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"Warning: Item database not found at {self.item_database_path}")
            return {"items": {}}
        except json.JSONDecodeError as e:
            print(f"Error parsing item database: {e}")
            return {"items": {}}
        except Exception as e:
            print(f"Unexpected error loading item database: {e}")
            return {"items": {}}
    
    def _get_craftable_items(self) -> List[Dict]:
        """Extract all items from the database that have ingredients (craftable items)."""
        craftable_items = []
        for item_id, item_data in self.item_database.get("items", {}).items():
            # Check if item has ingredients (regardless of userCraftable status)
            if (item_data.get("ingredients") and 
                len(item_data.get("ingredients", [])) > 0):
                craftable_items.append({
                    "id": item_id,
                    "numericId": item_data.get("numericId", int(item_id)),
                    "name": item_data.get("name", "Unknown"),
                    "shortname": item_data.get("shortname", "unknown")
                })
                
        
        return craftable_items
    
    def _generate_key_combinations(self) -> List[str]:
        """Generate all possible 5-key combinations from available keys."""
        combinations_list = []
        for combo in combinations(self.available_keys, 5):
            combinations_list.append("+".join(combo))
        return combinations_list
    
    def _format_bind_command(self, key_combo: str, command: str) -> str:
        """Format a bind command for the keys.cfg file."""
        return f"bind [{key_combo}] {command}"
    
    def _initialize_bind_mappings(self):
        """Initialize bind mappings for crafting items without generating the full keys.cfg."""
        print(f"Initializing bind mappings for {len(self.craftable_items)} craftable items...")
        
        for i, item in enumerate(self.craftable_items):
            if i * 2 >= len(self.key_combinations):
                print(f"Warning: Not enough key combinations for all items. Stopping at item {i}")
                break
                
            item_id = int(item["numericId"])
            item_name = item["name"]
            

            
            # Create bind mapping
            craft_bind_index = i * 2
            cancel_bind_index = i * 2 + 1
            
            # Track the mapping
            self.bind_mapping[item_id] = (craft_bind_index, cancel_bind_index)
            self.used_binds.add(craft_bind_index)
            self.used_binds.add(cancel_bind_index)
        
        print(f"Initialized {len(self.bind_mapping)} bind mappings")
    
    def generate_crafting_binds(self) -> List[str]:
        """Generate crafting binds for all craftable items."""
        binds = []
        item_count = len(self.craftable_items)
        
        print(f"Generating crafting binds for {item_count} craftable items...")
        
        for i, item in enumerate(self.craftable_items):
            if i * 2 >= len(self.key_combinations):
                print(f"Warning: Not enough key combinations for all items. Stopping at item {i}")
                break
                
            item_id = int(item["numericId"])
            item_name = item["name"]
            

            
            # Craft bind
            craft_bind_index = i * 2
            craft_key_combo = self.key_combinations[craft_bind_index]
            craft_command = f"craft.add {item_id} 1"
            craft_bind = self._format_bind_command(craft_key_combo, craft_command)
            
            # Cancel bind
            cancel_bind_index = i * 2 + 1
            cancel_key_combo = self.key_combinations[cancel_bind_index]
            cancel_command = f"craft.cancel {item_id} 1"
            cancel_bind = self._format_bind_command(cancel_key_combo, cancel_command)
            
            # Add combined comment with bind numbers
            binds.append(f"# Craft/Cancel {item_name} (ID: {item_id}) - reserved bind no.{craft_bind_index}/{cancel_bind_index}")
            binds.append(craft_bind)
            binds.append(cancel_bind)
            
            # Track the mapping
            self.bind_mapping[item_id] = (craft_bind_index, cancel_bind_index)
            self.used_binds.add(craft_bind_index)
            self.used_binds.add(cancel_bind_index)
            
            # Add empty line for readability
            binds.append("")
        
        # Fill remaining crafting slots with empty binds
        crafting_slots_used = len(self.craftable_items) * 2
        crafting_slots_total = self.CRAFTING_BINDS_END - self.CRAFTING_BINDS_START + 1
        
        if crafting_slots_used < crafting_slots_total:
            binds.append(f"# Empty reserved binds for future crafting items")
            for bind_index in range(self.CRAFTING_BINDS_START + crafting_slots_used, self.CRAFTING_BINDS_END + 1):
                if bind_index < len(self.key_combinations):
                    key_combo = self.key_combinations[bind_index]
                    empty_bind = self._format_bind_command(key_combo, '""')
                    binds.append(f"# Reserved bind no.{bind_index}")
                    binds.append(empty_bind)
                    self.used_binds.add(bind_index)
            binds.append("")
        
        print(f"Generated {len(binds)} bind lines for {item_count} items + empty reserves")
        return binds
    
    def generate_api_binds(self) -> List[str]:
        """Generate binds for API commands."""
        binds = []
        api_commands = [
            ("kill", "kill"),
            ("respawn", "respawn"),
            ("autorun", "forward;sprint;chat.add 0 0 \"Auto run enabled!\""),
            ("autorun_jump", "forward;sprint;jump;chat.add 0 0 \"Auto run and jump enabled!\""),
            ("crouch_attack", "attack;duck;chat.add 0 0 \"Auto crouch and attack enabled!\""),
            ("quit_game", "quit"),
            ("disconnect", "disconnect"),
            ("lookat_radius_20", "client.lookatradius 20;chat.add 0 0 \"Look radius set to wide (20)\""),
            ("lookat_radius_0", "client.lookatradius 0.0002;chat.add 0 0 \"Look radius set to narrow (0.0002)\""),
            ("audio_voices_0", "audio.voices 0;chat.add 0 0 \"Voice volume set to 0%\""),
            ("audio_voices_25", "audio.voices 0.25;chat.add 0 0 \"Voice volume set to 25%\""),
            ("audio_voices_50", "audio.voices 0.5;chat.add 0 0 \"Voice volume set to 50%\""),
            ("audio_voices_75", "audio.voices 0.75;chat.add 0 0 \"Voice volume set to 75%\""),
            ("audio_voices_100", "audio.voices 1;chat.add 0 0 \"Voice volume set to 100%\""),
            ("audio_master_0", "audio.master 0;chat.add 0 0 \"Master volume set to 0%\""),
            ("audio_master_25", "audio.master 0.25;chat.add 0 0 \"Master volume set to 25%\""),
            ("audio_master_50", "audio.master 0.5;chat.add 0 0 \"Master volume set to 50%\""),
            ("audio_master_75", "audio.master 0.75;chat.add 0 0 \"Master volume set to 75%\""),
            ("audio_master_100", "audio.master 1;chat.add 0 0 \"Master volume set to 100%\""),
            ("hud_off", "graphics.hud 0"),
            ("hud_on", "graphics.hud 1"),
            ("gesture_wave", "gesture wave"),
            ("gesture_victory", "gesture victory"),
            ("gesture_shrug", "gesture shrug"),
            ("gesture_thumbsup", "gesture thumbsup"),
            ("gesture_hurry", "gesture hurry"),
            ("gesture_ok", "gesture ok"),
            ("gesture_thumbsdown", "gesture thumbsdown"),
            ("gesture_clap", "gesture clap"),
            ("gesture_point", "gesture point"),
            ("gesture_friendly", "gesture friendly"),
            ("gesture_cabbagepatch", "gesture cabbagepatch"),
            ("gesture_twist", "gesture twist"),
            ("gesture_raisetheroof", "gesture raisetheroof"),
            ("gesture_beatchest", "gesture beatchest"),
            ("gesture_throatcut", "gesture throatcut"),
            ("gesture_fingergun", "gesture fingergun"),
            ("gesture_shush", "gesture shush"),
            ("gesture_shush_vocal", "gesture shush_vocal"),
            ("gesture_watchingyou", "gesture watchingyou"),
            ("gesture_loser", "gesture loser"),
            ("gesture_nono", "gesture nono"),
            ("gesture_knucklescrack", "gesture knucklescrack"),
            ("gesture_rps", "gesture rps"),
            ("noclip_true", "noclip true;chat.add 0 0 \"Noclip enabled!\""),
            ("noclip_false", "noclip false;chat.add 0 0 \"Noclip disabled!\""),
            ("global_god_true", "global.god true;chat.add 0 0 \"God mode enabled!\""),
            ("global_god_false", "global.god false;chat.add 0 0 \"God mode disabled!\""),
            ("env_time_0", "env.time 0;chat.add 0 0 \"Time set to 00:00 (midnight)\""),
            ("env_time_4", "env.time 4;chat.add 0 0 \"Time set to 04:00 (early morning)\""),
            ("env_time_8", "env.time 8;chat.add 0 0 \"Time set to 08:00 (morning)\""),
            ("env_time_12", "env.time 12;chat.add 0 0 \"Time set to 12:00 (noon)\""),
            ("env_time_16", "env.time 16;chat.add 0 0 \"Time set to 16:00 (afternoon)\""),
            ("env_time_20", "env.time 20;chat.add 0 0 \"Time set to 20:00 (evening)\""),
            ("env_time_24", "env.time 24;chat.add 0 0 \"Time set to 24:00 (midnight)\""),
            ("teleport2marker", "teleport2marker;chat.add 0 0 \"Teleported to marker!\""),
            ("combatlog", "combatlog"),
            ("console_clear", "console.clear"),
            ("consoletoggle", "consoletoggle"),
            ("chat_continuous_stack_enabled", "chat.add 0 0 \"Continuous stack inventory enabled!\""),
            ("chat_continuous_stack_disabled", "chat.add 0 0 \"Continuous stack inventory disabled!\""),
            ("chat_anti_afk_started", "chat.add 0 0 \"Anti-AFK started!\""),
            ("chat_anti_afk_stopped", "chat.add 0 0 \"Anti-AFK stopped!\""),
            ("cancel_all_crafting", "craft.cancelall;chat.add 0 0 \"All crafting cancelled!\""),
            ("ent_kill", "ent kill;chat.add 0 0 \"Entity killed!\""),
        ]
        
        print(f"Generating API binds...")
        
        for i, (name, command) in enumerate(api_commands):
            bind_index = self.API_BINDS_START + i
            if bind_index >= len(self.key_combinations):
                print(f"Warning: Not enough key combinations for API binds. Stopping at {name}")
                break
                
            key_combo = self.key_combinations[bind_index]
            bind = self._format_bind_command(key_combo, command)
            binds.append(f"# API: {name} - reserved bind no.{bind_index}")
            binds.append(bind)
            binds.append("")
            
            self.used_binds.add(bind_index)
        
        # Fill remaining API slots with empty binds
        api_slots_used = len(api_commands)
        api_slots_total = self.API_BINDS_END - self.API_BINDS_START + 1
        
        if api_slots_used < api_slots_total:
            binds.append(f"# Empty reserved binds for future API commands")
            for bind_index in range(self.API_BINDS_START + api_slots_used, self.API_BINDS_END + 1):
                if bind_index < len(self.key_combinations):
                    key_combo = self.key_combinations[bind_index]
                    empty_bind = self._format_bind_command(key_combo, '""')
                    binds.append(f"# Reserved bind no.{bind_index}")
                    binds.append(empty_bind)
                    self.used_binds.add(bind_index)
            binds.append("")
        
        return binds
    
    def generate_chat_binds(self) -> List[str]:
        """Generate empty reserved binds for chat and connection commands."""
        binds = []
        print(f"Generating empty reserved binds for chat/connection commands...")
        
        # Generate empty reserved binds for all chat/connection slots
        binds.append(f"# Empty reserved binds for dynamic chat/connection commands")
        for bind_index in range(self.CHAT_BINDS_START, self.CHAT_BINDS_END + 1):
            if bind_index < len(self.key_combinations):
                key_combo = self.key_combinations[bind_index]
                empty_bind = self._format_bind_command(key_combo, '""')
                binds.append(f"# Reserved bind no.{bind_index}")
                binds.append(empty_bind)
                self.used_binds.add(bind_index)
        binds.append("")
        
        return binds
    
    def read_existing_keys_cfg(self) -> Tuple[List[str], List[str], List[str]]:
        """Read existing keys.cfg and separate into sections."""
        user_binds = []
        rust_actions_binds = []
        other_binds = []
        
        if not os.path.exists(self.keys_cfg_path):
            print(f"Warning: keys.cfg not found at {self.keys_cfg_path}")
            return user_binds, rust_actions_binds, other_binds
        
        # Temporarily make file readable if it's read-only
        was_readonly = self.is_file_readonly()
        if was_readonly:
            logger.info("File is read-only, temporarily making it readable for reading...")
            if not self.set_file_writable():
                logger.error("Failed to make file writable for reading")
                return user_binds, rust_actions_binds, other_binds
        
        try:
            with open(self.keys_cfg_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_section = "other"
            for line in lines:
                line = line.rstrip('\n')
                
                if line.strip() == "#USER-SECTION-START":
                    current_section = "user"
                    continue
                elif line.strip() == "#USER-SECTION-END":
                    current_section = "other"
                    continue
                elif line.strip() == "#RUST-ACTIONS-START":
                    current_section = "rust_actions"
                    continue
                elif line.strip() == "#RUST-ACTIONS-END":
                    current_section = "other"
                    continue
                
                # Skip empty lines at the beginning of the file
                if current_section == "other" and not line.strip() and not other_binds:
                    continue
                
                if current_section == "user":
                    user_binds.append(line)
                elif current_section == "rust_actions":
                    rust_actions_binds.append(line)
                else:
                    other_binds.append(line)
            
            # If no section markers were found, treat all bind lines as user_binds (default Rust binds)
            if not any(line.strip() in ["#USER-SECTION-START", "#RUST-ACTIONS-START"] for line in lines):
                user_binds = [line.rstrip('\n') for line in lines if line.strip() and not line.strip().startswith('#')]
                other_binds = []
                rust_actions_binds = []
            else:
                # If we have sections, the user_binds should contain the default Rust binds
                # and other_binds should be empty (since we don't want duplication)
                if not other_binds:
                    other_binds = []
                
                # If user_binds is empty but we have section markers, it means the file
                # was corrupted or empty. In this case, we'll let the write method handle it.
            
            return user_binds, rust_actions_binds, other_binds
            
        except Exception as e:
            print(f"Error reading keys.cfg: {e}")
            return user_binds, rust_actions_binds, other_binds
        finally:
            # Restore read-only state if it was read-only before
            if was_readonly:
                logger.info("Restoring read-only state after reading...")
                self.set_file_readonly()
    
    def write_keys_cfg_with_sections(self) -> bool:
        """Write keys.cfg with proper sections."""
        try:
            logger.info("Starting write_keys_cfg_with_sections()...")
            
            # Read existing sections
            user_binds, _, other_binds = self.read_existing_keys_cfg()
            logger.info(f"Read existing sections: {len(user_binds)} user binds, {len(other_binds)} other binds")
            
            # If no existing file or no user_binds, create default Rust binds in user_binds
            if not user_binds:
                user_binds = [
                    "bind tab inventory.toggle",
                    "bind return chat.open",
                    "bind space +jump",
                    "bind 1 +slot1",
                    "bind 2 +slot2",
                    "bind 3 +slot3",
                    "bind 4 +slot4",
                    "bind 5 +slot5",
                    "bind 6 +slot6",
                    "bind 7 +holsteritem",
                    "bind a +left",
                    "bind b +gestures",
                    "bind c forward;sprint",
                    "bind d +right",
                    "bind e +nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+nextskin;+use",
                    "bind f +focusmap;lighttoggle",
                    "bind g +map",
                    "bind h +hoverloot",
                    "bind j +global.hudcomponent BinocularOverlay 1;global.hudcomponent BinocularOverlay 0",
                    "bind k exec keys.cfg",
                    "bind m +firemode",
                    "bind n inventory.examineheld",
                    "bind p +pets",
                    "bind q +prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+prevskin;+ping",
                    "bind r +reload",
                    "bind s +backward",
                    "bind t chat.open",
                    "bind v +voice",
                    "bind w +forward",
                    "bind x swapseats",
                    "bind y +opentutorialhelp",
                    "bind z attack;duck",
                    "bind keypad1 +notec",
                    "bind keypad2 +noted",
                    "bind keypad3 +notee",
                    "bind keypad4 +notef",
                    "bind keypad5 +noteg",
                    "bind keypad6 +notea",
                    "bind keypad7 +noteb",
                    "bind keypadplus +notesharpmod",
                    "bind keypadenter +noteoctaveupmod",
                    "bind pageup +zoomincrease",
                    "bind pagedown +zoomdecrease",
                    "bind f1 combatlog;consoletoggle",
                    "bind leftshift +sprint",
                    "bind leftcontrol +duck",
                    "bind leftalt +altlook;+meta.if_true \"headlerp 0\";+meta.if_false \"headlerp 100\"",
                    "bind mouse0 +attack",
                    "bind mouse1 +attack2",
                    "bind mouse2 +attack3",
                    "bind mouse3 inventory.togglecrafting",
                    "bind mouse4 ~graphics.fov 70;graphics.fov 80",
                    "bind mousewheelup +invprev",
                    "bind mousewheeldown +invnext",
                    "bind [leftcontrol+1] swaptoseat 0",
                    "bind [leftcontrol+2] swaptoseat 1",
                    "bind [leftcontrol+3] swaptoseat 2",
                    "bind [leftcontrol+4] swaptoseat 3",
                    "bind [leftcontrol+5] swaptoseat 4",
                    "bind [leftcontrol+6] swaptoseat 5",
                    "bind [leftcontrol+7] swaptoseat 6",
                    "bind [leftcontrol+8] swaptoseat 7",
                    "bind [leftshift+mousewheelup] +wireslackup",
                    "bind [leftshift+mousewheeldown] +wireslackdown"
                ]
            
            # Generate new rust-actions binds
            rust_actions_binds = []
            rust_actions_binds.append("# Rust Actions Programmatically Managed Binds")
            rust_actions_binds.append("# Generated by BindsManager")
            rust_actions_binds.append("")
            
            # Add crafting binds
            rust_actions_binds.append("# === CRAFTING BINDS ===")
            rust_actions_binds.extend(self.generate_crafting_binds())
            rust_actions_binds.append("")
            
            # Add API binds
            rust_actions_binds.append("# === API BINDS ===")
            rust_actions_binds.extend(self.generate_api_binds())
            rust_actions_binds.append("")
            
            # Add chat/connection binds
            rust_actions_binds.append("# === CHAT/CONNECTION BINDS ===")
            logger.info(f"Generating dynamic chat binds, current dynamic_binds count: {len(self.dynamic_binds)}")
            dynamic_chat_binds = self.generate_dynamic_chat_binds()
            logger.info(f"Generated {len(dynamic_chat_binds)} dynamic chat bind lines")
            rust_actions_binds.extend(dynamic_chat_binds)
            rust_actions_binds.append("")
            
            # Combine all sections
            all_lines = []
            
            # Add user section (contains default Rust binds)
            all_lines.append("#USER-SECTION-START")
            all_lines.extend(user_binds)
            all_lines.append("#USER-SECTION-END")
            all_lines.append("")
            
            # Add rust-actions section
            all_lines.append("#RUST-ACTIONS-START")
            all_lines.extend(rust_actions_binds)
            all_lines.append("#RUST-ACTIONS-END")
            all_lines.append("")
            
            # Write to file
            with open(self.keys_cfg_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_lines) + '\n')
            
            print(f"Successfully wrote keys.cfg with {len(all_lines)} total lines")
            print(f"  - {len(user_binds)} user-defined binds (including default Rust binds)")
            print(f"  - {len(rust_actions_binds)} rust-actions binds")
            return True
            
        except Exception as e:
            print(f"Error writing keys.cfg: {e}")
            return False
    
    def get_item_bind_info(self, item_id: int) -> Optional[Tuple[int, int]]:
        """Get the bind indices for a specific item (craft and cancel)."""
        return self.bind_mapping.get(item_id)
    
    def get_item_info(self, item_id: int) -> Optional[Dict]:
        """Get item information including amountToCreate from the database."""
        try:
            # Search through the item database for the item
            for db_item_id, item_data in self.item_database.get("items", {}).items():
                if item_data.get("numericId") == item_id:
                    return {
                        "id": db_item_id,
                        "numericId": item_data.get("numericId"),
                        "name": item_data.get("name", "Unknown"),
                        "shortname": item_data.get("shortname", "unknown"),
                        "amountToCreate": item_data.get("amountToCreate", 1),
                        "userCraftable": item_data.get("userCraftable", False)
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting item info for item_id {item_id}: {e}")
            return None
    
    def get_key_combo_for_bind(self, bind_index: int) -> Optional[str]:
        """Get the key combination for a specific bind index."""
        if 0 <= bind_index < len(self.key_combinations):
            return self.key_combinations[bind_index]
        return None
    
    def get_stats(self) -> Dict:
        """Get statistics about the binds manager."""
        return {
            "total_items": len(self.craftable_items),
            "total_key_combinations": len(self.key_combinations),
            "used_binds": len(self.used_binds),
            "available_binds": len(self.key_combinations) - len(self.used_binds),
            "crafting_binds_used": len([b for b in self.used_binds if self.CRAFTING_BINDS_START <= b <= self.CRAFTING_BINDS_END]),
            "api_binds_used": len([b for b in self.used_binds if self.API_BINDS_START <= b <= self.API_BINDS_END]),
            "chat_binds_used": len([b for b in self.used_binds if self.CHAT_BINDS_START <= b <= self.CHAT_BINDS_END])
        }
    
    def _backup_file_permissions(self) -> bool:
        """Backup current file permissions for later restoration."""
        try:
            if os.path.exists(self.keys_cfg_path):
                current_mode = os.stat(self.keys_cfg_path).st_mode
                self._file_permissions_backup = current_mode
                print(f"Backed up file permissions: {oct(current_mode)}")
                return True
            else:
                print("File doesn't exist, no permissions to backup")
                return False
        except Exception as e:
            print(f"Error backing up file permissions: {e}")
            return False
    
    def _restore_file_permissions(self) -> bool:
        """Restore previously backed up file permissions."""
        try:
            if self._file_permissions_backup is not None and os.path.exists(self.keys_cfg_path):
                os.chmod(self.keys_cfg_path, self._file_permissions_backup)
                print(f"Restored file permissions: {oct(self._file_permissions_backup)}")
                return True
            else:
                print("No permissions backup to restore or file doesn't exist")
                return False
        except Exception as e:
            print(f"Error restoring file permissions: {e}")
            return False
    
    def set_file_readonly(self) -> bool:
        """Set the keys.cfg file to read-only to prevent game modifications."""
        try:
            if not os.path.exists(self.keys_cfg_path):
                print("File doesn't exist, cannot set read-only")
                return False
            
            # Backup current permissions first
            self._backup_file_permissions()
            
            # Set read-only (remove write permission for all users)
            current_mode = os.stat(self.keys_cfg_path).st_mode
            readonly_mode = current_mode & ~stat.S_IWRITE & ~stat.S_IWGRP & ~stat.S_IWOTH
            os.chmod(self.keys_cfg_path, readonly_mode)
            
            print(f"Set keys.cfg to read-only: {oct(readonly_mode)}")
            return True
            
        except Exception as e:
            print(f"Error setting file to read-only: {e}")
            return False
    
    def set_file_writable(self) -> bool:
        """Set the keys.cfg file to writable for modifications."""
        try:
            if not os.path.exists(self.keys_cfg_path):
                print("File doesn't exist, cannot set writable")
                return False
            
            # Set writable (add write permission for owner)
            current_mode = os.stat(self.keys_cfg_path).st_mode
            writable_mode = current_mode | stat.S_IWRITE
            os.chmod(self.keys_cfg_path, writable_mode)
            
            print(f"Set keys.cfg to writable: {oct(writable_mode)}")
            return True
            
        except Exception as e:
            print(f"Error setting file to writable: {e}")
            return False
    
    def is_file_readonly(self) -> bool:
        """Check if the keys.cfg file is currently read-only."""
        try:
            if not os.path.exists(self.keys_cfg_path):
                return False
            
            current_mode = os.stat(self.keys_cfg_path).st_mode
            return not bool(current_mode & stat.S_IWRITE)
            
        except Exception as e:
            print(f"Error checking file permissions: {e}")
            return False
    
    def write_keys_cfg_with_sections_protected(self) -> bool:
        """Write keys.cfg with sections, handling file permissions automatically."""
        try:
            logger.info("Preparing to write keys.cfg...")
            
            # Set file to writable
            if not self.set_file_writable():
                logger.error("Failed to set file to writable")
                return False
            
            # Write the file
            logger.info("Calling write_keys_cfg_with_sections()...")
            success = self.write_keys_cfg_with_sections()
            logger.info(f"write_keys_cfg_with_sections() returned: {success}")
            
            if success:
                # Set file back to read-only to protect from game modifications
                logger.info("Setting file to read-only to protect from game modifications...")
                self.set_file_readonly()
            else:
                logger.error("write_keys_cfg_with_sections() failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in protected write operation: {e}")
            # Try to restore permissions on error
            self._restore_file_permissions()
            return False
    
    def get_or_create_dynamic_bind(self, command_type: str, string_value: str) -> int:
        """
        Get or create a dynamic bind for a chat/connection command.
        
        Args:
            command_type: Type of command ('chat_say', 'chat_teamsay', 'client_connect', 'respawn')
            string_value: The actual string value (message, IP, spawn_id, etc.)
        
        Returns:
            bind_index: The bind index for this string
        """
        # Create a unique key for this command
        bind_key = f"{command_type}:{string_value}"
        
        # Check if we already have a bind for this string
        if bind_key in self.dynamic_binds:
            bind_index = self.dynamic_binds[bind_key]
            # Move to end of order (most recently used)
            if bind_index in self.dynamic_bind_order:
                self.dynamic_bind_order.remove(bind_index)
            self.dynamic_bind_order.append(bind_index)
            return bind_index
        
        # We need to create a new bind
        # Check if we need to overwrite an old bind
        if len(self.dynamic_binds) >= (self.CHAT_BINDS_END - self.CHAT_BINDS_START + 1):
            # We're at capacity, need to overwrite the oldest bind
            oldest_bind_index = self.dynamic_bind_order.pop(0)  # Remove oldest
            
            # Find and remove the old bind_key from dynamic_binds
            old_bind_key = None
            for key, bind_index in self.dynamic_binds.items():
                if bind_index == oldest_bind_index:
                    old_bind_key = key
                    break
            
            if old_bind_key:
                del self.dynamic_binds[old_bind_key]
                logger.info(f"Overwriting old bind {old_bind_index} for '{old_bind_key}'")
            
            # Use the freed bind index
            bind_index = oldest_bind_index
        else:
            # Use the next available bind index
            bind_index = self.next_dynamic_bind
            self.next_dynamic_bind += 1
            
            # If we've reached the end, wrap back to start
            if self.next_dynamic_bind > self.CHAT_BINDS_END:
                self.next_dynamic_bind = self.CHAT_BINDS_START
        
        # Store the new bind
        self.dynamic_binds[bind_key] = bind_index
        self.dynamic_bind_order.append(bind_index)
        self.used_binds.add(bind_index)
        
        logger.info(f"Created new dynamic bind {bind_index} for '{command_type}:{string_value}'")
        
        return bind_index
    
    def generate_dynamic_chat_binds(self) -> List[str]:
        """Generate the actual dynamic chat/connection binds based on stored strings."""
        binds = []
        
        logger.info(f"generate_dynamic_chat_binds() called, dynamic_binds count: {len(self.dynamic_binds)}")
        
        if not self.dynamic_binds:
            # No dynamic binds yet, return placeholder binds
            logger.info("No dynamic binds found, returning placeholder binds")
            return self.generate_chat_binds()
        
        # Use the existing key combinations list for unique combinations
        # Each dynamic bind will get a unique key combination from the available pool
        
        # Define the command templates
        command_templates = {
            "chat_say": "chat.say",
            "chat_teamsay": "chat.teamsay",
            "client_connect": "disconnect;client.connect",
            "respawn_sleepingbag": "respawn_sleepingbag",
            "inventory_give": "inventory.give"
        }
        
        # Generate binds for each stored dynamic bind
        logger.info(f"Generating binds for {len(self.dynamic_binds)} dynamic binds:")
        for bind_key, bind_index in self.dynamic_binds.items():
            command_type, string_value = bind_key.split(":", 1)
            logger.info(f"  Processing: {bind_key} -> bind {bind_index}")
            
            if command_type in command_templates:
                # Use the unique key combination for this bind index
                if bind_index < len(self.key_combinations):
                    key_combo = self.key_combinations[bind_index]
                else:
                    # Fallback if we somehow exceed the available combinations
                    key_combo = "keypaddivide+keypadplus+keypad4+keypad7+period"
                
                # Wrap string values in quotes for chat commands
                if command_type in ["chat_say", "chat_teamsay"]:
                    command = f"{command_templates[command_type]} \"{string_value}\""
                elif command_type == "inventory_give":
                    # For inventory.give, the string_value is already the full command
                    command = string_value
                else:
                    command = f"{command_templates[command_type]} {string_value}"
                bind = self._format_bind_command(key_combo, command)
                
                binds.append(f"# Dynamic: {command_type} - '{string_value}' - bind no.{bind_index}")
                binds.append(bind)
                binds.append("")
                logger.info(f"    Generated: {bind}")
            else:
                logger.warning(f"    Unknown command type: {command_type}")
        
        # Fill remaining slots with empty binds (but don't add them to used_binds)
        dynamic_slots_used = len(self.dynamic_binds)
        dynamic_slots_total = self.CHAT_BINDS_END - self.CHAT_BINDS_START + 1
        
        if dynamic_slots_used < dynamic_slots_total:
            binds.append(f"# Empty reserved binds for future dynamic chat/connection commands")
            for bind_index in range(self.CHAT_BINDS_START, self.CHAT_BINDS_END + 1):
                if bind_index not in self.dynamic_binds.values():
                    # Use the actual key combination for this bind index
                    if bind_index < len(self.key_combinations):
                        key_combo = self.key_combinations[bind_index]
                    else:
                        # Fallback to a placeholder if we run out of combinations
                        key_combo = "keypaddivide+keypadplus+keypad4+keypad7+period"
                    empty_bind = self._format_bind_command(key_combo, '""')
                    binds.append(f"# Reserved bind no.{bind_index}")
                    binds.append(empty_bind)
                    # Don't add empty binds to used_binds - they should remain available
            binds.append("")
        
        return binds
    
    def reload_dynamic_binds(self) -> bool:
        """Reload the keys.cfg file in Rust to apply dynamic bind changes."""
        try:
            # This will be called by the keyboard manager to reload binds
            # The actual reload is done by pressing F1, typing 'exec keys.cfg', and pressing enter
            logger.info("Dynamic binds updated, reload required in Rust")
            return True
        except Exception as e:
            logger.error(f"Error reloading dynamic binds: {e}")
            return False
    
    def get_dynamic_bind_stats(self) -> Dict:
        """Get statistics about dynamic binds."""
        return {
            "total_dynamic_binds": len(self.dynamic_binds),
            "next_bind_index": self.next_dynamic_bind,
            "bind_order_length": len(self.dynamic_bind_order),
            "available_slots": (self.CHAT_BINDS_END - self.CHAT_BINDS_START + 1) - len(self.dynamic_binds)
        }
    
    def _load_dynamic_binds_from_keys_cfg(self) -> bool:
        """Load dynamic binds from the keys.cfg file."""
        try:
            if not os.path.exists(self.keys_cfg_path):
                logger.info("No keys.cfg file found, starting with empty dynamic binds")
                return True
            
            # Temporarily make file readable if it's read-only
            was_readonly = self.is_file_readonly()
            if was_readonly:
                logger.info("File is read-only, temporarily making it readable...")
                if not self.set_file_writable():
                    logger.error("Failed to make file writable for reading")
                    return False
            
            try:
                # Read the keys.cfg file
                with open(self.keys_cfg_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            finally:
                # Restore read-only state if it was read-only before
                if was_readonly:
                    logger.info("Restoring read-only state...")
                    self.set_file_readonly()
            
            # Parse dynamic binds from the file
            in_rust_actions_section = False
            in_chat_section = False
            
            for line in lines:
                line = line.strip()
                
                # Check for section markers
                if line == "#RUST-ACTIONS-START":
                    in_rust_actions_section = True
                    continue
                elif line == "#RUST-ACTIONS-END":
                    in_rust_actions_section = False
                    continue
                elif line == "# === CHAT/CONNECTION BINDS ===":
                    in_chat_section = True
                    continue
                
                # Only process lines in the chat section
                if not in_rust_actions_section or not in_chat_section:
                    continue
                
                # Look for dynamic bind comments
                if line.startswith("# Dynamic:"):
                    # Parse the dynamic bind info
                    # Format: # Dynamic: command_type - 'string_value' - bind no.bind_index
                    try:
                        # Extract command_type and string_value
                        parts = line.split(" - '")
                        if len(parts) >= 2:
                            command_part = parts[0].replace("# Dynamic: ", "")
                            string_part = parts[1].split("' - bind no.")[0]
                            bind_index_part = line.split("bind no.")[1]
                            
                            command_type = command_part.strip()
                            string_value = string_part.strip()
                            bind_index = int(bind_index_part)
                            
                            # Store the dynamic bind
                            bind_key = f"{command_type}:{string_value}"
                            self.dynamic_binds[bind_key] = bind_index
                            self.dynamic_bind_order.append(bind_index)
                            self.used_binds.add(bind_index)
                            
                            # Update next_dynamic_bind
                            if bind_index >= self.next_dynamic_bind:
                                self.next_dynamic_bind = bind_index + 1
                                
                    except Exception as e:
                        logger.warning(f"Failed to parse dynamic bind line: {line} - {e}")
                        continue
            
            # Ensure next_dynamic_bind is within valid range
            if self.next_dynamic_bind < self.CHAT_BINDS_START or self.next_dynamic_bind > self.CHAT_BINDS_END:
                self.next_dynamic_bind = self.CHAT_BINDS_START
            
            logger.info(f"Loaded {len(self.dynamic_binds)} dynamic binds from keys.cfg")
            return True
            
        except Exception as e:
            logger.error(f"Error loading dynamic binds from keys.cfg: {e}")
            # Reset to defaults on error
            self.dynamic_binds = {}
            self.next_dynamic_bind = self.CHAT_BINDS_START
            self.dynamic_bind_order = []
            return False
    
    def _migrate_dynamic_binds_from_json(self) -> bool:
        """One-time migration from old JSON file to keys.cfg format."""
        try:
            json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dynamic_binds.json")
            
            # Check if JSON file exists and we don't have dynamic binds loaded
            if os.path.exists(json_file_path) and not self.dynamic_binds:
                logger.info("Found old dynamic_binds.json, migrating to keys.cfg format...")
                
                # Load data from JSON file
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Restore the data
                self.dynamic_binds = data.get("dynamic_binds", {})
                self.next_dynamic_bind = data.get("next_dynamic_bind", self.CHAT_BINDS_START)
                self.dynamic_bind_order = data.get("dynamic_bind_order", [])
                
                # Ensure next_dynamic_bind is within valid range
                if self.next_dynamic_bind < self.CHAT_BINDS_START or self.next_dynamic_bind > self.CHAT_BINDS_END:
                    self.next_dynamic_bind = self.CHAT_BINDS_START
                
                # Add all dynamic bind indices to used_binds
                for bind_index in self.dynamic_binds.values():
                    self.used_binds.add(bind_index)
                
                logger.info(f"Migrated {len(self.dynamic_binds)} dynamic binds from JSON to memory")
                
                # Immediately write to keys.cfg to persist the migration
                if self.write_keys_cfg_with_sections_protected():
                    logger.info("Successfully migrated dynamic binds to keys.cfg")
                    
                    # Remove the old JSON file after successful migration
                    try:
                        os.remove(json_file_path)
                        logger.info("Removed old dynamic_binds.json file after successful migration")
                    except Exception as e:
                        logger.warning(f"Could not remove old JSON file: {e}")
                    
                    return True
                else:
                    logger.error("Failed to write migrated dynamic binds to keys.cfg")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating dynamic binds from JSON: {e}")
            return False
    
    def reload_dynamic_binds_from_file(self) -> bool:
        """Reload dynamic binds from keys.cfg file."""
        try:
            logger.info("Reloading dynamic binds from keys.cfg file...")
            
            # Clear current dynamic bind state
            self.dynamic_binds.clear()
            self.dynamic_bind_order.clear()
            self.next_dynamic_bind = self.CHAT_BINDS_START
            
            # Remove dynamic bind indices from used_binds
            for bind_index in range(self.CHAT_BINDS_START, self.CHAT_BINDS_END + 1):
                if bind_index in self.used_binds:
                    self.used_binds.remove(bind_index)
            
            # Load dynamic binds from keys.cfg
            success = self._load_dynamic_binds_from_keys_cfg()
            
            if success:
                logger.info(f"Successfully reloaded {len(self.dynamic_binds)} dynamic binds from keys.cfg")
            else:
                logger.error("Failed to reload dynamic binds from keys.cfg")
            
            return success
            
        except Exception as e:
            logger.error(f"Error reloading dynamic binds from file: {e}")
            return False
    
    def regenerate_with_cleared_dynamic_binds(self) -> bool:
        """Regenerate the keys.cfg file with all dynamic binds cleared."""
        try:
            logger.info("Regenerating keys.cfg with cleared dynamic binds...")
            
            # Clear all dynamic chat/connection binds from memory
            self.dynamic_binds.clear()
            self.dynamic_bind_order.clear()
            self.next_dynamic_bind = self.CHAT_BINDS_START
            
            # Remove dynamic bind indices from used_binds
            for bind_index in range(self.CHAT_BINDS_START, self.CHAT_BINDS_END + 1):
                if bind_index in self.used_binds:
                    self.used_binds.remove(bind_index)
            
            # Regenerate the file with cleared dynamic binds
            success = self.write_keys_cfg_with_sections_protected()
            
            if success:
                logger.info("Successfully regenerated keys.cfg with cleared dynamic binds")
            else:
                logger.error("Failed to regenerate keys.cfg with cleared dynamic binds")
            
            return success
            
        except Exception as e:
            logger.error(f"Error regenerating with cleared dynamic binds: {e}")
            return False


def main():
    """Main function to test the binds manager."""
    manager = BindsManager()
    
    # Print stats
    stats = manager.get_stats()
    print("Binds Manager Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Generate and write keys.cfg with proper sections (protected)
    print("\nGenerating keys.cfg with sections (protected)...")
    success = manager.write_keys_cfg_with_sections_protected()
    
    if success:
        print("Keys.cfg generation completed successfully!")
        print("To use these binds in Rust:")
        print("1. The keys.cfg file now includes all sections")
        print("2. Restart Rust or press F1 and type 'exec keys.cfg'")
        print("3. User binds are preserved in the USER-SECTION")
        print("4. Rust-actions binds are managed in the RUST-ACTIONS section")
    else:
        print("Keys.cfg generation failed!")


if __name__ == "__main__":
    main()
