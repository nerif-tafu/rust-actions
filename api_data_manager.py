#!/usr/bin/env python3
"""
API-based Data Manager for Rust Game Controller
Replaces steam_manager and unitypy_extractor with API calls to rust-api.tafu.casa
"""

import os
import json
import logging
import requests
import zipfile
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class APIDataManager:
    """Manages Rust game data through API calls instead of local extraction"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Use Documents/Rust-Actions folder for data storage
            documents_path = os.path.expanduser("~/Documents")
            data_dir = os.path.join(documents_path, "Rust-Actions")
        
        self.data_dir = Path(data_dir)
        self.database_path = self.data_dir / "itemDatabase.json"
        self.images_dir = self.data_dir / "images"
        self.crafting_data_path = self.data_dir / "craftingData.json"
        
        # API endpoints
        self.API_BASE_URL = "https://rust-api.tafu.casa"
        self.ITEMS_ENDPOINT = f"{self.API_BASE_URL}/api/items"
        self.IMAGES_ENDPOINT = f"{self.API_BASE_URL}/api/images/download-all"
        
        # API configuration
        self.ITEMS_LIMIT = 10000
        self.ITEMS_OFFSET = 0
        
        # Cache for database
        self.item_database_cache = None
        self.last_cache_time = 0
        self.crafting_data_cache = None
        self.last_crafting_cache_time = 0
        
        # Ensure directories exist
        self.ensure_directories_exist()
    
    def set_items_limit(self, limit: int, offset: int = 0):
        """Set the limit and offset for items API calls"""
        self.ITEMS_LIMIT = limit
        self.ITEMS_OFFSET = offset
        logger.info(f"Updated items API limit to {limit} and offset to {offset}")
    
    def get_items_limit_info(self) -> Dict[str, int]:
        """Get current limit and offset configuration"""
        return {
            "limit": self.ITEMS_LIMIT,
            "offset": self.ITEMS_OFFSET
        }
    
    def ensure_directories_exist(self):
        """Ensure all required directories exist"""
        logger.info("Ensuring data directories exist...")
        
        dirs_to_create = [
            self.data_dir,
            self.images_dir
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    
    def fetch_items_from_api(self) -> Dict[str, Any]:
        """Fetch all items from the Rust API"""
        try:
            # Build URL with limit and offset parameters
            url = f"{self.ITEMS_ENDPOINT}?limit={self.ITEMS_LIMIT}&offset={self.ITEMS_OFFSET}"
            logger.info(f"Fetching items from Rust API: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items_data = data.get("items", [])
            
            # Log sample data for debugging
            if items_data and len(items_data) > 0:
                sample_item = items_data[0]
                logger.info(f"Sample API item structure: {sample_item}")
                if sample_item.get("ingredients"):
                    logger.info(f"Sample ingredients structure: {sample_item['ingredients'][:2]}")
            
            logger.info(f"Successfully fetched {len(items_data)} items from API")
            return {"success": True, "items": items_data}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch items from API: {e}")
            return {"success": False, "error": f"API request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return {"success": False, "error": f"Invalid API response: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching items: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def download_images_from_api(self, progress_callback=None) -> Dict[str, Any]:
        """Download all item images from the Rust API"""
        try:
            if progress_callback:
                progress_callback(0, "Downloading images from API...")
            
            logger.info("Downloading images from Rust API...")
            
            # Download the zip file
            response = requests.get(self.IMAGES_ENDPOINT, stream=True, timeout=60)
            response.raise_for_status()
            
            # Save the zip file temporarily
            zip_path = self.data_dir / "images.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if progress_callback:
                progress_callback(50, "Extracting images...")
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.images_dir)
            
            # Clean up the zip file
            zip_path.unlink()
            
            # Count extracted images
            image_files = list(self.images_dir.glob("*.png"))
            
            if progress_callback:
                progress_callback(100, f"Downloaded {len(image_files)} images")
            
            logger.info(f"Successfully downloaded and extracted {len(image_files)} images")
            return {"success": True, "image_count": len(image_files)}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download images from API: {e}")
            return {"success": False, "error": f"API request failed: {str(e)}"}
        except zipfile.BadZipFile as e:
            logger.error(f"Failed to extract images zip: {e}")
            return {"success": False, "error": f"Invalid zip file: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error downloading images: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def convert_api_items_to_database_format(self, api_items: List[Dict]) -> Dict[str, Any]:
        """Convert API items format to our database format"""
        try:
            items = {}
            item_count = 0
            
            for api_item in api_items:
                try:
                    # Extract item data from API response
                    item_id = str(api_item.get("itemid", ""))
                    shortname = api_item.get("shortname", "")
                    display_name = api_item.get("displayName", "")
                    category = api_item.get("categoryName", "Uncategorized")
                    stackable = api_item.get("stackable", 1)
                    volume = api_item.get("volume", 0)
                    craft_time = api_item.get("craftTime", 0)
                    amount_to_create = api_item.get("amountToCreate", 1)
                    workbench_level = api_item.get("workbenchLevelRequired", 0)
                    
                    # Process ingredients
                    ingredients = []
                    api_ingredients = api_item.get("ingredients", [])
                    for ingredient in api_ingredients:
                        ingredient_item = ingredient.get("itemDef", {})
                        ingredient_shortname = ingredient_item.get("shortname", "")
                        ingredient_amount = ingredient.get("amount", 0)
                        
                        # Find the ingredient's itemid in our database
                        ingredient_itemid = None
                        for search_item in api_items:
                            if search_item.get("shortname") == ingredient_shortname:
                                ingredient_itemid = search_item.get("itemid")
                                break
                        
                        if ingredient_itemid is not None:
                            ingredients.append({
                                "id": str(ingredient_itemid),  # Ensure ingredient ID is string to match item ID format
                                "amount": ingredient_amount
                            })
                        else:
                            # Log missing ingredient for debugging
                            logger.warning(f"Could not find itemid for ingredient: {ingredient_shortname}")
                    
                    # Determine if item is craftable
                    user_craftable = len(ingredients) > 0
                    
                    if item_id:
                        items[item_id] = {
                            "id": item_id,
                            "name": display_name or shortname,
                            "description": "",  # API doesn't provide descriptions
                            "category": category,
                            "numericId": api_item.get("itemid"),
                            "shortname": shortname,
                            "image": f"/api/items/images/{shortname}.png",
                            "lastUpdated": datetime.now().isoformat(),
                            "stackable": stackable,
                            "volume": volume,
                            "userCraftable": user_craftable,
                            "craftTime": craft_time,
                            "amountToCreate": amount_to_create,
                            "workbenchLevel": workbench_level,
                            "ingredients": ingredients
                        }
                        
                        item_count += 1
                
                except Exception as e:
                    logger.error(f"Error processing API item {api_item.get('shortname', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully converted {item_count} items to database format")
            return items
            
        except Exception as e:
            logger.error(f"Error converting API items to database format: {e}")
            return {}
    
    def update_item_database(self, progress_callback=None) -> Dict[str, Any]:
        """Update the item database from the API"""
        try:
            if progress_callback:
                progress_callback(10, "Starting database update from API...")
            
            # Fetch items from API
            api_result = self.fetch_items_from_api()
            if not api_result.get("success"):
                return {
                    "success": False,
                    "message": f"Failed to fetch items from API: {api_result.get('error')}"
                }
            
            if progress_callback:
                progress_callback(30, "Converting API data to database format...")
            
            # Convert API items to our database format
            items = self.convert_api_items_to_database_format(api_result["items"])
            
            if progress_callback:
                progress_callback(50, "Saving database...")
            
            # Save the database to disk
            database = {
                "metadata": {
                    "itemCount": len(items),
                    "lastUpdated": datetime.now().isoformat(),
                    "source": "rust-api.tafu.casa",
                    "apiEndpoint": self.ITEMS_ENDPOINT
                },
                "items": items
            }
            
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
            
            if progress_callback:
                progress_callback(70, "Downloading images...")
            
            # Download images
            images_result = self.download_images_from_api(progress_callback)
            
            if progress_callback:
                progress_callback(100, "Database update complete!")
            
            # Clear the cache to force a reload
            self.item_database_cache = None
            self.crafting_data_cache = None
            
            return {
                "success": True,
                "message": f"Database updated with {len(items)} items from API",
                "itemCount": len(items),
                "imageCount": images_result.get("image_count", 0) if images_result.get("success") else 0
            }
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def load_database(self) -> Dict[str, Any]:
        """Load the item database from disk"""
        try:
            # Check if cache is still valid (less than 5 minutes old)
            now = datetime.now().timestamp()
            if self.item_database_cache and (now - self.last_cache_time < 300):
                return self.item_database_cache
            
            # Load database from disk
            if self.database_path.exists():
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.item_database_cache = data
                self.last_cache_time = now
                return data
            
            # Database doesn't exist yet - return empty database
            logger.info("Item database not found, returning empty database")
            return {"metadata": {"itemCount": 0}, "items": {}}
            
        except Exception as e:
            logger.error(f"Error loading item database: {e}")
            return {"metadata": {"itemCount": 0}, "items": {}}
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item data by ID"""
        try:
            database = self.load_database()
            id_str = str(item_id)
            
            # Try direct lookup first (string key)
            if id_str in database.get("items", {}):
                return database["items"][id_str]
            
            # If not found, try to find by numericId
            try:
                numeric_id = int(id_str)
                for key, item in database.get("items", {}).items():
                    if item.get("numericId") == numeric_id:
                        return item
            except ValueError:
                # id_str is not a valid integer, skip numeric lookup
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting item by ID {item_id}: {e}")
            return None
    
    def get_item_by_numeric_id(self, numeric_id: int) -> Optional[Dict[str, Any]]:
        """Get item data by numeric ID (for compatibility with crafting system)"""
        try:
            database = self.load_database()
            
            for key, item in database.get("items", {}).items():
                if item.get("numericId") == numeric_id:
                    return item
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting item by numeric ID {numeric_id}: {e}")
            return None
    
    def get_all_items(self) -> Dict[str, Any]:
        """Get all items from the database"""
        try:
            database = self.load_database()
            return database.get("items", {})
        except Exception as e:
            logger.error(f"Error getting all items: {e}")
            return {}
    
    def get_all_items_by_numeric_id(self) -> Dict[int, Any]:
        """Get all items indexed by numeric ID for crafting system compatibility"""
        try:
            database = self.load_database()
            items_by_numeric = {}
            
            for key, item in database.get("items", {}).items():
                numeric_id = item.get("numericId")
                if numeric_id is not None:
                    items_by_numeric[numeric_id] = item
            
            return items_by_numeric
            
        except Exception as e:
            logger.error(f"Error getting items by numeric ID: {e}")
            return {}
    
    def debug_missing_item(self, item_id: str) -> Dict[str, Any]:
        """Debug information about a missing item"""
        try:
            database = self.load_database()
            items = database.get("items", {})
            
            # Check if item exists by string ID
            if str(item_id) in items:
                return {"found": True, "by": "string_id", "item": items[str(item_id)]}
            
            # Check if item exists by numeric ID
            try:
                numeric_id = int(item_id)
                for key, item in items.items():
                    if item.get("numericId") == numeric_id:
                        return {"found": True, "by": "numeric_id", "item": item}
            except ValueError:
                pass
            
            # Item not found, return debug info
            return {
                "found": False,
                "searched_id": item_id,
                "total_items": len(items),
                "sample_keys": list(items.keys())[:5],
                "sample_numeric_ids": [item.get("numericId") for item in list(items.values())[:5] if item.get("numericId")]
            }
            
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def get_crafting_recipe(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get crafting recipe for a specific item"""
        try:
            item = self.get_item_by_id(item_id)
            if not item:
                return None
            
            # Check if the item has crafting data
            if item.get("userCraftable") and item.get("ingredients"):
                return {
                    "item_id": item.get("id"),
                    "shortname": item.get("shortname"),
                    "ingredients": item.get("ingredients", []),
                    "craft_time": item.get("craftTime", 0),
                    "amount_to_create": item.get("amountToCreate", 1),
                    "workbench_level": item.get("workbenchLevel", 0),
                    "user_craftable": item.get("userCraftable", False)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get crafting recipe for {item_id}: {e}")
            return None
    
    def get_all_crafting_recipes(self) -> Dict[str, Any]:
        """Get all crafting recipes"""
        try:
            database = self.load_database()
            items = database.get("items", {})
            
            recipes = []
            for item_id, item_data in items.items():
                if item_data.get("userCraftable") and item_data.get("ingredients"):
                    recipe = {
                        "item_id": item_data.get("id"),
                        "shortname": item_data.get("shortname"),
                        "ingredients": item_data.get("ingredients", []),
                        "craft_time": item_data.get("craftTime", 0),
                        "amount_to_create": item_data.get("amountToCreate", 1),
                        "workbench_level": item_data.get("workbenchLevel", 0),
                        "user_craftable": item_data.get("userCraftable", False)
                    }
                    recipes.append(recipe)
            
            return {"recipes": recipes}
            
        except Exception as e:
            logger.error(f"Failed to get all crafting recipes: {e}")
            return {"recipes": []}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        database = self.load_database()
        
        # Count items with crafting data
        items = database.get("items", {})
        recipe_count = 0
        craftable_items = 0
        
        for item_data in items.values():
            if item_data.get("ingredients") and item_data.get("userCraftable"):
                recipe_count += 1
                craftable_items += 1
        
        return {
            "itemCount": database.get("metadata", {}).get("itemCount", 0),
            "recipeCount": recipe_count,
            "craftableItems": craftable_items,
            "lastUpdated": database.get("metadata", {}).get("lastUpdated"),
            "source": database.get("metadata", {}).get("source", "API")
        }
    
    def reset_item_database(self) -> Dict[str, Any]:
        """Reset the entire item database and remove all downloaded files"""
        logger.info("Resetting item database and removing all downloaded files...")
        
        dirs_to_remove = [
            self.images_dir
        ]
        
        files_to_remove = [
            self.database_path,
            self.crafting_data_path
        ]
        
        # Remove directories
        for dir_path in dirs_to_remove:
            if dir_path.exists():
                logger.info(f"Removing directory: {dir_path}")
                import shutil
                shutil.rmtree(dir_path, ignore_errors=True)
        
        # Remove files
        for file_path in files_to_remove:
            if file_path.exists():
                logger.info(f"Removing file: {file_path}")
                file_path.unlink()
        
        # Clear cache
        self.item_database_cache = None
        self.crafting_data_cache = None
        self.last_cache_time = 0
        self.last_crafting_cache_time = 0
        
        logger.info("Database reset complete")
        return {"success": True}
    
    def get_craftable_items_for_binds(self) -> List[Dict[str, Any]]:
        """Get craftable items in the format expected by the binds manager"""
        try:
            database = self.load_database()
            craftable_items = []
            
            for item_id, item_data in database.get("items", {}).items():
                # Check if item has ingredients (craftable items)
                if (item_data.get("ingredients") and 
                    len(item_data.get("ingredients", [])) > 0):
                    craftable_items.append({
                        "id": item_id,
                        "numericId": item_data.get("numericId", int(item_id)),
                        "name": item_data.get("name", "Unknown"),
                        "shortname": item_data.get("shortname", "unknown")
                    })
            
            logger.info(f"Found {len(craftable_items)} craftable items for binds")
            return craftable_items
            
        except Exception as e:
            logger.error(f"Error getting craftable items for binds: {e}")
            return []
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test connection to the Rust API"""
        try:
            logger.info("Testing connection to Rust API...")
            
            # Test items endpoint with limit parameters
            items_url = f"{self.ITEMS_ENDPOINT}?limit={self.ITEMS_LIMIT}&offset={self.ITEMS_OFFSET}"
            items_response = requests.get(items_url, timeout=10)
            items_status = items_response.status_code == 200
            
            # Test images endpoint
            images_response = requests.head(self.IMAGES_ENDPOINT, timeout=10)
            images_status = images_response.status_code == 200
            
            return {
                "success": True,
                "items_endpoint": {
                    "url": items_url,
                    "status": items_status,
                    "response_code": items_response.status_code
                },
                "images_endpoint": {
                    "url": self.IMAGES_ENDPOINT,
                    "status": images_status,
                    "response_code": images_response.status_code
                },
                "overall_status": "Connected" if (items_status and images_status) else "Partially Connected"
            }
            
        except Exception as e:
            logger.error(f"Error testing API connection: {e}")
            return {
                "success": False,
                "error": str(e),
                "overall_status": "Failed"
            }

# Global API data manager instance
api_data_manager = APIDataManager()
