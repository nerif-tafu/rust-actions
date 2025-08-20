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
- **POST** `/craft/id` - Craft item by ID
- **POST** `/craft/name` - Craft item by name
- **POST** `/craft/cancel/id` - Cancel craft by item ID
- **POST** `/craft/cancel/name` - Cancel craft by item name
- **POST** `/craft/cancel-all` - Cancel all crafting

### Player Actions
- **POST** `/player/suicide` - Kill player character
- **POST** `/player/respawn` - Respawn player (optional spawn ID)
- **POST** `/player/auto-run` - Enable auto run
- **POST** `/player/auto-run-jump` - Enable auto run and jump
- **POST** `/player/auto-crouch-attack` - Enable auto crouch and attack

### Chat
- **POST** `/chat/global` - Send message to global chat
- **POST** `/chat/team` - Send message to team chat

### Game Management
- **POST** `/game/quit` - Quit the game
- **POST** `/game/disconnect` - Disconnect from server
- **POST** `/game/connect` - Connect to server

### Inventory
- **POST** `/inventory/stack` - Stack inventory items

### Settings
- **POST** `/settings/look-radius` - Set look at radius
- **POST** `/settings/voice-volume` - Set voice chat volume
- **POST** `/settings/master-volume` - Set master volume
- **POST** `/settings/hud` - Set HUD state (enabled/disabled)

### Input & Clipboard
- **POST** `/input/type-enter` - Type text and press enter
- **POST** `/clipboard/copy-json` - Copy JSON to clipboard

### Item Database
- **GET** `/items` - Get all items
- **GET** `/items/<item_id>` - Get item by ID
- **GET** `/items/name/<name>` - Get item by name
- **GET** `/items/category/<category>` - Get items by category
- **GET** `/items/search?q=<query>` - Search items by name or description
- **POST** `/items` - Add new item
- **PUT** `/items/<item_id>` - Update item
- **DELETE** `/items/<item_id>` - Delete item
- **GET** `/items/categories` - Get all categories
- **GET** `/items/stats` - Get database statistics
- **POST** `/items/load-game-files` - Load items from Rust game files
- **POST** `/items/import-item-manager` - Import items from item manager data

### Steam Integration
- **POST** `/steam/login` - Login to Steam
- **GET** `/steam/status` - Check Steam login status
- **POST** `/steam/update-database` - Update item database using Steam
- **POST** `/steam/reset-database` - Reset the item database
- **GET** `/steam/items` - Get all items from Steam database
- **GET** `/steam/items/<item_id>` - Get item by ID from Steam database
- **GET** `/steam/stats` - Get Steam database statistics
- **GET** `/steam/images/<filename>` - Serve Steam item images

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

**Respawn with specific ID:**
```bash
curl -X POST http://localhost:5000/player/respawn \
  -H "Content-Type: application/json" \
  -d '{"spawn_id": "spawn_point_1"}'
```

**Auto Run:**
```bash
curl -X POST http://localhost:5000/player/auto-run
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
