#!/usr/bin/env python3
"""
UnityPy-based Unity asset extractor for Rust crafting data
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

# Make UnityPy import optional
try:
    import UnityPy
    UNITYPY_AVAILABLE = True
    UnityPyEnvironment = UnityPy.Environment
except ImportError:
    UnityPy = None
    UNITYPY_AVAILABLE = False
    UnityPyEnvironment = Any  # Type hint fallback

logger = logging.getLogger(__name__)

@dataclass
class CraftingIngredient:
    """Represents a crafting ingredient"""
    item_id: str
    shortname: str
    amount: float
    is_blueprint: bool = False

@dataclass
class CraftingRecipe:
    """Represents a crafting recipe"""
    item_id: str
    shortname: str
    ingredients: List[CraftingIngredient]
    craft_time: float
    amount_to_create: int
    workbench_level: int
    scrap_required: int
    user_craftable: bool
    is_researchable: bool

class UnityPyExtractor:
    """Handles extraction and parsing of Unity assets using UnityPy for crafting data"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.extracted_dir = data_dir / "unitypy_extracted"
        
    def extract_crafting_data(self, bundle_path: Path) -> Dict[str, Any]:
        """Main method to extract all crafting data from a bundle file using UnityPy"""
        if not UNITYPY_AVAILABLE:
            logger.warning("UnityPy is not available. Unity asset extraction is disabled.")
            return {
                "success": False, 
                "error": "UnityPy is not available in this build. Unity asset extraction is disabled."
            }
            
        try:
            logger.info("Starting UnityPy extraction for crafting data...")
            
            # Create extraction directory
            self.extracted_dir.mkdir(parents=True, exist_ok=True)
            
            # Load the bundle with UnityPy
            logger.info(f"Loading bundle: {bundle_path}")
            env = UnityPy.load(str(bundle_path))
            
            logger.info(f"Loaded {len(env.objects)} objects from bundle")
            
            # Extract item definitions and recipes
            item_definitions = self.extract_item_definitions(env)
            recipes = self.extract_crafting_recipes(env, item_definitions)
            
            # Convert to dictionary format for database storage
            crafting_data = {
                "item_definitions": item_definitions,
                "recipes": []
            }
            
            for recipe in recipes:
                recipe_dict = {
                    "item_id": recipe.item_id,
                    "shortname": recipe.shortname,
                    "ingredients": [
                        {
                            "item_id": ing.item_id,
                            "shortname": ing.shortname,
                            "amount": ing.amount,
                            "is_blueprint": ing.is_blueprint
                        }
                        for ing in recipe.ingredients
                    ],
                    "craft_time": recipe.craft_time,
                    "amount_to_create": recipe.amount_to_create,
                    "workbench_level": recipe.workbench_level,
                    "scrap_required": recipe.scrap_required,
                    "user_craftable": recipe.user_craftable,
                    "is_researchable": recipe.is_researchable
                }
                crafting_data["recipes"].append(recipe_dict)
            
            logger.info(f"Successfully extracted {len(crafting_data['recipes'])} crafting recipes")
            return {
                "success": True,
                "crafting_data": crafting_data,
                "item_count": len(item_definitions),
                "recipe_count": len(crafting_data["recipes"])
            }
            
        except Exception as e:
            logger.error(f"Failed to extract crafting data with UnityPy: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_item_definitions(self, env: UnityPyEnvironment) -> Dict[str, Dict]:
        """Extract ItemDefinition objects using UnityPy"""
        if not UNITYPY_AVAILABLE:
            logger.warning("UnityPy is not available. Cannot extract item definitions.")
            return {}
            
        item_definitions = {}
        
        try:
            logger.info("Extracting ItemDefinition objects...")
            
            for obj in env.objects:
                if obj.type.name == "MonoBehaviour":
                    try:
                        # Read the object data
                        data = obj.read()
                        
                        # Check if this is an ItemDefinition by looking for key fields
                        if hasattr(data, 'itemid') and hasattr(data, 'shortname'):
                            # Get the PathID for this object
                            path_id = str(obj.path_id)
                            
                            # Extract item data
                            item_data = {
                                "itemid": getattr(data, 'itemid', None),
                                "shortname": getattr(data, 'shortname', ''),
                                "displayName": self._get_display_name(data),
                                "displayDescription": self._get_display_description(data),
                                "category": getattr(data, 'category', None),
                                "stackable": getattr(data, 'stackable', 1),
                                "rarity": getattr(data, 'rarity', None)
                            }
                            
                            item_definitions[path_id] = item_data
                            logger.debug(f"Parsed item: {item_data.get('shortname', 'unknown')} (PathID: {path_id})")
                            
                    except Exception as e:
                        logger.debug(f"Failed to parse object {obj.path_id}: {e}")
                        continue
            
            logger.info(f"Successfully extracted {len(item_definitions)} item definitions")
            
            # Log some sample items
            sample_items = list(item_definitions.items())[:5]
            for path_id, item_data in sample_items:
                logger.info(f"Sample item: {item_data.get('shortname', 'unknown')} (PathID: {path_id})")
            
            return item_definitions
            
        except Exception as e:
            logger.error(f"Failed to extract item definitions: {e}")
            return {}
    
    def extract_crafting_recipes(self, env: UnityPyEnvironment, item_definitions: Dict[str, Dict]) -> List[CraftingRecipe]:
        """Extract ItemBlueprint objects using UnityPy - Comprehensive approach"""
        if not UNITYPY_AVAILABLE:
            logger.warning("UnityPy is not available. Cannot extract crafting recipes.")
            return []
            
        recipes = []
        
        try:
            logger.info("Extracting ItemBlueprint objects...")
            
            for obj in env.objects:
                if obj.type.name == "MonoBehaviour":
                    try:
                        # Read the object data
                        data = obj.read()
                        
                        # Check if this has ingredients (comprehensive approach - include all recipes)
                        if hasattr(data, 'ingredients') and len(getattr(data, 'ingredients', [])) > 0:
                            # Extract ingredients
                            ingredients = []
                            for ingredient_data in getattr(data, 'ingredients', []):
                                # UnityPy should handle the reference properly
                                if hasattr(ingredient_data, 'itemDef') and ingredient_data.itemDef:
                                    # Get the referenced item definition
                                    ref_obj = ingredient_data.itemDef
                                    if hasattr(ref_obj, 'path_id'):
                                        ref_path_id = str(ref_obj.path_id)
                                        
                                        if ref_path_id in item_definitions:
                                            item_def = item_definitions[ref_path_id]
                                            ingredient = CraftingIngredient(
                                                item_id=str(item_def.get("itemid", "")),
                                                shortname=item_def.get("shortname", ""),
                                                amount=getattr(ingredient_data, 'amount', 0),
                                                is_blueprint=bool(getattr(ingredient_data, 'isBP', 0))
                                            )
                                            ingredients.append(ingredient)
                                            logger.debug(f"Added ingredient: {ingredient.shortname} (PathID: {ref_path_id})")
                                        else:
                                            logger.debug(f"Could not find item definition for PathID: {ref_path_id}")
                            
                            # Try to determine what item this recipe creates
                            # Follow the m_GameObject reference to find the actual item
                            item_name = ""
                            if hasattr(data, 'm_GameObject') and data.m_GameObject:
                                try:
                                    # Get the GameObject that this blueprint belongs to
                                    game_object = data.m_GameObject
                                    if hasattr(game_object, 'path_id'):
                                        game_obj_path_id = str(game_object.path_id)
                                        
                                        # Find the GameObject in the environment
                                        for env_obj in env.objects:
                                            if str(env_obj.path_id) == game_obj_path_id:
                                                game_obj_data = env_obj.read()
                                                if hasattr(game_obj_data, 'm_Name'):
                                                    item_name = game_obj_data.m_Name
                                                    break
                                except Exception as e:
                                    logger.debug(f"Failed to get GameObject name: {e}")
                            
                            # Fallback: try to get name from the object itself
                            if not item_name and hasattr(data, 'm_Name'):
                                item_name = data.m_Name
                            
                            # Try to find a matching item definition by shortname
                            matching_item_shortname = ""
                            for path_id, item_def in item_definitions.items():
                                if item_def.get("shortname", "").lower() == item_name.lower():
                                    matching_item_shortname = item_def.get("shortname", "")
                                    break
                            
                            # If no exact match, try partial matching (but be more careful)
                            if not matching_item_shortname:
                                best_match = None
                                best_score = 0
                                for path_id, item_def in item_definitions.items():
                                    shortname = item_def.get("shortname", "")
                                    # Calculate a simple similarity score
                                    if item_name.lower() in shortname.lower():
                                        score = len(item_name) / len(shortname)
                                        if score > best_score:
                                            best_score = score
                                            best_match = shortname
                                    elif shortname.lower() in item_name.lower():
                                        score = len(shortname) / len(item_name)
                                        if score > best_score:
                                            best_score = score
                                            best_match = shortname
                                
                                # Only use partial match if it's reasonably good (score > 0.7)
                                if best_match and best_score > 0.7:
                                    matching_item_shortname = best_match
                            
                            # Use the matched shortname or fallback to extracted name
                            final_shortname = matching_item_shortname if matching_item_shortname else item_name
                            
                            logger.debug(f"Processing recipe: {item_name} -> Item: {final_shortname}")
                            
                            # Create recipe
                            recipe = CraftingRecipe(
                                item_id="",  # Will be filled by matching with item definitions
                                shortname=final_shortname,
                                ingredients=ingredients,
                                craft_time=getattr(data, 'time', 0.0),
                                amount_to_create=getattr(data, 'amountToCreate', 1),
                                workbench_level=getattr(data, 'workbenchLevelRequired', 0),
                                scrap_required=getattr(data, 'scrapRequired', 0),
                                user_craftable=bool(getattr(data, 'userCraftable', 0)),
                                is_researchable=bool(getattr(data, 'isResearchable', 0))
                            )
                            
                            recipes.append(recipe)
                            logger.debug(f"Parsed recipe with {len(ingredients)} ingredients for item: {final_shortname}")
                            
                    except Exception as e:
                        logger.debug(f"Failed to parse object {obj.path_id}: {e}")
                        continue
            
            logger.info(f"Successfully extracted {len(recipes)} crafting recipes")
            return recipes
            
        except Exception as e:
            logger.error(f"Failed to extract crafting recipes: {e}")
            return []
    
    def _get_display_name(self, data) -> str:
        """Extract display name from item data"""
        if hasattr(data, 'displayName'):
            display_name = data.displayName
            if isinstance(display_name, dict) and 'english' in display_name:
                return display_name['english']
            elif isinstance(display_name, str):
                return display_name
        return ""
    
    def _get_display_description(self, data) -> str:
        """Extract display description from item data"""
        if hasattr(data, 'displayDescription'):
            display_desc = data.displayDescription
            if isinstance(display_desc, dict) and 'english' in display_desc:
                return display_desc['english']
            elif isinstance(display_desc, str):
                return display_desc
        return ""
