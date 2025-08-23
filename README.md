# Rust Game Controller API

A simple Python REST API for controlling actions in the game "Rust". This API provides endpoints for various game actions like crafting, player controls, chat, and game management.

## Features

- **Crafting Management**: Craft items by ID or name, cancel crafting
- **Player Controls**: Suicide, respawn, auto-run, auto-jump, auto-crouch-attack
- **Chat System**: Send messages to global and team chat
- **Game Management**: Connect/disconnect from servers, quit game
- **Inventory Management**: Stack inventory items
- **Settings**: Control volume, HUD, look radius
- **Input Simulation**: Type text and press enter
- **Clipboard Operations**: Copy JSON to clipboard
- **Chat Feedback**: Automatic chat messages for many actions (anti-AFK, continuous stack, crafting cancellation, etc.)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd companion-module-rust-actions
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:

**Option 1: GUI Application (Recommended)**
```bash
python gui.py
```

**Option 2: Command Line Only**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
- **GET** `/health` - Check API health status

### Crafting
- **POST** `/craft/id` - Craft item by ID with quantity
- **POST** `/craft/name` - Craft item by name with quantity
- **POST** `/craft/cancel/id` - Cancel craft by item ID with quantity
- **POST** `/craft/cancel/name` - Cancel craft by item name with quantity
- **POST** `/craft/cancel-all` - Cancel all crafting (includes chat feedback)

### Player Actions
- **POST** `/player/suicide` - Kill player character
- **POST** `/player/kill` - Kill player character only
- **POST** `/player/respawn` - Respawn player with optional spawn ID
- **POST** `/player/respawn-only` - Respawn player only (without killing first)
- **POST** `/player/respawn-random` - Kill and respawn player (random spawn)
- **POST** `/player/respawn-bed` - Kill and respawn at specific sleeping bag
- **POST** `/player/auto-run` - Enable auto run
- **POST** `/player/auto-run-jump` - Enable auto run and jump
- **POST** `/player/auto-crouch-attack` - Enable auto crouch and attack
- **POST** `/player/gesture` - Perform a gesture/emote
- **POST** `/player/noclip` - Toggle noclip on/off
- **POST** `/player/god-mode` - Toggle god mode on/off
- **POST** `/player/set-time` - Set time of day (0, 4, 8, 12, 16, 20, 24)
- **POST** `/player/teleport-marker` - Teleport to marker
- **POST** `/player/combat-log` - Toggle combat log
- **POST** `/player/clear-console` - Clear console
- **POST** `/player/toggle-console` - Toggle console

### Chat
- **POST** `/chat/global` - Send message to global chat
- **POST** `/chat/team` - Send message to team chat

### Game Management
- **POST** `/game/quit` - Quit the game
- **POST** `/game/disconnect` - Disconnect from server
- **POST** `/game/connect` - Connect to server with IP

### Inventory
- **POST** `/inventory/stack` - Stack inventory items
- **POST** `/inventory/toggle-stack` - Enable/disable continuous stack inventory operations (includes chat feedback)

### Settings
- **POST** `/settings/look-radius` - Set look at radius (20.0 or 0.0002)
- **POST** `/settings/voice-volume` - Set voice chat volume (0.0, 0.25, 0.5, 0.75, 1.0)
- **POST** `/settings/master-volume` - Set master volume (0.0, 0.25, 0.5, 0.75, 1.0)
- **POST** `/settings/hud` - Set HUD state (enabled/disabled)

### Input & Clipboard
- **POST** `/input/type-enter` - Type text and press enter
- **POST** `/clipboard/copy-json` - Copy JSON to clipboard

### Anti-AFK
- **POST** `/anti-afk/start` - Start the anti-AFK feature (includes chat feedback)
- **POST** `/anti-afk/stop` - Stop the anti-AFK feature (includes chat feedback)
- **GET** `/anti-afk/status` - Get the current anti-AFK status

### Keyboard Manager
- **GET** `/keyboard-manager/clear-cache` - Clear the keyboard manager's key combination cache

### Binds Manager
- **GET** `/binds-manager/reload-dynamic-binds` - Reload the binds manager's dynamic binds from keys.cfg
- **POST** `/binds-manager/regenerate-cleared` - Regenerate all binds with dynamic binds completely cleared

### Item Database
- **GET** `/items` - Get all items
- **GET** `/items/<item_id>` - Get item by ID
- **GET** `/items/category/<category>` - Get items by category
- **GET** `/items/search?q=<query>` - Search items by name or description
- **GET** `/items/categories` - Get all categories
- **GET** `/items/stats` - Get database statistics

### Steam Integration
- **POST** `/steam/login` - Login to Steam
- **GET** `/steam/status` - Check Steam login status
- **POST** `/steam/update-database` - Update item database using Steam
- **POST** `/steam/reset-database` - Reset the item database
- **GET** `/steam/items` - Get all items from Steam database
- **GET** `/steam/items/<item_id>` - Get item by ID from Steam database
- **GET** `/steam/stats` - Get Steam database statistics
- **GET** `/steam/test-installation` - Test SteamCMD installation
- **GET** `/steam/images/<filename>` - Serve Steam item images

### Steam Crafting Data
- **GET** `/steam/crafting/recipe/<item_id>` - Get crafting recipe for a specific item
- **GET** `/steam/crafting/recipes` - Get all crafting recipes
- **POST** `/steam/update-crafting` - Update crafting data from Unity bundles and merge into item database

## Chat Feedback System

Many API actions automatically send chat feedback messages to inform you when operations are completed. This includes:

- **Anti-AFK**: "Anti-AFK started!" / "Anti-AFK stopped!"
- **Continuous Stack Inventory**: "Continuous stack inventory enabled!" / "Continuous stack inventory disabled!"
- **Cancel All Crafting**: "All crafting cancelled!"
- **Player Actions**: Various feedback messages for auto-run, noclip, god mode, time changes, etc.

These messages are sent using Rust's `chat.add` command and appear in the game's chat interface.

## Usage Examples

### Crafting Items

**Craft by ID:**
```bash
curl -X POST http://localhost:5000/craft/id \
  -H "Content-Type: application/json" \
  -d '{"item_id": "12345", "quantity": 5}'
```

**Craft by Name:**
```bash
curl -X POST http://localhost:5000/craft/name \
  -H "Content-Type: application/json" \
  -d '{"item_name": "Stone Hatchet", "quantity": 1}'
```

### Player Actions

**Suicide:**
```bash
curl -X POST http://localhost:5000/player/suicide
```

**Kill Only:**
```bash
curl -X POST http://localhost:5000/player/kill
```

**Respawn with specific ID:**
```bash
curl -X POST http://localhost:5000/player/respawn \
  -H "Content-Type: application/json" \
  -d '{"spawn_id": "spawn_point_1"}'
```

**Respawn Only (without killing):**
```bash
curl -X POST http://localhost:5000/player/respawn-only
```

**Kill and Respawn Random:**
```bash
curl -X POST http://localhost:5000/player/respawn-random
```

**Kill and Respawn at Bed:**
```bash
curl -X POST http://localhost:5000/player/respawn-bed \
  -H "Content-Type: application/json" \
  -d '{"spawn_id": "bed_123"}'
```

**Auto Run:**
```bash
curl -X POST http://localhost:5000/player/auto-run
```

**Perform Gesture:**
```bash
curl -X POST http://localhost:5000/player/gesture \
  -H "Content-Type: application/json" \
  -d '{"gesture_name": "wave"}'
```

**Toggle Noclip:**
```bash
curl -X POST http://localhost:5000/player/noclip \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'
```

**Toggle God Mode:**
```bash
curl -X POST http://localhost:5000/player/god-mode \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'
```

**Set Time:**
```bash
curl -X POST http://localhost:5000/player/set-time \
  -H "Content-Type: application/json" \
  -d '{"time_hour": 12}'
```

**Teleport to Marker:**
```bash
curl -X POST http://localhost:5000/player/teleport-marker
```

**Toggle Combat Log:**
```bash
curl -X POST http://localhost:5000/player/combat-log
```

**Clear Console:**
```bash
curl -X POST http://localhost:5000/player/clear-console
```

**Toggle Console:**
```bash
curl -X POST http://localhost:5000/player/toggle-console
```

### Chat Messages

**Global Chat:**
```bash
curl -X POST http://localhost:5000/chat/global \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!"}'
```

**Team Chat:**
```bash
curl -X POST http://localhost:5000/chat/team \
  -H "Content-Type: application/json" \
  -d '{"message": "Team message here"}'
```

### Game Management

**Connect to Server:**
```bash
curl -X POST http://localhost:5000/game/connect \
  -H "Content-Type: application/json" \
  -d '{"server_ip": "192.168.1.100:28015"}'
```

**Disconnect:**
```bash
curl -X POST http://localhost:5000/game/disconnect
```

### Inventory Management

**Stack Inventory:**
```bash
curl -X POST http://localhost:5000/inventory/stack \
  -H "Content-Type: application/json" \
  -d '{"iterations": 80}'
```

**Toggle Continuous Stack:**
```bash
curl -X POST http://localhost:5000/inventory/toggle-stack \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'
```

### Anti-AFK

**Start Anti-AFK:**
```bash
curl -X POST http://localhost:5000/anti-afk/start
```

**Stop Anti-AFK:**
```bash
curl -X POST http://localhost:5000/anti-afk/stop
```

**Check Anti-AFK Status:**
```bash
curl -X GET http://localhost:5000/anti-afk/status
```

### Binds Management

**Clear Keyboard Manager Cache:**
```bash
curl -X GET http://localhost:5000/keyboard-manager/clear-cache
```

**Reload Dynamic Binds:**
```bash
curl -X GET http://localhost:5000/binds-manager/reload-dynamic-binds
```

**Regenerate All Binds:**
```bash
curl -X POST http://localhost:5000/binds-manager/regenerate-cleared
```

### Settings

**Set Voice Volume:**
```bash
curl -X POST http://localhost:5000/settings/voice-volume \
  -H "Content-Type: application/json" \
  -d '{"volume": 0.75}'
```

**Set HUD State:**
```bash
curl -X POST http://localhost:5000/settings/hud \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Input Simulation

**Type and Enter:**
```bash
curl -X POST http://localhost:5000/input/type-enter \
  -H "Content-Type: application/json" \
  -d '{"text": "/kill"}'
```

### Clipboard Operations

**Copy JSON to Clipboard:**
```bash
curl -X POST http://localhost:5000/clipboard/copy-json \
  -H "Content-Type: application/json" \
  -d '{"json_data": {"key": "value", "number": 42}}'
```

### Item Database Operations

**Get All Items:**
```bash
curl -X GET http://localhost:5000/items
```

**Get Item by ID:**
```bash
curl -X GET http://localhost:5000/items/stone_hatchet
```

**Get Item by Name:**
```bash
curl -X GET http://localhost:5000/items/name/Stone%20Hatchet
```

**Get Items by Category:**
```bash
curl -X GET http://localhost:5000/items/category/Tools
```

**Search Items:**
```bash
curl -X GET "http://localhost:5000/items/search?q=stone"
```

**Add New Item:**
```bash
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "metal_hatchet",
    "name": "Metal Hatchet",
    "category": "Tools",
    "description": "Advanced metal hatchet for efficient gathering",
    "stack_size": 1,
    "craft_time": 45.0,
    "ingredients": [
      {"item_id": "metal_fragments", "quantity": 200},
      {"item_id": "wood", "quantity": 100}
    ]
  }'
```

**Update Item:**
```bash
curl -X PUT http://localhost:5000/items/stone_hatchet \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description for stone hatchet",
    "craft_time": 25.0
  }'
```

**Delete Item:**
```bash
curl -X DELETE http://localhost:5000/items/metal_hatchet
```

**Get Categories:**
```bash
curl -X GET http://localhost:5000/items/categories
```

**Get Database Statistics:**
```bash
curl -X GET http://localhost:5000/items/stats
```

**Load Items from Game Files:**
```bash
curl -X POST http://localhost:5000/items/load-game-files \
  -H "Content-Type: application/json" \
  -d '{"game_files_path": "/path/to/rust/game/files"}'
```

**Import from Item Manager:**
```bash
curl -X POST http://localhost:5000/items/import-item-manager \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_id": "example_item",
        "name": "Example Item",
        "category": "Example Category",
        "description": "Item description",
        "stack_size": 1,
        "craft_time": 30.0,
        "ingredients": [
          {"item_id": "material1", "quantity": 100}
        ]
      }
    ]
  }'
```

### Steam Integration Operations

**Login to Steam:**
```bash
curl -X POST http://localhost:5000/steam/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_steam_username",
    "password": "your_steam_password"
  }'
```

**Check Steam Status:**
```bash
curl -X GET http://localhost:5000/steam/status
```

**Update Item Database via Steam:**
```bash
curl -X POST http://localhost:5000/steam/update-database
```

**Get Steam Database Stats:**
```bash
curl -X GET http://localhost:5000/steam/stats
```

**Get All Steam Items:**
```bash
curl -X GET http://localhost:5000/steam/items
```

**Get Steam Item by ID:**
```bash
curl -X GET http://localhost:5000/steam/items/2063916636
```

### Steam Crafting Data

**Get Crafting Recipe:**
```bash
curl -X GET http://localhost:5000/steam/crafting/recipe/2063916636
```

**Get All Crafting Recipes:**
```bash
curl -X GET http://localhost:5000/steam/crafting/recipes
```

**Update Crafting Data:**
```bash
curl -X POST http://localhost:5000/steam/update-crafting
```

**Test SteamCMD Installation:**
```bash
curl -X GET http://localhost:5000/steam/test-installation
```

## Response Format

All endpoints return JSON responses with the following structure:

**Success Response:**
```json
{
  "success": true,
  "action": "action_name",
  "message": "Action completed successfully",
  "additional_data": "value"
}
```

**Error Response:**
```json
{
  "error": "Error description"
}
```

## PyInstaller Packaging

To package the application with PyInstaller:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create the icon:
```bash
python create_icon.py
```

3. Create the executable:

**For GUI Application (Recommended):**
```bash
pyinstaller rust_controller_gui.spec
```

**For Command Line Only:**
```bash
pyinstaller rust_controller.spec
```

The executable will be created in the `dist` folder.

### GUI Features

The GUI application provides:
- **System Tray Integration**: Minimizes to system tray when closed
- **Startup with Windows**: Option to automatically start with Windows
- **Real-time Logs**: View server logs in real-time
- **Server Controls**: Start/stop the API server
- **Log Management**: Clear and save logs
- **Quick Access**: Open API in browser directly from GUI

## Development

### Project Structure
```
companion-module-rust-actions/
├── app.py                    # Main Flask application
├── gui.py                    # GUI application with system tray
├── item_database.py          # Item database management
├── steam_manager.py          # Steam integration and SteamCMD management
├── create_icon.py            # Icon generation script
├── requirements.txt          # Python dependencies
├── rust_controller.spec      # PyInstaller spec for CLI version
├── rust_controller_gui.spec  # PyInstaller spec for GUI version
├── rust_items.json          # Item database file (auto-generated)
├── item_pictures/           # Item pictures directory (auto-generated)
├── data/                    # Steam data directory (auto-generated)
│   ├── steamcmd/           # SteamCMD installation
│   ├── rustclient/         # Rust client files
│   ├── images/             # Steam item images
│   ├── itemDatabase.json   # Steam item database
│   └── steamCredentials.json # Steam credentials
├── README.md                # This file
└── .gitignore               # Git ignore file
```

### Adding New Endpoints

1. Add a new method to the `RustGameController` class in `app.py`
2. Create a corresponding Flask route
3. Add proper error handling and validation
4. Update this README with the new endpoint documentation

### TODO

- [ ] Implement actual game interaction logic
- [ ] Add authentication/authorization
- [ ] Add rate limiting
- [ ] Add configuration file support
- [ ] Add logging to file
- [ ] Add unit tests
- [ ] Add Docker support

## License

This project is licensed under the MIT License.

## Disclaimer

This API is for educational and development purposes. Make sure to comply with the game's terms of service and applicable laws when using this software.
