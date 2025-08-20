from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from pathlib import Path
from steam_manager import steam_manager

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
    
    def craft_by_id(self, item_id: str, quantity: int) -> dict:
        """Craft an item by ID with given quantity"""
        logger.info(f"Crafting item ID {item_id} with quantity {quantity}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "craft_by_id",
            "item_id": item_id,
            "quantity": quantity,
            "message": f"Crafting {quantity}x of item ID {item_id}"
        }
    
    def craft_by_name(self, item_name: str, quantity: int) -> dict:
        """Craft an item by name with given quantity"""
        logger.info(f"Crafting item {item_name} with quantity {quantity}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "craft_by_name",
            "item_name": item_name,
            "quantity": quantity,
            "message": f"Crafting {quantity}x of {item_name}"
        }
    
    def cancel_craft_by_id(self, item_id: str, quantity: int) -> dict:
        """Cancel crafting an item by ID with given quantity"""
        logger.info(f"Canceling craft of item ID {item_id} with quantity {quantity}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "cancel_craft_by_id",
            "item_id": item_id,
            "quantity": quantity,
            "message": f"Canceled crafting {quantity}x of item ID {item_id}"
        }
    
    def cancel_craft_by_name(self, item_name: str, quantity: int) -> dict:
        """Cancel crafting an item by name with given quantity"""
        logger.info(f"Canceling craft of item {item_name} with quantity {quantity}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "cancel_craft_by_name",
            "item_name": item_name,
            "quantity": quantity,
            "message": f"Canceled crafting {quantity}x of {item_name}"
        }
    
    def suicide(self) -> dict:
        """Kill the player character"""
        logger.info("Executing suicide command")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "suicide",
            "message": "Player committed suicide"
        }
    
    def respawn(self, spawn_id: str = None) -> dict:
        """Respawn player with optional spawn ID"""
        logger.info(f"Respawning with spawn ID: {spawn_id}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "respawn",
            "spawn_id": spawn_id,
            "message": f"Respawning with spawn ID: {spawn_id if spawn_id else 'random'}"
        }
    
    def auto_run(self) -> dict:
        """Enable auto run"""
        logger.info("Enabling auto run")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "auto_run",
            "message": "Auto run enabled"
        }
    
    def auto_run_jump(self) -> dict:
        """Enable auto run and jump"""
        logger.info("Enabling auto run and jump")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "auto_run_jump",
            "message": "Auto run and jump enabled"
        }
    
    def auto_crouch_attack(self) -> dict:
        """Enable auto crouch and attack"""
        logger.info("Enabling auto crouch and attack")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "auto_crouch_attack",
            "message": "Auto crouch and attack enabled"
        }
    
    def global_chat(self, message: str) -> dict:
        """Send message to global chat"""
        logger.info(f"Sending to global chat: {message}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "global_chat",
            "message": message,
            "response": f"Sent to global chat: {message}"
        }
    
    def team_chat(self, message: str) -> dict:
        """Send message to team chat"""
        logger.info(f"Sending to team chat: {message}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "team_chat",
            "message": message,
            "response": f"Sent to team chat: {message}"
        }
    
    def quit_game(self) -> dict:
        """Quit the game"""
        logger.info("Quitting game")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "quit_game",
            "message": "Game quit command executed"
        }
    
    def disconnect(self) -> dict:
        """Disconnect from server"""
        logger.info("Disconnecting from server")
        # TODO: Implement actual game interaction
        self.game_connected = False
        return {
            "success": True,
            "action": "disconnect",
            "message": "Disconnected from server"
        }
    
    def connect(self, server_ip: str) -> dict:
        """Connect to server with given IP"""
        logger.info(f"Connecting to server: {server_ip}")
        # TODO: Implement actual game interaction
        self.game_connected = True
        self.current_server = server_ip
        return {
            "success": True,
            "action": "connect",
            "server_ip": server_ip,
            "message": f"Connecting to server: {server_ip}"
        }
    
    def stack_inventory(self) -> dict:
        """Stack inventory items"""
        logger.info("Stacking inventory")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "stack_inventory",
            "message": "Inventory stacked"
        }
    
    def cancel_all_crafting(self) -> dict:
        """Cancel all crafting"""
        logger.info("Canceling all crafting")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "cancel_all_crafting",
            "message": "All crafting canceled"
        }
    
    def set_look_radius(self, radius: float) -> dict:
        """Set look at radius"""
        logger.info(f"Setting look radius to {radius}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "set_look_radius",
            "radius": radius,
            "message": f"Look radius set to {radius}"
        }
    
    def set_voice_volume(self, volume: float) -> dict:
        """Set voice chat volume"""
        logger.info(f"Setting voice volume to {volume}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "set_voice_volume",
            "volume": volume,
            "message": f"Voice volume set to {volume}"
        }
    
    def set_master_volume(self, volume: float) -> dict:
        """Set master volume"""
        logger.info(f"Setting master volume to {volume}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "set_master_volume",
            "volume": volume,
            "message": f"Master volume set to {volume}"
        }
    
    def copy_json_to_clipboard(self, json_data: dict) -> dict:
        """Copy JSON to clipboard"""
        logger.info(f"Copying JSON to clipboard: {json_data}")
        # TODO: Implement actual clipboard interaction
        return {
            "success": True,
            "action": "copy_json_to_clipboard",
            "json_data": json_data,
            "message": "JSON copied to clipboard"
        }
    
    def set_hud_state(self, enabled: bool) -> dict:
        """Set HUD state (enabled or disabled)"""
        logger.info(f"Setting HUD state to: {enabled}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "set_hud_state",
            "enabled": enabled,
            "message": f"HUD {'enabled' if enabled else 'disabled'}"
        }
    
    def type_and_enter(self, text: str) -> dict:
        """Type given string and press enter"""
        logger.info(f"Typing and entering: {text}")
        # TODO: Implement actual game interaction
        return {
            "success": True,
            "action": "type_and_enter",
            "text": text,
            "message": f"Typed and entered: {text}"
        }
    
    # Item Database Methods
    def get_all_items(self) -> dict:
        """Get all items from database"""
        try:
            steam_items = steam_manager.get_all_items()
            if steam_items:
                # Convert Steam database format to match expected format
                items_list = []
                for item_id, item_data in steam_items.items():
                    items_list.append({
                        "item_id": item_data.get("id", item_id),
                        "name": item_data.get("name", ""),
                        "description": item_data.get("description", ""),
                        "category": item_data.get("category", "Uncategorized"),
                        "stack_size": 1,  # Steam database doesn't have this
                        "craft_time": 0.0,  # Steam database doesn't have this
                        "ingredients": [],  # Steam database doesn't have this
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
                # Convert Steam database format to match expected format
                item_dict = {
                    "item_id": steam_item.get("id", item_id),
                    "name": steam_item.get("name", ""),
                    "description": steam_item.get("description", ""),
                    "category": steam_item.get("category", "Uncategorized"),
                    "stack_size": 1,  # Steam database doesn't have this
                    "craft_time": 0.0,  # Steam database doesn't have this
                    "ingredients": [],  # Steam database doesn't have this
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
                            "stack_size": 1,
                            "craft_time": 0.0,
                            "ingredients": [],
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
    


# Initialize the game controller
rust_controller = RustGameController()

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
        
        result = rust_controller.craft_by_id(item_id, quantity)
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
        
        result = rust_controller.craft_by_name(item_name, quantity)
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
        
        result = rust_controller.cancel_craft_by_id(item_id, quantity)
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
        
        result = rust_controller.cancel_craft_by_name(item_name, quantity)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in cancel_craft_by_name: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/suicide', methods=['POST'])
def suicide():
    """Kill the player character"""
    try:
        result = rust_controller.suicide()
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
        
        result = rust_controller.respawn(spawn_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in respawn: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-run', methods=['POST'])
def auto_run():
    """Enable auto run"""
    try:
        result = rust_controller.auto_run()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_run: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-run-jump', methods=['POST'])
def auto_run_jump():
    """Enable auto run and jump"""
    try:
        result = rust_controller.auto_run_jump()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_run_jump: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/player/auto-crouch-attack', methods=['POST'])
def auto_crouch_attack():
    """Enable auto crouch and attack"""
    try:
        result = rust_controller.auto_crouch_attack()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in auto_crouch_attack: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat/global', methods=['POST'])
def global_chat():
    """Send message to global chat"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "message is required"}), 400
        
        result = rust_controller.global_chat(message)
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
        
        result = rust_controller.team_chat(message)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in team_chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/quit', methods=['POST'])
def quit_game():
    """Quit the game"""
    try:
        result = rust_controller.quit_game()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in quit_game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from server"""
    try:
        result = rust_controller.disconnect()
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
        
        result = rust_controller.connect(server_ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in connect: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/inventory/stack', methods=['POST'])
def stack_inventory():
    """Stack inventory items"""
    try:
        result = rust_controller.stack_inventory()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stack_inventory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/craft/cancel-all', methods=['POST'])
def cancel_all_crafting():
    """Cancel all crafting"""
    try:
        result = rust_controller.cancel_all_crafting()
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
        
        result = rust_controller.set_look_radius(radius)
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
        
        result = rust_controller.set_voice_volume(volume)
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
        
        result = rust_controller.set_master_volume(volume)
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
        
        result = rust_controller.copy_json_to_clipboard(json_data)
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
        
        result = rust_controller.set_hud_state(enabled)
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
        
        result = rust_controller.type_and_enter(text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in type_and_enter: {e}")
        return jsonify({"error": str(e)}), 500

# Item Database Endpoints
@app.route('/items', methods=['GET'])
def get_all_items():
    """Get all items from database"""
    try:
        result = rust_controller.get_all_items()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_all_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/items/<item_id>', methods=['GET'])
def get_item_by_id(item_id):
    """Get item by ID"""
    try:
        result = rust_controller.get_item_by_id(item_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_item_by_id: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/items/category/<category>', methods=['GET'])
def get_items_by_category(category):
    """Get items by category"""
    try:
        result = rust_controller.get_items_by_category(category)
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
        
        result = rust_controller.search_items(query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in search_items: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/items/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    try:
        result = rust_controller.get_categories()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/items/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        result = rust_controller.get_database_stats()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_database_stats: {e}")
        return jsonify({"error": str(e)}), 500



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
    app.run(host='0.0.0.0', port=5000, debug=True)
