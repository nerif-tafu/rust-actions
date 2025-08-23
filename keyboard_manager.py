import json
import time
import threading
import os
from typing import Dict, List, Optional, Tuple, Any
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from binds_manager import BindsManager

class KeyboardSimulator:
    def __init__(self):
        # Initialize the keyboard controller
        self.controller = keyboard.Controller()
        
        # Available keys mapping
        self.available_keys = {
            # Letters
            'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g', 'h': 'h',
            'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o', 'p': 'p',
            'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x',
            'y': 'y', 'z': 'z',
            
            # Numbers
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
            '8': '8', '9': '9',
            
            # Function keys
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            'f13': Key.f13, 'f14': Key.f14, 'f15': Key.f15, 'f16': Key.f16,
            'f17': Key.f17, 'f18': Key.f18, 'f19': Key.f19, 'f20': Key.f20,
            'f21': Key.f21, 'f22': Key.f22, 'f23': Key.f23, 'f24': Key.f24,
            
            # Modifier keys
            'ctrl': Key.ctrl, 'left_ctrl': Key.ctrl_l, 'right_ctrl': Key.ctrl_r,
            'leftcontrol': Key.ctrl_l, 'rightcontrol': Key.ctrl_r,
            'shift': Key.shift, 'left_shift': Key.shift_l, 'right_shift': Key.shift_r,
            'leftshift': Key.shift_l, 'rightshift': Key.shift_r,
            'alt': Key.alt, 'left_alt': Key.alt_l, 'right_alt': Key.alt_r,
            'meta': Key.cmd, 'left_meta': Key.cmd_l, 'right_meta': Key.cmd_r,
            'windows': Key.cmd, 'left_windows': Key.cmd_l, 'right_windows': Key.cmd_r,
            'cmd': Key.cmd, 'left_cmd': Key.cmd_l, 'right_cmd': Key.cmd_r,
            
            # Special keys
            'enter': Key.enter, 'return': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'escape': Key.esc, 'esc': Key.esc,
            'backspace': Key.backspace,
            'delete': Key.delete, 'del': Key.delete,
            'insert': Key.insert, 'ins': Key.insert,
            'home': Key.home,
            'end': Key.end,
            'pageup': Key.page_up, 'page_up': Key.page_up,
            'pagedown': Key.page_down, 'page_down': Key.page_down,
            'numlock': Key.num_lock, 'num_lock': Key.num_lock,
            
            # Arrow keys
            'up': Key.up, 'up_arrow': Key.up, 'uparrow': Key.up,
            'down': Key.down, 'down_arrow': Key.down, 'downarrow': Key.down,
            'left': Key.left, 'left_arrow': Key.left, 'leftarrow': Key.left,
            'right': Key.right, 'right_arrow': Key.right, 'rightarrow': Key.right,
            
            # Numpad keys (using extended key codes to ensure they're recognized as keypad keys)
            'keypad0': KeyCode.from_vk(96), 'keypad1': KeyCode.from_vk(97), 'keypad2': KeyCode.from_vk(98),
            'keypad3': KeyCode.from_vk(99), 'keypad4': KeyCode.from_vk(100), 'keypad5': KeyCode.from_vk(101),
            'keypad6': KeyCode.from_vk(102), 'keypad7': KeyCode.from_vk(103), 'keypad8': KeyCode.from_vk(104),
            'keypad9': KeyCode.from_vk(105), 'keypadperiod': KeyCode.from_vk(110), 'keypadenter': KeyCode.from_vk(108),
            'keypadplus': KeyCode.from_vk(107), 'keypadminus': KeyCode.from_vk(109), 
            'keypadmultiply': KeyCode.from_vk(106), 'keypaddivide': KeyCode.from_vk(111),
            
            # Punctuation and symbols
            'comma': ',', ',': ',',
            'period': '.', '.': '.',
            'semicolon': ';', ';': ';',
            'colon': ':', ':': ':',
            'slash': '/', '/': '/',
            'backslash': '\\', '\\': '\\',
            'minus': '-', '-': '-',
            'equals': '=', '=': '=',
            'plus': '+', '+': '+',
            'underscore': '_', '_': '_',
            'bracket_left': '[', '[': '[', 'leftbracket': '[',
            'bracket_right': ']', ']': ']', 'rightbracket': ']',
            'brace_left': '{', '{': '{',
            'brace_right': '}', '}': '}',
            'pipe': '|', '|': '|',
            'tilde': '~', '~': '~',
            'backtick': '`', '`': '`',
            'quote': "'", "'": "'",
            'double_quote': '"', '"': '"',
            'question': '?', '?': '?',
            'exclamation': '!', '!': '!',
            'at': '@', '@': '@',
            'hash': '#', '#': '#',
            'dollar': '$', '$': '$',
            'percent': '%', '%': '%',
            'caret': '^', '^': '^',
            'ampersand': '&', '&': '&',
            'asterisk': '*', '*': '*',
            'parenthesis_left': '(', '(': '(',
            'parenthesis_right': ')', ')': ')',
        }
    
    def normalize_key(self, key):
        """Convert key name to pynput Key or KeyCode"""
        if key in self.available_keys:
            return self.available_keys[key]
        return None
    
    def single(self, key):
        """Simulate a single key press"""
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            # For numpad keys, ensure NumLock is on
            if key.startswith('keypad'):
                self._ensure_numlock_on()
            
            self.controller.press(normalized_key)
            time.sleep(0.05)  # Hold for 50ms
            self.controller.release(normalized_key)
        except Exception as e:
            raise Exception(f"Failed to send key {normalized_key}: {str(e)}")
    
    def _ensure_numlock_on(self):
        """Ensure NumLock is turned on for numpad operations"""
        try:
            # Check if NumLock is off by trying to send a numpad key
            # If it sends a different character, NumLock is off
            # We'll temporarily turn it on
            self.controller.press(Key.num_lock)
            time.sleep(0.01)
            self.controller.release(Key.num_lock)
            time.sleep(0.01)
        except:
            # If num_lock key is not available, we'll try alternative approach
            pass
    
    def combo(self, keys: List[str]):
        """Simulate a multi-key combination"""
        normalized_keys = []
        for key in keys:
            normalized_key = self.normalize_key(key)
            if not normalized_key:
                raise ValueError(f"Invalid key: {key}")
            normalized_keys.append(normalized_key)
        
        try:
            # Press all keys down
            for key in normalized_keys:
                self.controller.press(key)
            
            # Hold for a moment
            time.sleep(0.1)
            
            # Release in reverse order
            for key in reversed(normalized_keys):
                self.controller.release(key)
        except Exception as e:
            raise Exception(f"Failed to send combination {'+'.join(keys)}: {str(e)}")
    
    def down(self, key):
        """Simulate key down"""
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            self.controller.press(normalized_key)
        except Exception as e:
            raise Exception(f"Failed to send key down {normalized_key}: {str(e)}")
    
    def up(self, key):
        """Simulate key up"""
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            self.controller.release(normalized_key)
        except Exception as e:
            raise Exception(f"Failed to send key up {normalized_key}: {str(e)}")
    
    def type_string(self, text):
        """Type a string"""
        if not text or not isinstance(text, str):
            raise ValueError("Text parameter must be a non-empty string")
        
        try:
            self.controller.type(text)
        except Exception as e:
            raise Exception(f"Failed to type string: {str(e)}")
    
    def get_available_keys(self):
        """Get list of available keys"""
        return list(self.available_keys.keys())


import logging

class KeyboardManager:
    def __init__(self):
        logger = logging.getLogger(__name__)
        logger.info("=== KeyboardManager Initialization Start ===")
        self.binds_manager = BindsManager()
        self.keyboard_simulator = KeyboardSimulator()
        
        # Cache for key combinations
        self._key_combo_cache = {}
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Load key combinations into cache
        self._load_key_combinations()
        logger.info("=== KeyboardManager Initialization Complete ===")
    
    def _load_key_combinations(self):
        """Load all key combinations into cache for faster lookup"""
        logger = logging.getLogger(__name__)
        logger.info("Loading key combinations into cache...")
        for i, combo in enumerate(self.binds_manager.key_combinations):
            self._key_combo_cache[i] = combo.split('+')
        logger.info(f"Cached {len(self._key_combo_cache)} key combinations")
        
        # Force regeneration of bind mapping to ensure integer keys
        logger.info("Force regenerating bind mapping to ensure integer keys...")
        self.binds_manager.bind_mapping = {}  # Clear existing mapping
        self.binds_manager.generate_crafting_binds()  # Regenerate with integer keys
        logger.info(f"Regenerated bind mapping with {len(self.binds_manager.bind_mapping)} items")
        
        # DEBUG: Show some sample keys to verify they're integers
        sample_keys = list(self.binds_manager.bind_mapping.keys())[:5]
        logger.info(f"DEBUG: Sample bind_mapping keys: {sample_keys}")
        logger.info(f"DEBUG: Sample key types: {[type(k) for k in sample_keys]}")
        
        # Always regenerate keys.cfg to ensure it matches current available keys
        logger.info("Regenerating keys.cfg with protected write...")
        self.binds_manager.write_keys_cfg_with_sections_protected()
    
    def get_key_combo_for_bind(self, bind_index: int) -> Optional[List[str]]:
        """Get the key combination for a specific bind index"""
        return self._key_combo_cache.get(bind_index)
    
    def trigger_bind(self, bind_index: int) -> bool:
        """Trigger a bind by its index"""
        with self._lock:
            try:
                key_combo = self.get_key_combo_for_bind(bind_index)
                if not key_combo:
                    print(f"Warning: No key combination found for bind index {bind_index}")
                    return False
                
                print(f"Triggering bind {bind_index}: {'+'.join(key_combo)}")
                self.keyboard_simulator.combo(key_combo)
                return True
                
            except Exception as e:
                print(f"Error triggering bind {bind_index}: {e}")
                return False
    
    def craft_item(self, item_id: int) -> bool:
        """Craft an item by its ID"""
        print(f"PRINT: craft_item called with item_id: {item_id} (type: {type(item_id)})")
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"DEBUG: craft_item called with item_id: {item_id} (type: {type(item_id)})")
            
            # DEBUG: Log the item_id being looked up
            logger.info(f"DEBUG: Looking up bind for item_id: {item_id} (type: {type(item_id)})")
            logger.info(f"DEBUG: bind_mapping keys: {list(self.binds_manager.bind_mapping.keys())[:10]}...")  # Show first 10 keys
            
            logger.info(f"DEBUG: About to call get_item_bind_info...")
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            logger.info(f"DEBUG: get_item_bind_info returned: {bind_info}")
            
            if not bind_info:
                logger.warning(f"Warning: No bind found for item ID {item_id}")
                return False
            
            logger.info(f"DEBUG: About to unpack bind_info: {bind_info}")
            craft_bind_index, _ = bind_info
            logger.info(f"DEBUG: Unpacked craft_bind_index: {craft_bind_index} (type: {type(craft_bind_index)})")
            
            logger.info(f"DEBUG: About to call trigger_bind with craft_bind_index: {craft_bind_index}")
            result = self.trigger_bind(craft_bind_index)
            logger.info(f"DEBUG: trigger_bind returned: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error crafting item {item_id}: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def cancel_craft_item(self, item_id: int) -> bool:
        """Cancel crafting an item by its ID"""
        try:
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            if not bind_info:
                print(f"Warning: No bind found for item ID {item_id}")
                return False
            
            _, cancel_bind_index = bind_info
            return self.trigger_bind(cancel_bind_index)
            
        except Exception as e:
            print(f"Error canceling craft for item {item_id}: {e}")
            return False
    
    def trigger_api_command(self, command_name: str) -> bool:
        """Trigger an API command by name"""
        api_commands = {
            "kill": 3000,
            "autorun": 3001,
            "autorun_jump": 3002,
            "crouch_attack": 3003,
            "quit_game": 3004,
            "disconnect": 3005,
            "lookat_radius_20": 3006,
            "lookat_radius_0": 3007,
            "audio_voices_0": 3008,
            "audio_voices_25": 3009,
            "audio_voices_50": 3010,
            "audio_voices_75": 3011,
            "audio_voices_100": 3012,
            "audio_master_0": 3013,
            "audio_master_25": 3014,
            "audio_master_50": 3015,
            "audio_master_75": 3016,
            "audio_master_100": 3017,
            "hud_off": 3018,
            "hud_on": 3019,
        }
        
        bind_index = api_commands.get(command_name)
        if bind_index is None:
            print(f"Warning: Unknown API command: {command_name}")
            return False
        
        return self.trigger_bind(bind_index)
    
    def trigger_chat_command(self, command_name: str, **kwargs) -> bool:
        """Trigger a chat/connection command by name"""
        # For now, these are placeholders - they'll need to be implemented
        # when the actual chat commands are added to the binds
        chat_commands = {
            "chat_say": 4000,
            "chat_teamsay": 4001,
            "client_connect": 4002,
            "respawn": 4003,
        }
        
        bind_index = chat_commands.get(command_name)
        if bind_index is None:
            print(f"Warning: Unknown chat command: {command_name}")
            return False
        
        # For now, just trigger the bind (placeholders)
        return self.trigger_bind(bind_index)
    
    def stack_inventory(self, iterations: int = 100) -> bool:
        """Stack inventory by triggering the stack inventory binds"""
        try:
            # These are the item IDs for the stack inventory items
            stack_items = [-97956382, 1390353317, 15388698]  # TC, Wood, Stone
            
            print(f"Stacking inventory {iterations} times...")
            for i in range(iterations):
                for item_id in stack_items:
                    if not self.craft_item(item_id):
                        print(f"Failed to stack item {item_id} on iteration {i}")
                        return False
                time.sleep(0.01)  # Small delay between iterations
            
            return True
            
        except Exception as e:
            print(f"Error stacking inventory: {e}")
            return False
    
    def cancel_stack_inventory(self, iterations: int = 100) -> bool:
        """Cancel stack inventory by triggering the cancel binds"""
        try:
            # These are the item IDs for the stack inventory items
            stack_items = [-97956382, 1390353317, 15388698]  # TC, Wood, Stone
            
            print(f"Canceling stack inventory {iterations} times...")
            for i in range(iterations):
                for item_id in stack_items:
                    if not self.cancel_craft_item(item_id):
                        print(f"Failed to cancel stack item {item_id} on iteration {i}")
                        return False
                time.sleep(0.01)  # Small delay between iterations
            
            return True
            
        except Exception as e:
            print(f"Error canceling stack inventory: {e}")
            return False
    
    def stack_inventory_continuous(self, enable: bool) -> bool:
        """Enable or disable continuous stack inventory"""
        if enable:
            print("Starting continuous stack inventory...")
            # This would need to be implemented with a background thread
            # For now, just return success
            return True
        else:
            print("Stopping continuous stack inventory...")
            # This would need to stop the background thread
            return True
    
    def copy_json_to_clipboard(self, data: Any) -> bool:
        """Copy JSON data to clipboard"""
        try:
            import pyperclip
            json_str = json.dumps(data, indent=2)
            pyperclip.copy(json_str)
            print(f"Copied JSON data to clipboard: {len(json_str)} characters")
            return True
        except ImportError:
            print("Error: pyperclip not installed. Cannot copy to clipboard.")
            return False
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
    
    def type_and_enter(self, text: str) -> bool:
        """Type text and press enter"""
        try:
            print(f"Typing and entering: {text}")
            self.keyboard_simulator.type_string(text)
            time.sleep(0.1)
            self.keyboard_simulator.single('enter')
            return True
        except Exception as e:
            print(f"Error typing and entering text: {e}")
            return False
    
    def reload_binds(self) -> bool:
        """Reload binds by pressing F1, typing 'exec keys.cfg', and pressing enter"""
        try:
            print("Reloading binds...")
            # Press F1 to open console
            self.keyboard_simulator.single('f1')
            time.sleep(0.2)
            
            # Type the command
            self.keyboard_simulator.type_string("exec keys.cfg")
            time.sleep(0.1)
            
            # Press enter
            self.keyboard_simulator.single('enter')
            time.sleep(0.2)
            
            print("Binds reloaded successfully")
            return True
            
        except Exception as e:
            print(f"Error reloading binds: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics about the keyboard manager"""
        return {
            "total_binds": len(self._key_combo_cache),
            "available_commands": {
                "crafting_items": len(self.binds_manager.craftable_items),
                "api_commands": 20,
                "chat_commands": 4
            }
        }
    
    def set_keys_cfg_readonly(self) -> bool:
        """Set the keys.cfg file to read-only to prevent game modifications."""
        return self.binds_manager.set_file_readonly()
    
    def set_keys_cfg_writable(self) -> bool:
        """Set the keys.cfg file to writable for modifications."""
        return self.binds_manager.set_file_writable()
    
    def is_keys_cfg_readonly(self) -> bool:
        """Check if the keys.cfg file is currently read-only."""
        return self.binds_manager.is_file_readonly()
    
    def regenerate_keys_cfg_protected(self) -> bool:
        """Regenerate the keys.cfg file with protected write operations."""
        return self.binds_manager.write_keys_cfg_with_sections_protected()


def main():
    """Test the keyboard manager"""
    manager = KeyboardManager()
    
    # Print stats
    stats = manager.get_stats()
    print("Keyboard Manager Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test some basic functionality
    print("\nTesting basic functionality...")
    
    # Test API command
    print("Testing API command 'kill'...")
    success = manager.trigger_api_command("kill")
    print(f"Result: {'Success' if success else 'Failed'}")
    
    # Test crafting (using first craftable item)
    if manager.binds_manager.craftable_items:
        test_item = manager.binds_manager.craftable_items[0]
        print(f"Testing craft item: {test_item['name']} (ID: {test_item['numericId']})...")
        # Convert numericId to integer
        item_id_int = int(test_item['numericId'])
        success = manager.craft_item(item_id_int)
        print(f"Result: {'Success' if success else 'Failed'}")
    
    print("\nKeyboard manager is ready for use!")


if __name__ == "__main__":
    main()
