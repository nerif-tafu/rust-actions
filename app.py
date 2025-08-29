from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import time
from pathlib import Path
from steam_manager import steam_manager
from keyboard_manager import KeyboardManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class RustGameController:
    """Controller class for Rust game actions"""
    
    def __init__(self):
        self.game_connected = False
        self.current_server = None
        # Initialize the keyboard manager for actual keypress functionality
        try:
            # Force reload of keyboard_manager module to ensure we get the latest code
            import importlib
            import keyboard_manager
            importlib.reload(keyboard_manager)
            
            self.keyboard_manager = keyboard_manager.KeyboardManager()
            logger.info("KeyboardManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize KeyboardManager: {e}")
            self.keyboard_manager = None
    
    def craft_by_id(self, item_id: str, quantity: int) -> dict:
        """Craft an item by ID with given quantity"""
        import time
        api_start = time.time()
        logger.info(f"Crafting item ID {item_id} with quantity {quantity}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Convert item_id to integer
            convert_start = time.time()
            item_id_int = int(item_id)
            convert_time = time.time() - convert_start
            
            # Use bulk crafting for better performance
            bulk_start = time.time()
            success = self.keyboard_manager.bulk_craft_item(item_id_int, quantity)
            bulk_time = time.time() - bulk_start
            
            total_time = time.time() - api_start
            
            logger.info(f"API craft_by_id timing - Convert: {convert_time:.4f}s, Bulk: {bulk_time:.4f}s, Total: {total_time:.4f}s")
            
            return {
                "success": success,
                "action": "craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Bulk craft operation {'completed successfully' if success else 'failed'} for item ID {item_id} ({quantity} items) in {total_time:.4f}s"
            }
        except ValueError:
            total_time = time.time() - api_start
            logger.error(f"ValueError in craft_by_id after {total_time:.4f}s")
            return {
                "success": False,
                "action": "craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Invalid item ID: {item_id} (must be a number)"
            }
        except Exception as e:
            total_time = time.time() - api_start
            logger.error(f"Error crafting item {item_id} after {total_time:.4f}s: {e}")
            return {
                "success": False,
                "action": "craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Error: {str(e)}"
        }
    
    def craft_by_name(self, item_name: str, quantity: int) -> dict:
        """Craft an item by name with given quantity"""
        logger.info(f"Crafting item {item_name} with quantity {quantity} (type: {type(quantity)})")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Find the item by name in the binds manager
            item_found = None
            for item in self.keyboard_manager.binds_manager.craftable_items:
                if item["name"].lower() == item_name.lower():
                    item_found = item
                    break
            
            if not item_found:
                return {
                    "success": False,
                    "action": "craft_by_name",
                    "item_name": item_name,
                    "quantity": quantity,
                    "message": f"Item '{item_name}' not found in craftable items"
                }
            
            # DEBUG: Log the item details
            logger.info(f"DEBUG: Found item '{item_name}' with numericId: {item_found['numericId']} (type: {type(item_found['numericId'])})")
            
            # Convert quantity to integer and use bulk crafting for better performance
            quantity_int = int(quantity)
            item_id_int = int(item_found["numericId"])
            
            # Use bulk crafting for better performance
            success = self.keyboard_manager.bulk_craft_item(item_id_int, quantity_int)
            
            return {
                "success": success,
                "action": "craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Bulk craft operation {'completed successfully' if success else 'failed'} for {item_name} ({quantity} items)"
            }
        except ValueError as e:
            logger.error(f"Error crafting item {item_name}: Invalid numericId format - {e}")
            return {
                "success": False,
                "action": "craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Error: Invalid item ID format for '{item_name}'"
            }
        except Exception as e:
            logger.error(f"Error crafting item {item_name}: {e}")
            return {
                "success": False,
                "action": "craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Error: {str(e)}"
        }
    
    def cancel_craft_by_id(self, item_id: str, quantity: int) -> dict:
        """Cancel crafting an item by ID with given quantity"""
        logger.info(f"Canceling craft of item ID {item_id} with quantity {quantity}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "cancel_craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Convert item_id to integer
            item_id_int = int(item_id)
            
            # Use bulk cancel for better performance
            success = self.keyboard_manager.bulk_cancel_craft_item(item_id_int, quantity)
            
            return {
                "success": success,
                "action": "cancel_craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Bulk cancel operation {'completed successfully' if success else 'failed'} for item ID {item_id} ({quantity} items)"
            }
        except ValueError:
            return {
                "success": False,
                "action": "cancel_craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Invalid item ID: {item_id} (must be a number)"
            }
        except Exception as e:
            logger.error(f"Error canceling craft item {item_id}: {e}")
            return {
                "success": False,
                "action": "cancel_craft_by_id",
                "item_id": item_id,
                "quantity": quantity,
                "message": f"Error: {str(e)}"
        }
    
    def cancel_craft_by_name(self, item_name: str, quantity: int) -> dict:
        """Cancel crafting an item by name with given quantity"""
        logger.info(f"Canceling craft of item {item_name} with quantity {quantity}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "cancel_craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Find the item by name in the binds manager
            item_found = None
            for item in self.keyboard_manager.binds_manager.craftable_items:
                if item["name"].lower() == item_name.lower():
                    item_found = item
                    break
            
            if not item_found:
                return {
                    "success": False,
                    "action": "cancel_craft_by_name",
                    "item_name": item_name,
                    "quantity": quantity,
                    "message": f"Item '{item_name}' not found in craftable items"
                }
            
            # Convert quantity to integer and use bulk cancel for better performance
            quantity_int = int(quantity)
            item_id_int = int(item_found["numericId"])
            
            # Use bulk cancel for better performance
            success = self.keyboard_manager.bulk_cancel_craft_item(item_id_int, quantity_int)
            
            return {
                "success": success,
                "action": "cancel_craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Bulk cancel operation {'completed successfully' if success else 'failed'} for {item_name} ({quantity} items)"
            }
        except ValueError as e:
            logger.error(f"Error canceling craft item {item_name}: Invalid numericId format - {e}")
            return {
                "success": False,
                "action": "cancel_craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Error: Invalid item ID format for '{item_name}'"
            }
        except Exception as e:
            logger.error(f"Error canceling craft item {item_name}: {e}")
            return {
                "success": False,
                "action": "cancel_craft_by_name",
                "item_name": item_name,
                "quantity": quantity,
                "message": f"Error: {str(e)}"
        }
    
    def suicide(self) -> dict:
        """Kill the player character"""
        logger.info("Executing suicide command")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "suicide",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("kill")
            return {
                "success": success,
                "action": "suicide",
                "message": "Suicide command executed successfully" if success else "Failed to execute suicide command"
            }
        except Exception as e:
            logger.error(f"Error executing suicide: {e}")
            return {
                "success": False,
                "action": "suicide",
                "message": f"Error: {str(e)}"
        }
    
    def respawn(self, spawn_id: str = None) -> dict:
        """Respawn player with optional spawn ID"""
        logger.info(f"Respawning with spawn ID: {spawn_id}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "respawn",
                "spawn_id": spawn_id,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Check if spawn_id has a valid value (not None and not empty string)
            if spawn_id is not None and str(spawn_id).strip():
                # Use dynamic bind system for respawn_sleepingbag command (kill + respawn_sleepingbag <id>)
                spawn_id_str = str(spawn_id).strip()
                # First kill the player
                success = self.keyboard_manager.trigger_api_command("kill")
                if success:
                    time.sleep(1.0)  # Wait 1 second between kill and respawn
                    # Then respawn at specific sleeping bag
                    success = self.keyboard_manager.trigger_chat_command("respawn_sleepingbag", string_value=spawn_id_str)
                return {
                    "success": success,
                    "action": "respawn_sleepingbag",
                    "spawn_id": spawn_id,
                    "message": f"Respawn sleeping bag command executed successfully" if success else "Failed to execute respawn sleeping bag command"
                }
            else:
                # Use static bind system for regular respawn (kill + respawn)
                success = self.keyboard_manager.trigger_api_command("kill")
                if success:
                    time.sleep(0.5)  # Wait 0.5 seconds between kill and respawn
                    success = self.keyboard_manager.trigger_api_command("respawn")
                return {
                    "success": success,
                    "action": "respawn",
                    "spawn_id": None,
                    "message": f"Respawn command executed successfully" if success else "Failed to execute respawn command"
                }
        except Exception as e:
            logger.error(f"Error executing respawn: {e}")
            return {
                "success": False,
                "action": "respawn",
                "spawn_id": spawn_id,
                "message": f"Error: {str(e)}"
            }
    
    def kill_only(self) -> dict:
        """Kill the player character only"""
        logger.info("Killing player character")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "kill_only",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("kill")
            return {
                "success": success,
                "action": "kill_only",
                "message": "Kill command executed successfully" if success else "Failed to execute kill command"
            }
        except Exception as e:
            logger.error(f"Error executing kill: {e}")
            return {
                "success": False,
                "action": "kill_only",
                "message": f"Error: {str(e)}"
            }
    
    def respawn_only(self) -> dict:
        """Respawn the player character only (without killing first)"""
        logger.info("Respawning player character")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "respawn_only",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("respawn")
            return {
                "success": success,
                "action": "respawn_only",
                "message": "Respawn command executed successfully" if success else "Failed to execute respawn command"
            }
        except Exception as e:
            logger.error(f"Error executing respawn: {e}")
            return {
                "success": False,
                "action": "respawn_only",
                "message": f"Error: {str(e)}"
            }
    
    def respawn_random(self) -> dict:
        """Kill and respawn the player character (random spawn)"""
        logger.info("Killing and respawning player character (random spawn)")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "respawn_random",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # First kill the player
            success = self.keyboard_manager.trigger_api_command("kill")
            if success:
                time.sleep(0.1)  # Small delay between kill and respawn
                # Then respawn
                success = self.keyboard_manager.trigger_api_command("respawn")
            return {
                "success": success,
                "action": "respawn_random",
                "message": "Kill and respawn command executed successfully" if success else "Failed to execute kill and respawn command"
            }
        except Exception as e:
            logger.error(f"Error executing kill and respawn: {e}")
            return {
                "success": False,
                "action": "respawn_random",
                "message": f"Error: {str(e)}"
            }
    
    def respawn_bed(self, spawn_id: str) -> dict:
        """Kill and respawn at specific sleeping bag"""
        logger.info(f"Killing and respawning at sleeping bag: {spawn_id}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "respawn_bed",
                "spawn_id": spawn_id,
                "message": "KeyboardManager not initialized"
                }
        
        if not spawn_id or not str(spawn_id).strip():
            return {
                "success": False,
                "action": "respawn_bed",
                "spawn_id": spawn_id,
                "message": "Spawn ID is required for respawn bed"
            }
        
        try:
            spawn_id_str = str(spawn_id).strip()
            # First kill the player
            success = self.keyboard_manager.trigger_api_command("kill")
            if success:
                time.sleep(0.1)  # Small delay between kill and respawn
                # Then respawn at specific sleeping bag
                success = self.keyboard_manager.trigger_chat_command("respawn_sleepingbag", string_value=spawn_id_str)
            return {
                "success": success,
                "action": "respawn_bed",
                "spawn_id": spawn_id,
                "message": f"Kill and respawn bed command executed successfully" if success else "Failed to execute kill and respawn bed command"
            }
        except Exception as e:
            logger.error(f"Error executing kill and respawn bed: {e}")
            return {
                "success": False,
                "action": "respawn_bed",
                "spawn_id": spawn_id,
                "message": f"Error: {str(e)}"
        }
    
    def auto_run(self) -> dict:
        """Enable auto run"""
        logger.info("Enabling auto run")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "auto_run",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("autorun")
            return {
                "success": success,
                "action": "auto_run",
                "message": "Auto run command executed successfully" if success else "Failed to execute auto run command"
            }
        except Exception as e:
            logger.error(f"Error executing auto run: {e}")
            return {
                "success": False,
                "action": "auto_run",
                "message": f"Error: {str(e)}"
        }
    
    def auto_run_jump(self) -> dict:
        """Enable auto run and jump"""
        logger.info("Enabling auto run and jump")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "auto_run_jump",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("autorun_jump")
            return {
                "success": success,
                "action": "auto_run_jump",
                "message": "Auto run and jump command executed successfully" if success else "Failed to execute auto run and jump command"
            }
        except Exception as e:
            logger.error(f"Error executing auto run and jump: {e}")
            return {
                "success": False,
                "action": "auto_run_jump",
                "message": f"Error: {str(e)}"
        }
    
    def auto_crouch_attack(self) -> dict:
        """Enable auto crouch and attack"""
        logger.info("Enabling auto crouch and attack")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "auto_crouch_attack",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("crouch_attack")
            return {
                "success": success,
                "action": "auto_crouch_attack",
                "message": "Auto crouch and attack command executed successfully" if success else "Failed to execute auto crouch and attack command"
            }
        except Exception as e:
            logger.error(f"Error executing auto crouch and attack: {e}")
            return {
                "success": False,
                "action": "auto_crouch_attack",
                "message": f"Error: {str(e)}"
            }
    
    def gesture(self, gesture_name: str) -> dict:
        """Perform a gesture/emote"""
        logger.info(f"Performing gesture: {gesture_name}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "gesture",
                "gesture_name": gesture_name,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command(f"gesture_{gesture_name}")
            return {
                "success": success,
                "action": "gesture",
                "gesture_name": gesture_name,
                "message": f"Gesture '{gesture_name}' executed successfully" if success else f"Failed to execute gesture '{gesture_name}'"
            }
        except Exception as e:
            logger.error(f"Error executing gesture {gesture_name}: {e}")
            return {
                "success": False,
                "action": "gesture",
                "gesture_name": gesture_name,
                "message": f"Error: {str(e)}"
            }
    
    def noclip_toggle(self, enable: bool) -> dict:
        """Toggle noclip on/off"""
        logger.info(f"Setting noclip to: {enable}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "noclip_toggle",
                "enable": enable,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            command_name = "noclip_true" if enable else "noclip_false"
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "noclip_toggle",
                "enable": enable,
                "message": f"Noclip {'enabled' if enable else 'disabled'}" if success else "Failed to toggle noclip"
            }
        except Exception as e:
            logger.error(f"Error toggling noclip: {e}")
            return {
                "success": False,
                "action": "noclip_toggle",
                "enable": enable,
                "message": f"Error: {str(e)}"
            }
    
    def god_mode_toggle(self, enable: bool) -> dict:
        """Toggle god mode on/off"""
        logger.info(f"Setting god mode to: {enable}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "god_mode_toggle",
                "enable": enable,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            command_name = "global_god_true" if enable else "global_god_false"
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "god_mode_toggle",
                "enable": enable,
                "message": f"God mode {'enabled' if enable else 'disabled'}" if success else "Failed to toggle god mode"
            }
        except Exception as e:
            logger.error(f"Error toggling god mode: {e}")
            return {
                "success": False,
                "action": "god_mode_toggle",
                "enable": enable,
                "message": f"Error: {str(e)}"
            }
    
    def set_time(self, time_hour: int) -> dict:
        """Set time of day (0-24)"""
        logger.info(f"Setting time to: {time_hour}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "set_time",
                "time_hour": time_hour,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Map time to command names
            time_commands = {
                0: "env_time_0", 4: "env_time_4", 8: "env_time_8", 12: "env_time_12",
                16: "env_time_16", 20: "env_time_20", 24: "env_time_24"
            }
            
            command_name = time_commands.get(time_hour)
            if command_name is None:
                return {
                    "success": False,
                    "action": "set_time",
                    "time_hour": time_hour,
                    "message": f"Invalid time: {time_hour}. Must be one of: 0, 4, 8, 12, 16, 20, 24"
                }
            
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "set_time",
                "time_hour": time_hour,
                "message": f"Time set to {time_hour}:00" if success else "Failed to set time"
            }
        except Exception as e:
            logger.error(f"Error setting time: {e}")
            return {
                "success": False,
                "action": "set_time",
                "time_hour": time_hour,
                "message": f"Error: {str(e)}"
            }
    
    def teleport_to_marker(self) -> dict:
        """Teleport to marker"""
        logger.info("Teleporting to marker")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "teleport_to_marker",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("teleport2marker")
            return {
                "success": success,
                "action": "teleport_to_marker",
                "message": "Teleported to marker successfully" if success else "Failed to teleport to marker"
            }
        except Exception as e:
            logger.error(f"Error teleporting to marker: {e}")
            return {
                "success": False,
                "action": "teleport_to_marker",
                "message": f"Error: {str(e)}"
            }
    
    def toggle_combat_log(self) -> dict:
        """Toggle combat log"""
        logger.info("Toggling combat log")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "toggle_combat_log",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("combatlog")
            return {
                "success": success,
                "action": "toggle_combat_log",
                "message": "Combat log toggled successfully" if success else "Failed to toggle combat log"
            }
        except Exception as e:
            logger.error(f"Error toggling combat log: {e}")
            return {
                "success": False,
                "action": "toggle_combat_log",
                "message": f"Error: {str(e)}"
            }
    
    def clear_console(self) -> dict:
        """Clear console"""
        logger.info("Clearing console")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "clear_console",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("console_clear")
            return {
                "success": success,
                "action": "clear_console",
                "message": "Console cleared successfully" if success else "Failed to clear console"
            }
        except Exception as e:
            logger.error(f"Error clearing console: {e}")
            return {
                "success": False,
                "action": "clear_console",
                "message": f"Error: {str(e)}"
            }
    
    def toggle_console(self) -> dict:
        """Toggle console"""
        logger.info("Toggling console")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "toggle_console",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("consoletoggle")
            return {
                "success": success,
                "action": "toggle_console",
                "message": "Console toggled successfully" if success else "Failed to toggle console"
            }
        except Exception as e:
            logger.error(f"Error toggling console: {e}")
            return {
                "success": False,
                "action": "toggle_console",
                "message": f"Error: {str(e)}"
        }
    
    def global_chat(self, message: str) -> dict:
        """Send message to global chat using dynamic binds"""
        logger.info(f"Sending to global chat: {message}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "global_chat",
                "message": message,
                "response": "KeyboardManager not initialized"
                }
        
        try:
            # Use dynamic bind system for chat messages
            success = self.keyboard_manager.trigger_chat_command("chat_say", string_value=message)
            return {
                "success": success,
                "action": "global_chat",
                "message": message,
                "response": f"Message sent to global chat: {message}" if success else "Failed to send message"
            }
        except Exception as e:
            logger.error(f"Error sending global chat message: {e}")
            return {
                "success": False,
                "action": "global_chat",
                "message": message,
                "response": f"Error: {str(e)}"
        }
    
    def team_chat(self, message: str) -> dict:
        """Send message to team chat using dynamic binds"""
        logger.info(f"Sending to team chat: {message}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "team_chat",
                "message": message,
                "response": "KeyboardManager not initialized"
                }
        
        try:
            # Use dynamic bind system for team chat messages
            success = self.keyboard_manager.trigger_chat_command("chat_teamsay", string_value=message)
            return {
                "success": success,
                "action": "team_chat",
                "message": message,
                "response": f"Message sent to team chat: {message}" if success else "Failed to send message"
            }
        except Exception as e:
            logger.error(f"Error sending team chat message: {e}")
            return {
                "success": False,
                "action": "team_chat",
                "message": message,
                "response": f"Error: {str(e)}"
        }
    
    def quit_game(self) -> dict:
        """Quit the game"""
        logger.info("Quitting game")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "quit_game",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("quit_game")
            return {
                "success": success,
                "action": "quit_game",
                "message": "Game quit command executed successfully" if success else "Failed to execute quit command"
            }
        except Exception as e:
            logger.error(f"Error executing quit game: {e}")
            return {
                "success": False,
                "action": "quit_game",
                "message": f"Error: {str(e)}"
        }
    
    def disconnect(self) -> dict:
        """Disconnect from server"""
        logger.info("Disconnecting from server")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "disconnect",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.trigger_api_command("disconnect")
            if success:
                self.game_connected = False
                return {
                    "success": success,
                    "action": "disconnect",
                    "message": "Disconnected from server successfully" if success else "Failed to disconnect"
                }
        except Exception as e:
            logger.error(f"Error executing disconnect: {e}")
            return {
                "success": False,
                "action": "disconnect",
                "message": f"Error: {str(e)}"
        }
    
    def connect(self, server_ip: str) -> dict:
        """Connect to server with given IP using dynamic binds"""
        logger.info(f"Connecting to server: {server_ip}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "connect",
                "server_ip": server_ip,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Use dynamic bind system for server connection
            success = self.keyboard_manager.trigger_chat_command("client_connect", string_value=server_ip)
            if success:
                self.game_connected = True
                self.current_server = server_ip
                return {
                    "success": success,
                    "action": "connect",
                    "server_ip": server_ip,
                    "message": f"Connecting to server: {server_ip}" if success else "Failed to connect"
                }
        except Exception as e:
            logger.error(f"Error executing connect: {e}")
            return {
                "success": False,
                "action": "connect",
                "server_ip": server_ip,
                "message": f"Error: {str(e)}"
            }
    
    def stack_inventory(self, iterations: int = 80) -> dict:
        """Stack inventory items"""
        logger.info(f"Stacking inventory with {iterations} iterations")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "stack_inventory",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.stack_inventory(iterations=iterations)
            return {
                "success": success,
                "action": "stack_inventory",
                "iterations": iterations,
                "message": f"Inventory stacked successfully ({iterations} iterations)" if success else f"Failed to stack inventory ({iterations} iterations)"
            }
        except Exception as e:
            logger.error(f"Error stacking inventory: {e}")
            return {
                "success": False,
                "action": "stack_inventory",
                "iterations": iterations,
                "message": f"Error: {str(e)}"
            }
    
    def cancel_all_crafting(self, iterations: int = 80) -> dict:
        """Cancel all crafting"""
        logger.info(f"Canceling all crafting with {iterations} iterations")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "cancel_all_crafting",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Use cancel_stack_inventory to cancel the specific stack items
            success = self.keyboard_manager.cancel_stack_inventory(iterations=iterations)
            
            # Also trigger the chat notification
            chat_success = self.keyboard_manager.trigger_api_command("cancel_all_crafting")
            
            return {
                "success": success,
                "action": "cancel_all_crafting",
                "iterations": iterations,
                "message": f"All crafting canceled successfully" if success else f"Failed to cancel all crafting"
            }
        except Exception as e:
            logger.error(f"Error canceling all crafting: {e}")
            return {
                "success": False,
                "action": "cancel_all_crafting",
                "iterations": iterations,
                "message": f"Error: {str(e)}"
            }
    
    def toggle_stack_inventory(self, enable: bool) -> dict:
        """Enable or disable continuous stack inventory operations"""
        logger.info(f"{'Enabling' if enable else 'Disabling'} continuous stack inventory")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "toggle_stack_inventory",
                "enable": enable,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.stack_inventory_continuous(enable)
            return {
                "success": success,
                "action": "toggle_stack_inventory",
                "enable": enable,
                "message": f"Continuous stack inventory {'enabled' if enable else 'disabled'} successfully" if success else f"Failed to {'enable' if enable else 'disable'} continuous stack inventory"
            }
        except Exception as e:
            logger.error(f"Error toggling stack inventory: {e}")
            return {
                "success": False,
                "action": "toggle_stack_inventory",
                "enable": enable,
                "message": f"Error: {str(e)}"
        }
    
    def set_look_radius(self, radius: float) -> dict:
        """Set look at radius"""
        logger.info(f"Setting look radius to {radius}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "set_look_radius",
                "radius": radius,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Map radius values to bind indices
            radius_commands = {
                20.0: "lookat_radius_20",    # Bind index 3006
                0.0002: "lookat_radius_0"    # Bind index 3007
            }
            
            command_name = radius_commands.get(radius)
            if command_name is None:
                return {
                    "success": False,
                    "action": "set_look_radius",
                    "radius": radius,
                    "message": f"Invalid radius value: {radius}. Must be one of: 20, 0.0002"
                }
            
            # Use the proper bind instead of typing
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "set_look_radius",
                "radius": radius,
                "message": f"Look radius set to {radius}" if success else "Failed to set look radius"
            }
        except Exception as e:
            logger.error(f"Error setting look radius: {e}")
            return {
                "success": False,
                "action": "set_look_radius",
                "radius": radius,
                "message": f"Error: {str(e)}"
        }
    
    def set_voice_volume(self, volume: float) -> dict:
        """Set voice chat volume"""
        logger.info(f"Setting voice volume to {volume}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "set_voice_volume",
                "volume": volume,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Map volume values to bind indices
            volume_binds = {
                0.0: "audio_voices_0",
                0.25: "audio_voices_25", 
                0.5: "audio_voices_50",
                0.75: "audio_voices_75",
                1.0: "audio_voices_100"
            }
            
            command_name = volume_binds.get(volume)
            if command_name is None:
                return {
                    "success": False,
                    "action": "set_voice_volume",
                    "volume": volume,
                    "message": f"Invalid volume value: {volume}. Must be one of: 0, 0.25, 0.5, 0.75, 1"
                }
            
            # Use the proper bind instead of typing
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "set_voice_volume",
                "volume": volume,
                "message": f"Voice volume set to {volume}" if success else "Failed to set voice volume"
            }
        except Exception as e:
            logger.error(f"Error setting voice volume: {e}")
            return {
                "success": False,
                "action": "set_voice_volume",
                "volume": volume,
                "message": f"Error: {str(e)}"
        }
    
    def set_master_volume(self, volume: float) -> dict:
        """Set master volume"""
        logger.info(f"Setting master volume to {volume}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "set_master_volume",
                "volume": volume,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Map volume values to bind indices
            volume_binds = {
                0.0: "audio_master_0",
                0.25: "audio_master_25", 
                0.5: "audio_master_50",
                0.75: "audio_master_75",
                1.0: "audio_master_100"
            }
            
            command_name = volume_binds.get(volume)
            if command_name is None:
                return {
                    "success": False,
                    "action": "set_master_volume",
                    "volume": volume,
                    "message": f"Invalid volume value: {volume}. Must be one of: 0, 0.25, 0.5, 0.75, 1"
                }
            
            # Use the proper bind instead of typing
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "set_master_volume",
                "volume": volume,
                "message": f"Master volume set to {volume}" if success else "Failed to set master volume"
            }
        except Exception as e:
            logger.error(f"Error setting master volume: {e}")
            return {
                "success": False,
                "action": "set_master_volume",
                "volume": volume,
                "message": f"Error: {str(e)}"
        }
    
    def copy_json_to_clipboard(self, json_data: dict) -> dict:
        """Copy JSON to clipboard"""
        logger.info(f"Copying JSON to clipboard: {json_data}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "copy_json_to_clipboard",
                "json_data": json_data,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.copy_json_to_clipboard(json_data)
            return {
                "success": success,
                "action": "copy_json_to_clipboard",
                "json_data": json_data,
                "message": "JSON copied to clipboard successfully" if success else "Failed to copy JSON to clipboard"
            }
        except Exception as e:
            logger.error(f"Error copying JSON to clipboard: {e}")
            return {
                "success": False,
                "action": "copy_json_to_clipboard",
                "json_data": json_data,
                "message": f"Error: {str(e)}"
        }
    
    def set_hud_state(self, enabled: bool) -> dict:
        """Set HUD state (enabled or disabled)"""
        logger.info(f"Setting HUD state to: {enabled}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "set_hud_state",
                "enabled": enabled,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Map HUD state to bind indices
            hud_commands = {
                True: "hud_on",   # Bind index 3019
                False: "hud_off"  # Bind index 3018
            }
            
            command_name = hud_commands.get(enabled)
            if command_name is None:
                return {
                    "success": False,
                    "action": "set_hud_state",
                    "enabled": enabled,
                    "message": f"Invalid HUD state: {enabled}"
                }
            
            # Use the proper bind instead of typing
            success = self.keyboard_manager.trigger_api_command(command_name)
            return {
                "success": success,
                "action": "set_hud_state",
                "enabled": enabled,
                "message": f"HUD {'enabled' if enabled else 'disabled'}" if success else "Failed to set HUD state"
            }
        except Exception as e:
            logger.error(f"Error setting HUD state: {e}")
            return {
                "success": False,
                "action": "set_hud_state",
                "enabled": enabled,
                "message": f"Error: {str(e)}"
        }
    
    def type_and_enter(self, text: str) -> dict:
        """Type given string and press enter"""
        logger.info(f"Typing and entering: {text}")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "type_and_enter",
                "text": text,
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.type_and_enter(text)
            return {
                "success": success,
                "action": "type_and_enter",
                "text": text,
                "message": f"Typed and entered: {text}" if success else "Failed to type and enter text"
            }
        except Exception as e:
            logger.error(f"Error typing and entering text: {e}")
            return {
                "success": False,
                "action": "type_and_enter",
                "text": text,
                "message": f"Error: {str(e)}"
        }
    
    # Item Database Methods
    def get_all_items(self) -> dict:
        """Get all items from database"""
        try:
            steam_items = steam_manager.get_all_items()
            if steam_items:
                # Convert database format to match expected format
                items_list = []
                for item_id, item_data in steam_items.items():
                    items_list.append({
                        "item_id": item_data.get("id", item_id),
                        "name": item_data.get("name", ""),
                        "description": item_data.get("description", ""),
                        "category": item_data.get("category", "Uncategorized"),
                        "stack_size": item_data.get("stack_size", 1),
                        "craft_time": item_data.get("craft_time", 0.0),
                        "ingredients": item_data.get("ingredients", []),
                        "picture_url": item_data.get("image", "")
                    })
                
                return {
                    "success": True,
                    "action": "get_all_items",
                    "items": items_list,
                    "count": len(items_list),
                    "message": f"Retrieved {len(items_list)} items"
                }
            else:
                return {
                    "success": True,
                    "action": "get_all_items",
                    "items": [],
                    "count": 0,
                    "message": "No items found in database"
                }
        except Exception as e:
            logger.error(f"Failed to get items from Steam database: {e}")
            return {
                "success": False,
                "action": "get_all_items",
                "message": f"Error retrieving items: {str(e)}"
            }
    
    def get_item_by_id(self, item_id: str) -> dict:
        """Get item by ID"""
        try:
            steam_item = steam_manager.get_item_by_id(item_id)
            if steam_item:
                # Convert database format to match expected format
                item_dict = {
                    "item_id": steam_item.get("id", item_id),
                    "name": steam_item.get("name", ""),
                    "description": steam_item.get("description", ""),
                    "category": steam_item.get("category", "Uncategorized"),
                    "stack_size": steam_item.get("stack_size", 1),
                    "craft_time": steam_item.get("craft_time", 0.0),
                    "ingredients": steam_item.get("ingredients", []),
                    "picture_url": steam_item.get("image", "")
                }
                
                return {
                    "success": True,
                    "action": "get_item_by_id",
                    "item": item_dict,
                    "message": f"Retrieved item: {steam_item.get('name', '')}"
                }
            else:
                return {
                    "success": False,
                    "action": "get_item_by_id",
                    "message": f"Item with ID {item_id} not found"
                }
        except Exception as e:
            logger.error(f"Failed to get item from Steam database: {e}")
            return {
                "success": False,
                "action": "get_item_by_id",
                "message": f"Error retrieving item: {str(e)}"
            }
    
    def get_items_by_category(self, category: str) -> dict:
        """Get items by category"""
        try:
            steam_items = steam_manager.get_all_items()
            if steam_items:
                # Filter items by category
                matching_items = []
                for item_id, item_data in steam_items.items():
                    if item_data.get("category", "Uncategorized").lower() == category.lower():
                        matching_items.append({
                            "item_id": item_data.get("id", item_id),
                            "name": item_data.get("name", ""),
                            "description": item_data.get("description", ""),
                            "category": item_data.get("category", "Uncategorized"),
                            "stack_size": 1,
                            "craft_time": 0.0,
                            "ingredients": [],
                            "picture_url": item_data.get("image", "")
                        })
                
                return {
                    "success": True,
                    "action": "get_items_by_category",
                    "items": matching_items,
                    "category": category,
                    "count": len(matching_items),
                    "message": f"Retrieved {len(matching_items)} items in category '{category}'"
                }
            else:
                return {
                    "success": True,
                    "action": "get_items_by_category",
                    "items": [],
                    "category": category,
                    "count": 0,
                    "message": f"No items found in category '{category}'"
                }
        except Exception as e:
            logger.error(f"Failed to get items by category: {e}")
            return {
                "success": False,
                "action": "get_items_by_category",
                "message": f"Error retrieving items by category: {str(e)}"
            }
    
    def search_items(self, query: str) -> dict:
        """Search items by name or description"""
        try:
            steam_items = steam_manager.get_all_items()
            if steam_items:
                # Search in Steam database
                matching_items = []
                query_lower = query.lower()
                
                for item_id, item_data in steam_items.items():
                    name = item_data.get("name", "").lower()
                    description = item_data.get("description", "").lower()
                    
                    if query_lower in name or query_lower in description:
                        matching_items.append({
                            "item_id": item_data.get("id", item_id),
                            "name": item_data.get("name", ""),
                            "description": item_data.get("description", ""),
                            "category": item_data.get("category", "Uncategorized"),
                            "stack_size": item_data.get("stack_size", 1),
                            "craft_time": item_data.get("craft_time", 0.0),
                            "ingredients": item_data.get("ingredients", []),
                            "picture_url": item_data.get("image", "")
                        })
                
                return {
                    "success": True,
                    "action": "search_items",
                    "items": matching_items,
                    "query": query,
                    "count": len(matching_items),
                    "message": f"Found {len(matching_items)} items matching '{query}'"
                }
            else:
                return {
                    "success": True,
                    "action": "search_items",
                    "items": [],
                    "query": query,
                    "count": 0,
                    "message": f"No items found matching '{query}'"
                }
        except Exception as e:
            logger.error(f"Failed to search Steam database: {e}")
            return {
                "success": False,
                "action": "search_items",
                "message": f"Error searching items: {str(e)}"
            }
    

    

    

    
    def get_categories(self) -> dict:
        """Get all categories"""
        try:
            steam_items = steam_manager.get_all_items()
            if steam_items:
                # Extract unique categories from Steam database
                categories = set()
                for item_data in steam_items.values():
                    category = item_data.get('category', 'Uncategorized')
                    categories.add(category)
                
                categories_list = sorted(list(categories))
                return {
                    "success": True,
                    "action": "get_categories",
                    "categories": categories_list,
                    "count": len(categories_list),
                    "message": f"Retrieved {len(categories_list)} categories"
                }
            else:
                return {
                    "success": True,
                    "action": "get_categories",
                    "categories": [],
                    "count": 0,
                    "message": "No categories found"
                }
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return {
                "success": False,
                "action": "get_categories",
                "message": f"Error retrieving categories: {str(e)}"
            }
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            steam_stats = steam_manager.get_database_stats()
            if steam_stats:
                item_count = steam_stats.get('itemCount', 0)
                last_updated = steam_stats.get('lastUpdated', '')
                
                # Get categories from Steam database
                steam_items = steam_manager.get_all_items()
                categories = set()
                if steam_items:
                    for item_data in steam_items.values():
                        category = item_data.get('category', 'Uncategorized')
                        categories.add(category)
                
                return {
                    "success": True,
                    "action": "get_database_stats",
                    "stats": {
                        "total_items": item_count,
                        "total_categories": len(categories),
                        "categories": list(categories)
                    },
                    "message": f"Database contains {item_count} items in {len(categories)} categories"
                }
            else:
                return {
                    "success": True,
                    "action": "get_database_stats",
                    "stats": {
                        "total_items": 0,
                        "total_categories": 0,
                        "categories": []
                    },
                    "message": "Database is empty"
                }
        except Exception as e:
            logger.error(f"Failed to get stats from Steam database: {e}")
            return {
                "success": False,
                "action": "get_database_stats",
                "message": f"Error retrieving database stats: {str(e)}"
            }
    
    def start_anti_afk(self) -> dict:
        """Start the anti-AFK feature"""
        logger.info("Starting anti-AFK feature")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "start_anti_afk",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.start_anti_afk()
            return {
                "success": success,
                "action": "start_anti_afk",
                "message": "Anti-AFK started successfully" if success else "Failed to start anti-AFK"
            }
        except Exception as e:
            logger.error(f"Error starting anti-AFK: {e}")
            return {
                "success": False,
                "action": "start_anti_afk",
                "message": f"Error: {str(e)}"
            }
    
    def stop_anti_afk(self) -> dict:
        """Stop the anti-AFK feature"""
        logger.info("Stopping anti-AFK feature")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "stop_anti_afk",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            success = self.keyboard_manager.stop_anti_afk()
            return {
                "success": success,
                "action": "stop_anti_afk",
                "message": "Anti-AFK stopped successfully" if success else "Failed to stop anti-AFK"
            }
        except Exception as e:
            logger.error(f"Error stopping anti-AFK: {e}")
            return {
                "success": False,
                "action": "stop_anti_afk",
                "message": f"Error: {str(e)}"
            }
    
    def get_anti_afk_status(self) -> dict:
        """Get the current anti-AFK status"""
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "get_anti_afk_status",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            is_running = self.keyboard_manager.is_anti_afk_running()
            return {
                "success": True,
                "action": "get_anti_afk_status",
                "running": is_running,
                "message": "Anti-AFK is running" if is_running else "Anti-AFK is not running"
            }
        except Exception as e:
            logger.error(f"Error getting anti-AFK status: {e}")
            return {
                "success": False,
                "action": "get_anti_afk_status",
                "message": f"Error: {str(e)}"
            }
    
    def reload_binds_manager_dynamic_binds(self) -> dict:
        """Reload the binds manager's dynamic binds from keys.cfg"""
        logger.info("Reloading binds manager dynamic binds from keys.cfg")
        
        if not self.keyboard_manager:
            return {
                "success": False,
                "action": "reload_binds_manager_dynamic_binds",
                "message": "KeyboardManager not initialized"
                }
        
        try:
            # Reload dynamic binds from keys.cfg
            success = self.keyboard_manager.binds_manager.reload_dynamic_binds_from_file()
            return {
                "success": success,
                "action": "reload_binds_manager_dynamic_binds",
                "message": "Dynamic binds reloaded successfully" if success else "Failed to reload dynamic binds"
            }
        except Exception as e:
            logger.error(f"Error reloading dynamic binds: {e}")
            return {
                "success": False,
                "action": "reload_binds_manager_dynamic_binds",
                "message": f"Error: {str(e)}"
            }
    


# Initialize the game controller (will be created when app starts)
rust_controller = None

def create_rust_controller():
    """Create the RustGameController instance when the app starts"""
    global rust_controller
    if rust_controller is None:
        rust_controller = RustGameController()
    return rust_controller

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Rust Game Controller API",
        "version": "1.0.0"
    })

@app.route('/craft/id', methods=['POST'])
def craft_by_id():
    """Craft an item by ID with given quantity"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return jsonify({"error": "item_id is required"}), 400
        
        controller = create_rust_controller()
        result = controller.craft_by_id(item_id, quantity)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in craft_by_id: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/craft/name', methods=['POST'])
def craft_by_name():
    """Craft an item by name with given quantity"""
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        quantity = data.get('quantity', 1)
        
        if not item_name:
            return jsonify({"error": "item_name is required"}), 400
        
        controller = create_rust_controller()
        result = controller.craft_by_name(item_name, quantity)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in craft_by_name: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/craft/cancel/id', methods=['POST'])
def cancel_craft_by_id():
    """Cancel crafting an item by ID with given quantity"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return jsonify({"error": "item_id is required"}), 400
        
        controller = create_rust_controller()
        result = controller.cancel_craft_by_id(item_id, quantity)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in cancel_craft_by_id: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/craft/cancel/name', methods=['POST'])
def cancel_craft_by_name():
    """Cancel crafting an item by name with given quantity"""
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        quantity = data.get('quantity', 1)
        
        if not item_name:
            return jsonify({"error": "item_name is required"}), 400
        
        controller = create_rust_controller()
        result = controller.cancel_craft_by_name(item_name, quantity)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in cancel_craft_by_name: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/suicide', methods=['POST'])
def suicide():
    """Kill the player character"""
    try:
        controller = create_rust_controller()
        result = controller.suicide()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in suicide: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/respawn', methods=['POST'])
def respawn():
    """Respawn player with optional spawn ID"""
    try:
        data = request.get_json() or {}
        spawn_id = data.get('spawn_id')
        
        controller = create_rust_controller()
        result = controller.respawn(spawn_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in respawn: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/kill', methods=['POST'])
def kill_only():
    """Kill the player character only"""
    try:
        controller = create_rust_controller()
        result = controller.kill_only()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in kill_only: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/respawn-only', methods=['POST'])
def respawn_only():
    """Respawn the player character only (without killing first)"""
    try:
        controller = create_rust_controller()
        result = controller.respawn_only()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in respawn_only: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/respawn-random', methods=['POST'])
def respawn_random():
    """Kill and respawn the player character (random spawn)"""
    try:
        controller = create_rust_controller()
        result = controller.respawn_random()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in respawn_random: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/respawn-bed', methods=['POST'])
def respawn_bed():
    """Kill and respawn at specific sleeping bag"""
    try:
        data = request.get_json()
        spawn_id = data.get('spawn_id')
        
        if not spawn_id:
            return jsonify({"error": "spawn_id is required"}), 400
        
        controller = create_rust_controller()
        result = controller.respawn_bed(spawn_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in respawn_bed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-run', methods=['POST'])
def auto_run():
    """Enable auto run"""
    try:
        controller = create_rust_controller()
        result = controller.auto_run()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_run: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-run-jump', methods=['POST'])
def auto_run_jump():
    """Enable auto run and jump"""
    try:
        controller = create_rust_controller()
        result = controller.auto_run_jump()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_run_jump: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-crouch-attack', methods=['POST'])
def auto_crouch_attack():
    """Enable auto crouch and attack"""
    try:
        controller = create_rust_controller()
        result = controller.auto_crouch_attack()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_crouch_attack: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/gesture', methods=['POST'])
def gesture():
    """Perform a gesture/emote"""
    try:
        data = request.get_json() or {}
        gesture_name = data.get('gesture_name')
        
        if not gesture_name:
            return jsonify({"error": "gesture_name is required"}), 400
        
        controller = create_rust_controller()
        result = controller.gesture(gesture_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in gesture: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/noclip', methods=['POST'])
def noclip_toggle():
    """Toggle noclip on/off"""
    try:
        data = request.get_json() or {}
        enable = data.get('enable')
        
        if enable is None:
            return jsonify({"error": "enable parameter is required (true/false)"}), 400
        
        controller = create_rust_controller()
        result = controller.noclip_toggle(enable)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in noclip_toggle: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/god-mode', methods=['POST'])
def god_mode_toggle():
    """Toggle god mode on/off"""
    try:
        data = request.get_json() or {}
        enable = data.get('enable')
        
        if enable is None:
            return jsonify({"error": "enable parameter is required (true/false)"}), 400
        
        controller = create_rust_controller()
        result = controller.god_mode_toggle(enable)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in god_mode_toggle: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/set-time', methods=['POST'])
def set_time():
    """Set time of day"""
    try:
        data = request.get_json() or {}
        time_hour = data.get('time_hour')
        
        if time_hour is None:
            return jsonify({"error": "time_hour parameter is required (0, 4, 8, 12, 16, 20, 24)"}), 400
        
        controller = create_rust_controller()
        result = controller.set_time(time_hour)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in set_time: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/teleport-marker', methods=['POST'])
def teleport_to_marker():
    """Teleport to marker"""
    try:
        controller = create_rust_controller()
        result = controller.teleport_to_marker()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in teleport_to_marker: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/combat-log', methods=['POST'])
def toggle_combat_log():
    """Toggle combat log"""
    try:
        controller = create_rust_controller()
        result = controller.toggle_combat_log()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in toggle_combat_log: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/clear-console', methods=['POST'])
def clear_console():
    """Clear console"""
    try:
        controller = create_rust_controller()
        result = controller.clear_console()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in clear_console: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/toggle-console', methods=['POST'])
def toggle_console():
    """Toggle console"""
    try:
        controller = create_rust_controller()
        result = controller.toggle_console()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in toggle_console: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat/global', methods=['POST'])
def global_chat():
    """Send message to global chat"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "message is required"}), 400
        
        controller = create_rust_controller()
        result = controller.global_chat(message)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in global_chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat/team', methods=['POST'])
def team_chat():
    """Send message to team chat"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "message is required"}), 400
        
        controller = create_rust_controller()
        result = controller.team_chat(message)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in team_chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/quit', methods=['POST'])
def quit_game():
    """Quit the game"""
    try:
        controller = create_rust_controller()
        result = controller.quit_game()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in quit_game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from server"""
    try:
        controller = create_rust_controller()
        result = controller.disconnect()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/connect', methods=['POST'])
def connect():
    """Connect to server with given IP"""
    try:
        data = request.get_json()
        server_ip = data.get('server_ip')
        
        if not server_ip:
            return jsonify({"error": "server_ip is required"}), 400
        
        controller = create_rust_controller()
        result = controller.connect(server_ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in connect: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/inventory/stack', methods=['POST'])
def stack_inventory():
    """Stack inventory items"""
    try:
        data = request.get_json() or {}
        iterations = data.get('iterations', 80)
        
        controller = create_rust_controller()
        result = controller.stack_inventory(iterations=iterations)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stack_inventory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/inventory/toggle-stack', methods=['POST'])
def toggle_stack_inventory():
    """Enable or disable continuous stack inventory operations"""
    try:
        data = request.get_json() or {}
        enable = data.get('enable')
        
        if enable is None:
            return jsonify({"error": "enable parameter is required (true/false)"}), 400
        
        controller = create_rust_controller()
        result = controller.toggle_stack_inventory(enable=enable)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in toggle_stack_inventory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/craft/cancel-all', methods=['POST'])
def cancel_all_crafting():
    """Cancel all crafting"""
    try:
        data = request.get_json() or {}
        iterations = data.get('iterations', 80)
        
        controller = create_rust_controller()
        result = controller.cancel_all_crafting(iterations=iterations)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in cancel_all_crafting: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings/look-radius', methods=['POST'])
def set_look_radius():
    """Set look at radius"""
    try:
        data = request.get_json()
        radius = data.get('radius')
        
        if radius is None:
            return jsonify({"error": "radius is required"}), 400
        
        controller = create_rust_controller()
        result = controller.set_look_radius(radius)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in set_look_radius: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings/voice-volume', methods=['POST'])
def set_voice_volume():
    """Set voice chat volume"""
    try:
        data = request.get_json()
        volume = data.get('volume')
        
        if volume is None:
            return jsonify({"error": "volume is required"}), 400
        
        controller = create_rust_controller()
        result = controller.set_voice_volume(volume)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in set_voice_volume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings/master-volume', methods=['POST'])
def set_master_volume():
    """Set master volume"""
    try:
        data = request.get_json()
        volume = data.get('volume')
        
        if volume is None:
            return jsonify({"error": "volume is required"}), 400
        
        controller = create_rust_controller()
        result = controller.set_master_volume(volume)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in set_master_volume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/clipboard/copy-json', methods=['POST'])
def copy_json_to_clipboard():
    """Copy JSON to clipboard"""
    try:
        data = request.get_json()
        json_data = data.get('json_data')
        
        if not json_data:
            return jsonify({"error": "json_data is required"}), 400
        
        controller = create_rust_controller()
        result = controller.copy_json_to_clipboard(json_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in copy_json_to_clipboard: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings/hud', methods=['POST'])
def set_hud_state():
    """Set HUD state (enabled or disabled)"""
    try:
        data = request.get_json()
        enabled = data.get('enabled')
        
        if enabled is None:
            return jsonify({"error": "enabled is required"}), 400
        
        controller = create_rust_controller()
        result = controller.set_hud_state(enabled)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in set_hud_state: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/input/type-enter', methods=['POST'])
def type_and_enter():
    """Type given string and press enter"""
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({"error": "text is required"}), 400
        
        controller = create_rust_controller()
        result = controller.type_and_enter(text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in type_and_enter: {e}")
        return jsonify({"error": str(e)}), 500

# Item Database Endpoints
@app.route('/items', methods=['GET'])
def get_all_items():
    """Get all items from database"""
    try:
        controller = create_rust_controller()
        result = controller.get_all_items()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_all_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/items/<item_id>', methods=['GET'])
def get_item_by_id(item_id):
    """Get item by ID"""
    try:
        controller = create_rust_controller()
        result = controller.get_item_by_id(item_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_item_by_id: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/items/category/<category>', methods=['GET'])
def get_items_by_category(category):
    """Get items by category"""
    try:
        controller = create_rust_controller()
        result = controller.get_items_by_category(category)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_items_by_category: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/items/search', methods=['GET'])
def search_items():
    """Search items by name or description"""
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "query parameter 'q' is required"}), 400
        
        controller = create_rust_controller()
        result = controller.search_items(query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in search_items: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/items/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    try:
        controller = create_rust_controller()
        result = controller.get_categories()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/items/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        controller = create_rust_controller()
        result = controller.get_database_stats()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_database_stats: {e}")
        return jsonify({"error": str(e)}), 500


# Anti-AFK Endpoints
@app.route('/anti-afk/start', methods=['POST'])
def start_anti_afk():
    """Start the anti-AFK feature"""
    try:
        controller = create_rust_controller()
        result = controller.start_anti_afk()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in start_anti_afk: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/anti-afk/stop', methods=['POST'])
def stop_anti_afk():
    """Stop the anti-AFK feature"""
    try:
        controller = create_rust_controller()
        result = controller.stop_anti_afk()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stop_anti_afk: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/anti-afk/status', methods=['GET'])
def get_anti_afk_status():
    """Get the current anti-AFK status"""
    try:
        controller = create_rust_controller()
        result = controller.get_anti_afk_status()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_anti_afk_status: {e}")
        return jsonify({"error": str(e)}), 500


# Keyboard Manager Endpoints
@app.route('/keyboard-manager/clear-cache', methods=['GET'])
def clear_keyboard_manager_cache():
    """Clear the keyboard manager's key combination cache"""
    try:
        controller = create_rust_controller()
        if controller.keyboard_manager:
            # Clear the cache
            controller.keyboard_manager._key_combo_cache.clear()
            # Reload key combinations from binds manager
            controller.keyboard_manager._load_key_combinations()
            logger.info("Keyboard manager cache cleared and refreshed successfully")
            return jsonify({
                "success": True,
                "message": "Keyboard manager cache cleared and refreshed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Keyboard manager not initialized"
            }), 500
    except Exception as e:
        logger.error(f"Error in clear_keyboard_manager_cache: {e}")
        return jsonify({
            "success": False,
            "message": f"Error clearing cache: {str(e)}"
        }), 500

@app.route('/binds-manager/reload-dynamic-binds', methods=['GET'])
def reload_binds_manager_dynamic_binds():
    """Reload the binds manager's dynamic binds from keys.cfg"""
    try:
        controller = create_rust_controller()
        result = controller.reload_binds_manager_dynamic_binds()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in reload_binds_manager_dynamic_binds: {e}")
        return jsonify({
            "success": False,
            "message": f"Error reloading dynamic binds: {str(e)}"
        }), 500

@app.route('/binds-manager/regenerate-cleared', methods=['POST'])
def regenerate_binds_with_cleared_dynamic():
    """Regenerate all binds with dynamic binds completely cleared"""
    try:
        controller = create_rust_controller()
        if controller.keyboard_manager and controller.keyboard_manager.binds_manager:
            # Clear dynamic binds from the server's binds manager instance
            binds_manager = controller.keyboard_manager.binds_manager
            binds_manager.dynamic_binds.clear()
            binds_manager.dynamic_bind_order.clear()
            binds_manager.next_dynamic_bind = binds_manager.CHAT_BINDS_START
            
            # Remove dynamic bind indices from used_binds
            for bind_index in range(binds_manager.CHAT_BINDS_START, binds_manager.CHAT_BINDS_END + 1):
                if bind_index in binds_manager.used_binds:
                    binds_manager.used_binds.remove(bind_index)
            
            # Regenerate keys.cfg with cleared state
            success = binds_manager.write_keys_cfg_with_sections_protected()
            
            if success:
                logger.info("Successfully regenerated keys.cfg with cleared dynamic binds")
                return jsonify({
                    "success": True,
                    "message": "All rust-actions binds regenerated with dynamic binds cleared"
                })
            else:
                logger.error("Failed to regenerate keys.cfg")
                return jsonify({
                    "success": False,
                    "message": "Failed to write keys.cfg file"
                }), 500
        else:
            return jsonify({
                "success": False,
                "message": "Keyboard manager or binds manager not initialized"
            }), 500
    except Exception as e:
        logger.error(f"Error in regenerate_binds_with_cleared_dynamic: {e}")
        return jsonify({
            "success": False,
            "message": f"Error regenerating binds: {str(e)}"
        }), 500


# Steam Integration Endpoints
@app.route('/steam/login', methods=['POST'])
def steam_login():
    """Login to Steam"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Username and password are required"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        result = steam_manager.steam_login(username, password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in steam_login: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/status', methods=['GET'])
def steam_status():
    """Check Steam login status"""
    try:
        result = steam_manager.check_steam_login()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in steam_status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/update-database', methods=['POST'])
def update_steam_database():
    """Update item database using Steam"""
    try:
        data = request.get_json() or {}
        credentials = data.get('credentials')  # Optional credentials
        
        def progress_callback(progress, message):
            # For API calls, we'll just log the progress
            logger.info(f"Progress {progress}%: {message}")
        
        result = steam_manager.update_item_database(
            credentials=credentials,
            progress_callback=progress_callback
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in update_steam_database: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/reset-database', methods=['POST'])
def reset_steam_database():
    """Reset the item database"""
    try:
        result = steam_manager.reset_item_database()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in reset_steam_database: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/items', methods=['GET'])
def get_steam_items():
    """Get all items from Steam database"""
    try:
        items = steam_manager.get_all_items()
        return jsonify({
            "success": True,
            "items": items,
            "count": len(items)
        })
    except Exception as e:
        logger.error(f"Error in get_steam_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/craftable-items', methods=['GET'])
def get_craftable_items():
    """Get only craftable items with ingredients from Steam database"""
    try:
        # Use the binds_manager to get properly filtered craftable items
        controller = create_rust_controller()
        craftable_items = {}
        for item in controller.keyboard_manager.binds_manager.craftable_items:
            item_id = item['id']
            # Get the full item data from steam_manager
            full_item = steam_manager.get_item_by_id(item_id)
            if full_item:
                craftable_items[item_id] = full_item
        
        return jsonify({
            "success": True,
            "items": craftable_items,
            "count": len(craftable_items)
        })
    except Exception as e:
        logger.error(f"Error in get_craftable_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/items/<item_id>', methods=['GET'])
def get_steam_item(item_id):
    """Get item by ID from Steam database"""
    try:
        item = steam_manager.get_item_by_id(item_id)
        if item:
            return jsonify({
                "success": True,
                "item": item
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Item with ID {item_id} not found"
            }), 404
    except Exception as e:
        logger.error(f"Error in get_steam_item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/stats', methods=['GET'])
def get_steam_stats():
    """Get Steam database statistics"""
    try:
        stats = steam_manager.get_database_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error in get_steam_stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/test-installation', methods=['GET'])
def test_steam_installation():
    """Test SteamCMD installation"""
    try:
        result = steam_manager.test_steamcmd_installation()
        return jsonify({
            "success": True,
            "test_result": result
        })
    except Exception as e:
        logger.error(f"Error in test_steam_installation: {e}")
        return jsonify({"error": str(e)}), 500

# Serve Steam item images
@app.route('/steam/images/<filename>')
def serve_steam_image(filename):
    """Serve Steam item images"""
    try:
        from flask import send_from_directory
        return send_from_directory(steam_manager.images_dir, filename)
    except Exception as e:
        logger.error(f"Error serving Steam image {filename}: {e}")
        return jsonify({"error": "Image not found"}), 404

# Crafting Data Endpoints
@app.route('/steam/crafting/recipe/<item_id>', methods=['GET'])
def get_crafting_recipe(item_id):
    """Get crafting recipe for a specific item"""
    try:
        recipe = steam_manager.get_crafting_recipe(item_id)
        if recipe:
            return jsonify({
                "success": True,
                "recipe": recipe
            })
        else:
            return jsonify({
                "success": False,
                "message": f"No crafting recipe found for item: {item_id}"
            }), 404
    except Exception as e:
        logger.error(f"Error in get_crafting_recipe: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/crafting/recipes', methods=['GET'])
def get_all_crafting_recipes():
    """Get all crafting recipes"""
    try:
        recipes = steam_manager.get_all_crafting_recipes()
        return jsonify({
            "success": True,
            "recipes": recipes.get("recipes", []),
            "count": len(recipes.get("recipes", []))
        })
    except Exception as e:
        logger.error(f"Error in get_all_crafting_recipes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/steam/update-crafting', methods=['POST'])
def update_crafting_data():
    """Update crafting data from Unity bundles and merge into item database"""
    try:
        # Find the items.preload.bundle file
        steam_apps_path = Path("data/steamcmd/steamapps/common/Rust")
        possible_bundle_paths = [
            steam_apps_path / "Bundles" / "shared" / "items.preload.bundle",
            steam_apps_path / "RustClient_Data" / "Bundles" / "shared" / "items.preload.bundle",
            Path("data/rustclient/Bundles/shared/items.preload.bundle"),
            Path("data/rustclient/data/rustclient/Bundles/shared/items.preload.bundle"),
        ]
        
        bundle_path = None
        for path in possible_bundle_paths:
            if path.exists():
                bundle_path = path
                logger.info(f"Found items bundle at: {bundle_path}")
                break
        
        if not bundle_path:
            return jsonify({
                "success": False,
                "error": "items.preload.bundle not found. Please run 'Update Item Database' first to download Rust client files."
            }), 404
        
        # Extract crafting data using Unity asset extractor and merge into database
        result = steam_manager.extract_crafting_data_from_bundles(bundle_path)
        
        if result.get("success"):
            # Get the merge result from the steam manager
            merge_result = steam_manager.merge_crafting_data_into_database(result["crafting_data"])
            
            if merge_result.get("success"):
                logger.info(f"Merged {merge_result['recipes_added']} crafting recipes into item database")
                return jsonify({
                    "success": True,
                    "message": f"Successfully merged {merge_result['recipes_added']} crafting recipes into item database. Note: Some recipes (like Night Vision Goggles) are hardcoded in the game and not stored in Unity bundles.",
                    "recipes_added": merge_result["recipes_added"],
                    "total_recipes": merge_result["total_recipes"]
                })
            else:
                return jsonify({
                    "success": False,
                    "error": merge_result.get("error", "Failed to merge crafting data")
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Unknown error during extraction")
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating crafting data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize the RustGameController when the app starts
    logger.info("Initializing RustGameController...")
    create_rust_controller()
    logger.info("RustGameController initialized successfully")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
