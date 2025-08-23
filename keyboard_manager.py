import json
import time
import threading
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from binds_manager import BindsManager

# Add win32gui import for window focus checking
try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: win32gui not available. Focus checking will be disabled.")

# Setup logger
logger = logging.getLogger(__name__)

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
            
            # Numpad keys (using virtual key codes)
            'keypad0': KeyCode.from_vk(96), 'keypad1': KeyCode.from_vk(97), 'keypad2': KeyCode.from_vk(98),
            'keypad3': KeyCode.from_vk(99), 'keypad4': KeyCode.from_vk(100), 'keypad5': KeyCode.from_vk(101),
            'keypad6': KeyCode.from_vk(102), 'keypad7': KeyCode.from_vk(103), 'keypad8': KeyCode.from_vk(104),
            'keypad9': KeyCode.from_vk(105), 'keypadperiod': KeyCode.from_vk(110), 'keypadenter': KeyCode.from_vk(108),
            'keypadplus': KeyCode.from_vk(107), 'keypadminus': KeyCode.from_vk(109), 
            'keypadmultiply': KeyCode.from_vk(106), 'keypaddivide': KeyCode.from_vk(111),
            
            # Punctuation and symbols
            'comma': KeyCode.from_vk(188), ',': KeyCode.from_vk(188),
            'period': KeyCode.from_vk(190), '.': KeyCode.from_vk(190),
            'semicolon': KeyCode.from_vk(186), ';': KeyCode.from_vk(186),  # Use virtual key code for semicolon
            'colon': ':', ':': ':',
            'slash': KeyCode.from_vk(191), '/': KeyCode.from_vk(191),
            'backslash': '\\', '\\': '\\',
            'minus': '-', '-': '-',
            'equals': '=', '=': '=',
            'plus': '+', '+': '+',
            'underscore': '_', '_': '_',
            'bracket_left': KeyCode.from_vk(219), '[': KeyCode.from_vk(219), 'leftbracket': KeyCode.from_vk(219),
            'bracket_right': KeyCode.from_vk(221), ']': KeyCode.from_vk(221), 'rightbracket': KeyCode.from_vk(221),
            'brace_left': '{', '{': '{',
            'brace_right': '}', '}': '}',
            'pipe': '|', '|': '|',
            'tilde': '~', '~': '~',
            "backquote": "'", "'": "'",  # In Rust keys.cfg, 'backquote' means single quote/apostrophe
            'backtick': '`', '`': '`',
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
    
    def is_rust_focused(self):
        """Check if RustClient.exe is the currently focused window"""
        if not WIN32_AVAILABLE:
            logger.warning("Focus checking not available - win32gui not installed")
            return True  # Allow execution if focus checking is not available
        
        try:
            # Get the handle of the currently focused window
            focused_hwnd = win32gui.GetForegroundWindow()
            if focused_hwnd == 0:
                logger.warning("No focused window found")
                return False
            
            # Get the process ID of the focused window
            _, focused_pid = win32process.GetWindowThreadProcessId(focused_hwnd)
            
            # Get the window title
            window_title = win32gui.GetWindowText(focused_hwnd)
            
            # Check if the window title contains "Rust"
            if "Rust" in window_title:
                logger.debug(f"Rust window focused: {window_title}")
                return True
            
            # Additional check: try to get the process name
            try:
                import psutil
                process = psutil.Process(focused_pid)
                process_name = process.name()
                if process_name.lower() == "rustclient.exe":
                    logger.debug(f"RustClient.exe process focused: {process_name}")
                    return True
            except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                # psutil not available or process access denied, fall back to window title only
                pass
            
            logger.debug(f"Non-Rust window focused: {window_title} (PID: {focused_pid})")
            return False
            
        except Exception as e:
            logger.error(f"Error checking window focus: {e}")
            return True  # Allow execution if focus check fails
    
    def single(self, key):
        """Simulate a single key press"""
        # Check if Rust is focused before executing
        if not self.is_rust_focused():
            logger.warning(f"Skipping key press '{key}' - Rust is not focused")
            return
        
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            # For numpad keys, ensure NumLock is on
            if key.startswith('keypad'):
                self._ensure_numlock_on()
            
            self.controller.press(normalized_key)
            time.sleep(0.005)  # Hold for 5ms (reduced from 50ms for speed)
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
        # Check if Rust is focused before executing
        if not self.is_rust_focused():
            logger.warning(f"Skipping key combination '{'+'.join(keys)}' - Rust is not focused")
            return
        
        import time
        combo_start = time.time()
        
        normalized_keys = []
        normalize_start = time.time()
        for key in keys:
            normalized_key = self.normalize_key(key)
            if not normalized_key:
                raise ValueError(f"Invalid key: {key}")
            normalized_keys.append(normalized_key)
        normalize_time = time.time() - normalize_start
        
        try:
            # Press all keys down
            press_start = time.time()
            for key in normalized_keys:
                self.controller.press(key)
            press_time = time.time() - press_start
            
            # Hold for a minimal moment (reduced from 0.1s to 0.01s for speed)
            hold_start = time.time()
            time.sleep(0.02)
            hold_time = time.time() - hold_start
            
            # Release in reverse order
            release_start = time.time()
            for key in reversed(normalized_keys):
                self.controller.release(key)
            release_time = time.time() - release_start
            
            total_time = time.time() - combo_start
            
            # Log timing details for debugging (only if significant)
            if total_time > 0.02:  # Only log if combo takes more than 20ms (reduced threshold)
                print(f"Combo timing - Normalize: {normalize_time:.4f}s, Press: {press_time:.4f}s, Hold: {hold_time:.4f}s, Release: {release_time:.4f}s, Total: {total_time:.4f}s")
            
        except Exception as e:
            total_time = time.time() - combo_start
            logger.error(f"[ERROR] Combo failed after {total_time:.4f}s: {str(e)}")
            raise Exception(f"Failed to send combination {'+'.join(keys)}: {str(e)}")
    
    def down(self, key):
        """Simulate key down"""
        # Check if Rust is focused before executing
        if not self.is_rust_focused():
            logger.warning(f"Skipping key down '{key}' - Rust is not focused")
            return
        
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            self.controller.press(normalized_key)
        except Exception as e:
            raise Exception(f"Failed to send key down {normalized_key}: {str(e)}")
    
    def up(self, key):
        """Simulate key up"""
        # Check if Rust is focused before executing
        if not self.is_rust_focused():
            logger.warning(f"Skipping key up '{key}' - Rust is not focused")
            return
        
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            raise ValueError(f"Invalid key: {key}")
        
        try:
            self.controller.release(normalized_key)
        except Exception as e:
            raise Exception(f"Failed to send key up {normalized_key}: {str(e)}")
    
    def type_string(self, text):
        """Type a string"""
        # Check if Rust is focused before executing
        if not self.is_rust_focused():
            logger.warning(f"Skipping string typing '{text}' - Rust is not focused")
            return
        
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
        
        # Anti-AFK feature
        self.anti_afk_enabled = False
        self.anti_afk_thread = None
        self.anti_afk_stop_event = threading.Event()
        
        # Continuous stack inventory feature
        self.continuous_stack_enabled = False
        self.continuous_stack_thread = None
        self.continuous_stack_stop_event = threading.Event()
        
        # Load key combinations into cache
        self._load_key_combinations()
        logger.info("=== KeyboardManager Initialization Complete ===")
    
    def _load_key_combinations(self):
        """Load all key combinations into cache for faster lookup"""
        logger = logging.getLogger(__name__)
        logger.info("Loading key combinations into cache...")
        
        # Clear the cache first
        self._key_combo_cache.clear()
        
        # Populate cache from binds_manager's key_combinations for regular binds
        for i, combo in enumerate(self.binds_manager.key_combinations):
            self._key_combo_cache[i] = combo.split('+')
        
        # Now populate cache for dynamic binds from the binds_manager's data
        # For dynamic binds, we need to use the correct key combinations based on command type
        # Define the key combinations for each command type (fixed combinations as specified)
        dynamic_key_combinations = {
            "chat_say": "keypaddivide+keypadplus+keypad4+keypad7+period",
            "chat_teamsay": "keypaddivide+keypadplus+keypad4+keypad7+leftbracket",
            "client_connect": "keypaddivide+keypadplus+keypad4+keypad7+rightbracket",
            "respawn": "keypaddivide+keypadplus+keypad4+keypad8+keypad9"
        }
        
        # Populate cache for existing dynamic binds
        for bind_key, bind_index in self.binds_manager.dynamic_binds.items():
            command_type = bind_key.split(":", 1)[0]
            if command_type in dynamic_key_combinations:
                key_combo = dynamic_key_combinations[command_type]
                self._key_combo_cache[bind_index] = key_combo.split('+')
        
        # For empty dynamic bind slots, use the static key combinations
        for bind_index in range(self.binds_manager.CHAT_BINDS_START, self.binds_manager.CHAT_BINDS_END + 1):
            if bind_index not in self.binds_manager.dynamic_binds.values():
                if bind_index < len(self.binds_manager.key_combinations):
                    key_combo = self.binds_manager.key_combinations[bind_index]
                    self._key_combo_cache[bind_index] = key_combo.split('+')
        
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
    
    def _refresh_dynamic_bind_cache(self):
        """Refresh the cache for dynamic binds only"""
        logger.info("Refreshing dynamic bind cache...")
        
        # Update cache for existing dynamic binds using unique key combinations
        for bind_key, bind_index in self.binds_manager.dynamic_binds.items():
            command_type = bind_key.split(":", 1)[0]
            # Use the unique key combination for this bind index
            if bind_index < len(self.binds_manager.key_combinations):
                key_combo = self.binds_manager.key_combinations[bind_index]
                self._key_combo_cache[bind_index] = key_combo.split('+')
            else:
                logger.warning(f"Bind index {bind_index} exceeds available key combinations")
        
        logger.info(f"Refreshed cache for {len(self.binds_manager.dynamic_binds)} dynamic binds")
    
    def get_key_combo_for_bind(self, bind_index: int) -> Optional[List[str]]:
        """Get the key combination for a specific bind index"""
        return self._key_combo_cache.get(bind_index)
    
    def trigger_bind(self, bind_index: int) -> bool:
        """Trigger a bind by its index"""
        import time
        with self._lock:
            try:
                cache_start = time.time()
                key_combo = self.get_key_combo_for_bind(bind_index)
                cache_time = time.time() - cache_start
                
                if not key_combo:
                    logger.error(f"[ERROR] No key combination found for bind index {bind_index}")
                    return False
                
                combo_start = time.time()
                self.keyboard_simulator.combo(key_combo)
                combo_time = time.time() - combo_start
                
                # Log timing details for debugging
                if cache_time > 0.001 or combo_time > 0.01:  # Only log if there's significant time
                    print(f"Bind {bind_index} timing - Cache: {cache_time:.4f}s, Combo: {combo_time:.4f}s")
                
                return True
                
            except Exception as e:
                logger.error(f"[ERROR] Error triggering bind {bind_index}: {e}")
                return False
    
    def craft_item(self, item_id: int) -> bool:
        """Craft an item by its ID"""
        try:
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            
            if not bind_info:
                logger.warning(f"No bind found for item ID {item_id}")
                return False
            
            craft_bind_index, _ = bind_info
            return self.trigger_bind(craft_bind_index)
            
        except Exception as e:
            logger.error(f"Error crafting item {item_id}: {e}")
            return False
    
    def bulk_craft_item(self, item_id: int, iterations: int = 1) -> bool:
        """Craft an item multiple times rapidly"""
        import time
        start_time = time.time()
        
        try:
            bind_info_start = time.time()
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            bind_info_time = time.time() - bind_info_start
            
            if not bind_info:
                logger.warning(f"No bind found for item ID {item_id}")
                return False
            
            craft_bind_index, _ = bind_info
            
            logger.info(f"Starting bulk craft for item {item_id}: {iterations} iterations")
            logger.info(f"Bind lookup took: {bind_info_time:.4f}s")
            
            # Trigger the bind multiple times rapidly
            bind_trigger_start = time.time()
            for i in range(iterations):
                iteration_start = time.time()
                if not self.trigger_bind(craft_bind_index):
                    logger.error(f"Failed to trigger bind on iteration {i}")
                    return False
                iteration_time = time.time() - iteration_start
                if i % 10 == 0:  # Log every 10th iteration
                    logger.info(f"Iteration {i}: {iteration_time:.4f}s")
                # No delay - maximum speed execution
            
            bind_trigger_time = time.time() - bind_trigger_start
            total_time = time.time() - start_time
            
            logger.info(f"Bulk craft completed successfully: {iterations} iterations")
            logger.info(f"Total time: {total_time:.4f}s")
            logger.info(f"Bind lookup: {bind_info_time:.4f}s ({bind_info_time/total_time*100:.1f}%)")
            logger.info(f"Bind triggering: {bind_trigger_time:.4f}s ({bind_trigger_time/total_time*100:.1f}%)")
            logger.info(f"Average per iteration: {bind_trigger_time/iterations:.4f}s")
            
            return True
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error bulk crafting item {item_id} after {total_time:.4f}s: {e}")
            return False
    
    def cancel_craft_item(self, item_id: int) -> bool:
        """Cancel crafting an item by its ID"""
        try:
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            if not bind_info:
                logger.warning(f"No bind found for item ID {item_id}")
                return False
            
            _, cancel_bind_index = bind_info
            return self.trigger_bind(cancel_bind_index)
            
        except Exception as e:
            logger.error(f"Error canceling craft for item {item_id}: {e}")
            return False
    
    def bulk_cancel_craft_item(self, item_id: int, iterations: int = 1) -> bool:
        """Cancel crafting an item multiple times rapidly"""
        import time
        start_time = time.time()
        
        try:
            bind_info_start = time.time()
            bind_info = self.binds_manager.get_item_bind_info(item_id)
            bind_info_time = time.time() - bind_info_start
            
            if not bind_info:
                logger.warning(f"No bind found for item ID {item_id}")
                return False
            
            _, cancel_bind_index = bind_info
            
            logger.info(f"Starting bulk cancel craft for item {item_id}: {iterations} iterations")
            logger.info(f"Bind lookup took: {bind_info_time:.4f}s")
            
            # Trigger the bind multiple times rapidly
            bind_trigger_start = time.time()
            for i in range(iterations):
                iteration_start = time.time()
                if not self.trigger_bind(cancel_bind_index):
                    logger.error(f"Failed to trigger cancel bind on iteration {i}")
                    return False
                iteration_time = time.time() - iteration_start
                if i % 10 == 0:  # Log every 10th iteration
                    logger.info(f"Iteration {i}: {iteration_time:.4f}s")
                # No delay - maximum speed execution
            
            bind_trigger_time = time.time() - bind_trigger_start
            total_time = time.time() - start_time
            
            logger.info(f"Bulk cancel craft completed successfully: {iterations} iterations")
            logger.info(f"Total time: {total_time:.4f}s")
            logger.info(f"Bind lookup: {bind_info_time:.4f}s ({bind_info_time/total_time*100:.1f}%)")
            logger.info(f"Bind triggering: {bind_trigger_time:.4f}s ({bind_trigger_time/total_time*100:.1f}%)")
            logger.info(f"Average per iteration: {bind_trigger_time/iterations:.4f}s")
            
            return True
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error bulk canceling craft for item {item_id} after {total_time:.4f}s: {e}")
            return False
    
    def trigger_api_command(self, command_name: str) -> bool:
        """Trigger an API command by name"""
        api_commands = {
            "kill": 3000,
            "respawn": 3001,
            "autorun": 3002,
            "autorun_jump": 3003,
            "crouch_attack": 3004,
            "quit_game": 3005,
            "disconnect": 3006,
            "lookat_radius_20": 3007,
            "lookat_radius_0": 3008,
            "audio_voices_0": 3009,
            "audio_voices_25": 3010,
            "audio_voices_50": 3011,
            "audio_voices_75": 3012,
            "audio_voices_100": 3013,
            "audio_master_0": 3014,
            "audio_master_25": 3015,
            "audio_master_50": 3016,
            "audio_master_75": 3017,
            "audio_master_100": 3018,
            "hud_off": 3019,
            "hud_on": 3020,
            "gesture_wave": 3021,
            "gesture_victory": 3022,
            "gesture_shrug": 3023,
            "gesture_thumbsup": 3024,
            "gesture_hurry": 3025,
            "gesture_ok": 3026,
            "gesture_thumbsdown": 3027,
            "gesture_clap": 3028,
            "gesture_point": 3029,
            "gesture_friendly": 3030,
            "gesture_cabbagepatch": 3031,
            "gesture_twist": 3032,
            "gesture_raisetheroof": 3033,
            "gesture_beatchest": 3034,
            "gesture_throatcut": 3035,
            "gesture_fingergun": 3036,
            "gesture_shush": 3037,
            "gesture_shush_vocal": 3038,
            "gesture_watchingyou": 3039,
            "gesture_loser": 3040,
            "gesture_nono": 3041,
            "gesture_knucklescrack": 3042,
            "gesture_rps": 3043,
            "noclip_true": 3044,
            "noclip_false": 3045,
            "global_god_true": 3046,
            "global_god_false": 3047,
            "env_time_0": 3048,
            "env_time_4": 3049,
            "env_time_8": 3050,
            "env_time_12": 3051,
            "env_time_16": 3052,
            "env_time_20": 3053,
            "env_time_24": 3054,
            "teleport2marker": 3055,
            "combatlog": 3056,
            "console_clear": 3057,
            "consoletoggle": 3058,
        }
        
        bind_index = api_commands.get(command_name)
        if bind_index is None:
            logger.warning(f"Unknown API command: {command_name}")
            return False
        
        return self.trigger_bind(bind_index)
    
    def trigger_chat_command(self, command_name: str, **kwargs) -> bool:
        """Trigger a chat/connection command by name with dynamic bind management"""
        try:
            # Get the string value from kwargs
            string_value = kwargs.get('string_value', '')
            if not string_value:
                logger.warning(f"No string value provided for chat command: {command_name}")
                return False
            
            # Get or create a dynamic bind for this string
            bind_key = f"{command_name}:{string_value}"
            was_new_bind = bind_key not in self.binds_manager.dynamic_binds
            bind_index = self.binds_manager.get_or_create_dynamic_bind(command_name, string_value)
            
            # Check if we need to reload the binds (new bind was created)
            if was_new_bind:
                # Regenerate the keys.cfg file with the new dynamic bind
                logger.info(f"Regenerating keys.cfg with new dynamic bind {bind_index}")
                if not self.binds_manager.write_keys_cfg_with_sections_protected():
                    logger.error("Failed to regenerate keys.cfg with dynamic bind")
                    return False
                
                # Refresh the keyboard manager's cache to include the new bind
                logger.info("Refreshing keyboard manager cache for new dynamic bind")
                self._refresh_dynamic_bind_cache()
                
                # Reload the binds in Rust
                logger.info("Reloading binds in Rust...")
                if not self.reload_binds():
                    logger.error("Failed to reload binds in Rust")
                    return False
            
            # Trigger the bind
            result = self.trigger_bind(bind_index)
            return result
            
        except Exception as e:
            logger.error(f"Error triggering chat command {command_name}: {e}")
            return False
    
    def stack_inventory(self, iterations: int = 80) -> bool:
        """Stack inventory by triggering the stack inventory binds"""
        try:
            # These are the item IDs for the stack inventory items
            stack_items = [-97956382, 1390353317, 15388698]  # TC, Wood, Stone
            
            # Only log start and end, not every iteration
            logger.info(f"Starting stack inventory: {iterations} iterations")
            for i in range(iterations):
                for item_id in stack_items:
                    if not self.craft_item(item_id):
                        logger.error(f"Failed to stack item {item_id} on iteration {i}")
                        return False
                # No delay - maximum speed execution
            
            logger.info("Stack inventory completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stacking inventory: {e}")
            return False
    
    def cancel_stack_inventory(self, iterations: int = 80) -> bool:
        """Cancel stack inventory by triggering the cancel binds"""
        try:
            # These are the item IDs for the stack inventory items
            stack_items = [-97956382, 1390353317, 15388698]  # TC, Wood, Stone
            
            # Only log start and end, not every iteration
            logger.info(f"Starting cancel stack inventory: {iterations} iterations")
            for i in range(iterations):
                for item_id in stack_items:
                    if not self.cancel_craft_item(item_id):
                        logger.error(f"Failed to cancel stack item {item_id} on iteration {i}")
                        return False
                # No delay - maximum speed execution
            
            logger.info("Cancel stack inventory completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling stack inventory: {e}")
            return False
    
    def stack_inventory_continuous(self, enable: bool) -> bool:
        """Enable or disable continuous stack inventory"""
        if enable:
            if self.continuous_stack_enabled:
                logger.warning("Continuous stack inventory is already running")
                return False
            
            logger.info("Starting continuous stack inventory...")
            self.continuous_stack_enabled = True
            self.continuous_stack_stop_event.clear()
            self.continuous_stack_thread = threading.Thread(target=self._continuous_stack_inventory_loop, daemon=True)
            self.continuous_stack_thread.start()
            return True
        else:
            if not self.continuous_stack_enabled:
                logger.warning("Continuous stack inventory is not running")
                return False
            
            logger.info("Stopping continuous stack inventory...")
            self.continuous_stack_enabled = False
            self.continuous_stack_stop_event.set()
            if self.continuous_stack_thread and self.continuous_stack_thread.is_alive():
                self.continuous_stack_thread.join(timeout=2.0)
            return True
    
    def _continuous_stack_inventory_loop(self):
        """Background thread for continuous stack inventory operations"""
        logger.info("Continuous stack inventory loop started")
        
        while self.continuous_stack_enabled and not self.continuous_stack_stop_event.is_set():
            try:
                # Stack inventory (80 iterations)
                logger.info("Executing stack inventory (80 iterations)")
                self.stack_inventory(iterations=80)
                
                # Wait 10 seconds
                logger.info("Waiting 10 seconds before canceling...")
                for i in range(10):
                    if self.continuous_stack_stop_event.is_set():
                        break
                    time.sleep(1)
                
                if self.continuous_stack_stop_event.is_set():
                    break
                
                # Cancel 1x of each stacking
                logger.info("Canceling 1x of each stacking")
                self.cancel_stack_inventory(iterations=1)
                
                # Wait a moment before next cycle
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in continuous stack inventory loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info("Continuous stack inventory loop stopped")
    
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
        """Reload binds by pressing F1, typing 'exec keys.cfg', pressing enter, then pressing F1"""
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
            
            # Press F1 to close console
            self.keyboard_simulator.single('f1')
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
    
    def start_anti_afk(self) -> bool:
        """Start the anti-AFK feature"""
        if self.anti_afk_enabled:
            logger.warning("Anti-AFK is already running")
            return False
        
        try:
            self.anti_afk_enabled = True
            self.anti_afk_stop_event.clear()
            self.anti_afk_thread = threading.Thread(target=self._anti_afk_loop, daemon=True)
            self.anti_afk_thread.start()
            logger.info("Anti-AFK started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start anti-AFK: {e}")
            self.anti_afk_enabled = False
            return False
    
    def stop_anti_afk(self) -> bool:
        """Stop the anti-AFK feature"""
        if not self.anti_afk_enabled:
            logger.warning("Anti-AFK is not running")
            return False
        
        try:
            self.anti_afk_enabled = False
            self.anti_afk_stop_event.set()
            if self.anti_afk_thread and self.anti_afk_thread.is_alive():
                self.anti_afk_thread.join(timeout=5)
            logger.info("Anti-AFK stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stop anti-AFK: {e}")
            return False
    
    def is_anti_afk_running(self) -> bool:
        """Check if anti-AFK is currently running"""
        return self.anti_afk_enabled and self.anti_afk_thread and self.anti_afk_thread.is_alive()
    
    def _anti_afk_loop(self):
        """Anti-AFK loop that runs in background thread"""
        logger.info("Anti-AFK loop started")
        
        while not self.anti_afk_stop_event.is_set():
            try:
                # Hold W down (move forward) for 1 second
                logger.info("Anti-AFK: Holding W for 1 second")
                self.keyboard_simulator.down('w')
                
                # Wait 1 second while holding W
                if self.anti_afk_stop_event.wait(1):
                    # If stopping, release W before breaking
                    self.keyboard_simulator.up('w')
                    break
                
                # Release W
                self.keyboard_simulator.up('w')
                
                # Hold S down (move backward) for 1 second
                logger.info("Anti-AFK: Holding S for 1 second")
                self.keyboard_simulator.down('s')
                
                # Wait 1 second while holding S
                if self.anti_afk_stop_event.wait(1):
                    # If stopping, release S before breaking
                    self.keyboard_simulator.up('s')
                    break
                
                # Release S
                self.keyboard_simulator.up('s')
                
                # Wait 1 minute (60 seconds) before next cycle
                if self.anti_afk_stop_event.wait(60):
                    break
                    
            except Exception as e:
                logger.error(f"Error in anti-AFK loop: {e}")
                # Make sure to release any held keys in case of error
                try:
                    self.keyboard_simulator.up('w')
                    self.keyboard_simulator.up('s')
                except:
                    pass
                # Wait a bit before retrying
                if self.anti_afk_stop_event.wait(10):
                    break
        
        logger.info("Anti-AFK loop stopped")


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
