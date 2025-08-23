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
        # Use absolute path for item database to ensure it works when running as subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.item_database_path = os.path.join(current_dir, "data", "itemDatabase.json")
        
        # Available keys for binds
        self.available_keys = [
            'keypaddivide', 'keypadmultiply', 'keypadminus', 'keypadplus', 'keypadperiod',
            'keypad1', 'keypad2', 'keypad3', 'keypad4', 'keypad5', 'keypad6', 'keypad7', 'keypad8', 'keypad9', 'keypad0',
            'f13', 'f14', 'f15',
            'slash', 'period', 'comma', 'quote', 'backquote', 'semicolon', 'leftbracket', 'rightbracket'
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
        
        # File permission management
        self._file_permissions_backup = None
        
    def _load_item_database(self) -> Dict:
        """Load the item database from JSON file."""
        try:
            print(f"DEBUG: Loading item database from: {self.item_database_path}")
            with open(self.item_database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"DEBUG: Successfully loaded item database with {len(data.get('items', {}))} items")
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
        """Extract all user-craftable items from the database."""
        craftable_items = []
        print(f"DEBUG: Processing {len(self.item_database.get('items', {}))} items for craftable items")
        for item_id, item_data in self.item_database.get("items", {}).items():
            if item_data.get("userCraftable", False):
                craftable_items.append({
                    "id": item_id,
                    "numericId": item_data.get("numericId", int(item_id)),
                    "name": item_data.get("name", "Unknown"),
                    "shortname": item_data.get("shortname", "unknown")
                })
        print(f"DEBUG: Found {len(craftable_items)} craftable items")
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
            
            # DEBUG: Log the item details during bind generation
            logger.info(f"DEBUG: Generating binds for item '{item_name}' with numericId: {item['numericId']} -> item_id: {item_id} (type: {type(item_id)})")
            
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
            ("autorun", "forward;sprint"),
            ("autorun_jump", "forward;sprint;jump"),
            ("crouch_attack", "attack;duck"),
            ("quit_game", "quit"),
            ("disconnect", "disconnect"),
            ("lookat_radius_20", "client.lookatradius 20"),
            ("lookat_radius_0", "client.lookatradius 0.0002"),
            ("audio_voices_0", "audio.voices 0"),
            ("audio_voices_25", "audio.voices 0.25"),
            ("audio_voices_50", "audio.voices 0.5"),
            ("audio_voices_75", "audio.voices 0.75"),
            ("audio_voices_100", "audio.voices 1"),
            ("audio_master_0", "audio.master 0"),
            ("audio_master_25", "audio.master 0.25"),
            ("audio_master_50", "audio.master 0.5"),
            ("audio_master_75", "audio.master 0.75"),
            ("audio_master_100", "audio.master 1"),
            ("hud_off", "graphics.hud 0"),
            ("hud_on", "graphics.hud 1"),
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
        """Generate binds for chat and connection commands (placeholder)."""
        binds = []
        print(f"Generating chat/connection binds (placeholder)...")
        
        # These will be populated dynamically when needed
        chat_commands = [
            ("chat_say", "chat.say"),
            ("chat_teamsay", "chat.teamsay"),
            ("client_connect", "client.connect"),
            ("respawn", "respawn"),
        ]
        
        for i, (name, command) in enumerate(chat_commands):
            bind_index = self.CHAT_BINDS_START + i
            if bind_index >= len(self.key_combinations):
                print(f"Warning: Not enough key combinations for chat binds. Stopping at {name}")
                break
                
            key_combo = self.key_combinations[bind_index]
            bind = self._format_bind_command(key_combo, f"{command} <placeholder>")
            binds.append(f"# Chat/Connection: {name} (placeholder) - reserved bind no.{bind_index}")
            binds.append(bind)
            binds.append("")
            
            self.used_binds.add(bind_index)
        
        # Fill remaining chat slots with empty binds
        chat_slots_used = len(chat_commands)
        chat_slots_total = self.CHAT_BINDS_END - self.CHAT_BINDS_START + 1
        
        if chat_slots_used < chat_slots_total:
            binds.append(f"# Empty reserved binds for future chat/connection commands")
            for bind_index in range(self.CHAT_BINDS_START + chat_slots_used, self.CHAT_BINDS_END + 1):
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
                
                if current_section == "user":
                    user_binds.append(line)
                elif current_section == "rust_actions":
                    rust_actions_binds.append(line)
                else:
                    other_binds.append(line)
            
            # If no section markers were found, treat all bind lines as other_binds (default Rust binds)
            if not any(line.strip() in ["#USER-SECTION-START", "#RUST-ACTIONS-START"] for line in lines):
                other_binds = [line.rstrip('\n') for line in lines if line.strip() and not line.strip().startswith('#')]
                user_binds = []
                rust_actions_binds = []
            
            return user_binds, rust_actions_binds, other_binds
            
        except Exception as e:
            print(f"Error reading keys.cfg: {e}")
            return user_binds, rust_actions_binds, other_binds
    
    def write_keys_cfg_with_sections(self) -> bool:
        """Write keys.cfg with proper sections."""
        try:
            # Read existing sections
            user_binds, _, other_binds = self.read_existing_keys_cfg()
            
            # If no existing file or no other_binds, create default Rust binds
            if not other_binds:
                other_binds = [
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
            rust_actions_binds.extend(self.generate_chat_binds())
            rust_actions_binds.append("")
            
            # Combine all sections
            all_lines = []
            
            # Add other binds (default Rust binds)
            all_lines.extend(other_binds)
            all_lines.append("")
            
            # Add user section
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
                f.write('\n'.join(all_lines))
            
            print(f"Successfully wrote keys.cfg with {len(all_lines)} total lines")
            print(f"  - {len(other_binds)} default Rust binds")
            print(f"  - {len(user_binds)} user-defined binds")
            print(f"  - {len(rust_actions_binds)} rust-actions binds")
            return True
            
        except Exception as e:
            print(f"Error writing keys.cfg: {e}")
            return False
    
    def get_item_bind_info(self, item_id: int) -> Optional[Tuple[int, int]]:
        """Get the bind indices for a specific item (craft and cancel)."""
        # DEBUG: Log the lookup attempt
        logger = logging.getLogger(__name__)
        logger.info(f"DEBUG: get_item_bind_info called with item_id: {item_id} (type: {type(item_id)})")
        logger.info(f"DEBUG: bind_mapping type: {type(self.bind_mapping)}")
        logger.info(f"DEBUG: bind_mapping keys sample: {list(self.bind_mapping.keys())[:5]}")
        logger.info(f"DEBUG: bind_mapping key types sample: {[type(k) for k in list(self.bind_mapping.keys())[:5]]}")
        result = self.bind_mapping.get(item_id)
        logger.info(f"DEBUG: Lookup result: {result}")
        return result
    
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
            print("Preparing to write keys.cfg...")
            
            # Set file to writable
            if not self.set_file_writable():
                print("Failed to set file to writable")
                return False
            
            # Write the file
            success = self.write_keys_cfg_with_sections()
            
            if success:
                # Set file back to read-only to protect from game modifications
                print("Setting file to read-only to protect from game modifications...")
                self.set_file_readonly()
            
            return success
            
        except Exception as e:
            print(f"Error in protected write operation: {e}")
            # Try to restore permissions on error
            self._restore_file_permissions()
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
