#!/usr/bin/env python3
"""
Steam Manager for Rust Game Controller
Handles SteamCMD installation, Steam login, and Rust client downloads
"""

import os
import json
import logging
import requests
import subprocess
import platform
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from unitypy_extractor import UnityPyExtractor

logger = logging.getLogger(__name__)

class SteamManager:
    """Manages SteamCMD operations and Rust client downloads"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Use Documents/Rust-Actions folder for data storage
            documents_path = os.path.expanduser("~/Documents")
            data_dir = os.path.join(documents_path, "Rust-Actions")
        
        self.data_dir = Path(data_dir)
        self.database_path = self.data_dir / "itemDatabase.json"
        self.images_dir = self.data_dir / "images"
        self.rust_client_path = self.data_dir / "rustclient"
        self.steamcmd_dir = self.data_dir / "steamcmd"
        self.steam_credentials_path = self.data_dir / "steamCredentials.json"
        
        # Constants
        self.RUST_APP_ID = "252490"  # Rust Client
        self.is_windows = platform.system() == "Windows"
        self.steamcmd_exe = self.steamcmd_dir / ("steamcmd.exe" if self.is_windows else "steamcmd.sh")
        
        # Steam login state
        self.steam_login_state = {
            "loggedIn": False,
            "username": "",
            "timestamp": 0
        }
        
        # Cache for database
        self.item_database_cache = None
        self.last_cache_time = 0
        
        # Unity asset extractor for crafting data
        self.unity_extractor = UnityPyExtractor(self.data_dir)
        
        # Ensure directories exist
        self.ensure_directories_exist()
        
        # Load saved credentials
        self.load_saved_credentials()
    
    def ensure_directories_exist(self):
        """Ensure all required directories exist"""
        logger.info("Ensuring data directories exist...")
        
        dirs_to_create = [
            self.data_dir,
            self.images_dir,
            self.rust_client_path,
            self.steamcmd_dir
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    

    
    def load_saved_credentials(self):
        """Load saved Steam credentials"""
        try:
            if self.steam_credentials_path.exists():
                with open(self.steam_credentials_path, 'r') as f:
                    saved_credentials = json.load(f)
                    self.steam_login_state["username"] = saved_credentials.get("username", "")
                    logger.info(f"Loaded saved Steam username: {self.steam_login_state['username']}")
        except Exception as e:
            logger.error(f"Error loading saved Steam credentials: {e}")
    
    def save_credentials(self, username: str):
        """Save Steam credentials"""
        try:
            credentials = {"username": username}
            with open(self.steam_credentials_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            logger.info(f"Saved Steam username to {self.steam_credentials_path}")
        except Exception as e:
            logger.error(f"Error saving Steam credentials: {e}")
    
    def is_steamcmd_installed(self) -> bool:
        """Check if SteamCMD is installed"""
        if not self.steamcmd_exe.exists():
            return False
        
        # Test if SteamCMD is actually executable
        try:
            if self.is_windows:
                # On Windows, try to run steamcmd with +quit to test if it works
                process = subprocess.run(
                    [str(self.steamcmd_exe), "+quit"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False
                )
                return process.returncode == 0
            else:
                # On Unix, check if file is executable
                return os.access(self.steamcmd_exe, os.X_OK)
        except Exception as e:
            logger.warning(f"Error testing SteamCMD: {e}")
            return False
    
    def install_steamcmd(self, progress_callback=None) -> bool:
        """Download and install SteamCMD"""
        if self.is_steamcmd_installed():
            logger.info("SteamCMD is already installed")
            return True
        
        logger.info("Installing SteamCMD...")
        if progress_callback:
            progress_callback(15, "Downloading SteamCMD...")
        
        try:
            # Download URLs
            if self.is_windows:
                download_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
                download_path = self.steamcmd_dir / "steamcmd.zip"
            else:
                download_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
                download_path = self.steamcmd_dir / "steamcmd.tar.gz"
            
            # Download SteamCMD
            logger.info(f"Downloading from {download_url} to {download_path}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if progress_callback:
                progress_callback(18, "Extracting SteamCMD...")
            
            # Extract the file
            if self.is_windows:
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(self.steamcmd_dir)
            else:
                with tarfile.open(download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.steamcmd_dir)
                
                # Make steamcmd.sh executable
                steamcmd_sh = self.steamcmd_dir / "steamcmd.sh"
                if steamcmd_sh.exists():
                    os.chmod(steamcmd_sh, 0o755)
            
            # Clean up downloaded file
            download_path.unlink()
            
            logger.info("SteamCMD installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install SteamCMD: {e}")
            return False
    
    def run_steamcmd(self, args: list, credentials: Optional[Dict] = None, progress_callback=None) -> bool:
        """Run a SteamCMD command"""
        try:
            cmd_args = args.copy()
            
            # Add login credentials if provided
            if credentials:
                logger.info("Attempting login with provided credentials")
                # Insert login credentials at the start, before any other commands
                cmd_args = ["+login", credentials["username"], credentials["password"]] + cmd_args
            elif self.steam_login_state["loggedIn"] and self.steam_login_state["username"]:
                logger.info(f"Attempting login with cached credentials for {self.steam_login_state['username']}")
                cmd_args = ["+login", self.steam_login_state["username"]] + cmd_args
            else:
                logger.info("No cached credentials available, running without login")
            
            # Build the full command
            cmd = [str(self.steamcmd_exe)] + cmd_args
            
            # Mask password in logs
            log_cmd = " ".join(cmd)
            if credentials and "password" in credentials:
                log_cmd = log_cmd.replace(credentials["password"], "********")
            
            logger.info(f"Running SteamCMD command: {log_cmd}")
            logger.debug(f"Command args: {cmd}")
            
            # Run SteamCMD with shell=True for better compatibility (like Node.js version)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            # Read output in real-time
            stdout_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output = output.strip()
                    stdout_lines.append(output)
                    logger.debug(f"SteamCMD stdout: {output}")
                    if progress_callback:
                        progress_callback(30, f"SteamCMD: {output[:80]}...")
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Get stderr output for debugging
            stderr_output = process.stderr.read() if process.stderr else ""
            if stderr_output:
                logger.error(f"SteamCMD stderr: {stderr_output}")
            
            logger.info(f"SteamCMD process exited with code {return_code}")
            
            if return_code == 0:
                logger.info("SteamCMD command completed successfully")
                return True
            else:
                logger.error(f"SteamCMD process failed with code {return_code}")
                # Log the full stdout output for debugging
                if stdout_lines:
                    logger.error("SteamCMD stdout output:")
                    for line in stdout_lines:
                        logger.error(f"  {line}")
                if stderr_output:
                    logger.error(f"SteamCMD stderr: {stderr_output}")
                
                # Provide specific error messages for common Steam error codes
                if return_code == 5:
                    logger.error("Steam error code 5: App not available. This usually means:")
                    logger.error("  - The Steam account doesn't own Rust (app ID 252490)")
                    logger.error("  - The account is restricted or banned")
                    logger.error("  - Steam Guard is blocking the login")
                elif return_code == 8:
                    logger.error("Steam error code 8: No subscription. The account doesn't own this app.")
                elif return_code == 10:
                    logger.error("Steam error code 10: App not available in this region.")
                
                return False
                
        except Exception as e:
            logger.error(f"Error running SteamCMD: {e}")
            return False
    
    def check_steam_login(self) -> Dict[str, Any]:
        """Check Steam login status"""
        try:
            # Try to detect if we can login with cached credentials by running SteamCMD with just +login command
            username = self.steam_login_state["username"] or ""
            
            # If we don't have a username, we can't check for cached credentials
            if not username:
                logger.info("No username available to check cached login status")
                return {
                    "success": True,
                    "loggedIn": False,
                    "username": "",
                    "message": "First-time setup: Please enter your Steam credentials"
                }
            
            # Try with username to see if it uses cached credentials or asks for password
            command = f'"{self.steamcmd_exe}" +login {username} +quit'
            
            logger.info("Testing SteamCMD cached login...")
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True
            )
            
            stdout = process.stdout
            stderr = process.stderr
            
            if stdout:
                logger.debug(f"SteamCMD login test stdout: {stdout}")
            if stderr:
                logger.error(f"SteamCMD login test stderr: {stderr}")
            
            # Check if login was successful without requiring password
            if ('Logging in using cached credentials' in stdout or 
                (f"Logging in user '{username}'" in stdout and 'password:' not in stdout)):
                
                # Extract username from output if possible
                import re
                username_match = re.search(r"Logging in user '([^']+)'", stdout)
                username = username_match.group(1) if username_match else username
                
                # Update our internal login state
                self.steam_login_state = {
                    "loggedIn": True,
                    "username": username,
                    "timestamp": datetime.now().timestamp()
                }
                
                logger.info(f"Detected valid cached Steam login for: {username}")
                
                return {
                    "success": True,
                    "loggedIn": True,
                    "username": username,
                    "message": f"Logged in as {username}"
                }
            elif any(phrase in stdout for phrase in ["Cached credentials not found", "password:", "FAILED"]):
                # No cached credentials or they're invalid
                logger.info("No valid cached Steam credentials found")
                
                return {
                    "success": True,
                    "loggedIn": False,
                    "username": "",
                    "message": "Steam login required: Please enter your credentials"
                }
            else:
                # Unclear outcome, assume not logged in
                logger.info("Unclear Steam login status, assuming not logged in")
                
                return {
                    "success": True,
                    "loggedIn": False,
                    "username": "",
                    "message": "Steam login required: Unable to determine login status"
                }
                
        except Exception as e:
            logger.error(f"Error checking Steam login: {e}")
            return {
                "success": False,
                "loggedIn": False,
                "username": "",
                "message": f"Error checking login status: {str(e)}"
            }
    
    def steam_login(self, username: str, password: str, twofa_code: Optional[str] = None) -> Dict[str, Any]:
        """Attempt Steam login"""
        try:
            logger.info(f"Attempting Steam login for user: {username}")
            
            # Ensure SteamCMD is installed
            if not self.is_steamcmd_installed():
                logger.info("SteamCMD not found, installing first...")
                if not self.install_steamcmd():
                    return {
                        "success": False,
                        "loggedIn": False,
                        "message": "Failed to install SteamCMD"
                    }
            
            # Verify SteamCMD exists after installation
            if not self.steamcmd_exe.exists():
                logger.error(f"SteamCMD executable not found at: {self.steamcmd_exe}")
                return {
                    "success": False,
                    "loggedIn": False,
                    "message": f"SteamCMD executable not found at: {self.steamcmd_exe}"
                }
            
            # Build the login command
            if twofa_code:
                # Include 2FA code in the command
                command = f'"{self.steamcmd_exe}" +login {username} "{password}" "{twofa_code}" +quit'
                log_command = f'"{self.steamcmd_exe}" +login {username} "********" "********" +quit'
            else:
                # Standard login without 2FA
                command = f'"{self.steamcmd_exe}" +login {username} "{password}" +quit'
                log_command = f'"{self.steamcmd_exe}" +login {username} "********" +quit'
            
            logger.info(f"Running command: {log_command}")
            
            # Run the command using subprocess.run
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if process.stdout:
                logger.debug(f"SteamCMD stdout: {process.stdout}")
            if process.stderr:
                logger.error(f"SteamCMD stderr: {process.stderr}")
            
            if process.returncode != 0:
                logger.error(f"SteamCMD exec error: return code {process.returncode}")
                return {
                    "success": False,
                    "loggedIn": False,
                    "message": f"Steam login failed: return code {process.returncode}"
                }
            
            # Check if login was successful (no 'FAILED' in output)
            if "FAILED" in process.stdout:
                logger.error("Login failed - FAILED found in output")
                return {
                    "success": False,
                    "loggedIn": False,
                    "message": "Invalid password or login failed"
                }
            
            # Update login state
            self.steam_login_state = {
                "loggedIn": True,
                "username": username,
                "timestamp": datetime.now().timestamp()
            }
            
            # Save credentials
            self.save_credentials(username)
            
            logger.info("Steam login successful")
            return {
                "success": True,
                "loggedIn": True,
                "username": username,
                "message": "Steam login successful"
            }
                
        except Exception as e:
            logger.error(f"Error during Steam login: {e}")
            return {
                "success": False,
                "loggedIn": False,
                "message": f"Login error: {str(e)}"
            }
    
    def download_rust_client(self, credentials: Optional[Dict] = None, progress_callback=None) -> bool:
        """Download Rust client files using SteamCMD"""
        try:
            if progress_callback:
                progress_callback(25, "Checking for Rust client files...")
            
            # Check if we already have the required files in any possible location
            steam_apps_path = self.steamcmd_dir / "steamapps" / "common" / "Rust"
            possible_paths = [
                steam_apps_path / "Bundles" / "items",
                steam_apps_path / "RustClient_Data" / "Bundles" / "items",
                self.rust_client_path / "Bundles" / "items",
                self.rust_client_path / "data" / "rustclient" / "Bundles" / "items",
                self.rust_client_path / "RustClient_Data" / "Bundles" / "items"
            ]
            
            for path in possible_paths:
                if path.exists():
                    item_files = list(path.glob("*.json"))
                    if item_files:
                        logger.info(f"Rust client files already downloaded at: {path}")
                        if progress_callback:
                            progress_callback(40, "Rust client files already downloaded")
                        return True
            
            if progress_callback:
                progress_callback(30, "Downloading Rust client files...")
            
            # Download to default Steam apps location (no force_install_dir)
            args = [
                "+app_update", self.RUST_APP_ID,
                "validate",
                "+quit"
            ]
            
            # Run SteamCMD to download Rust client
            if self.run_steamcmd(args, credentials, progress_callback):
                logger.info("Rust client files downloaded successfully!")
                if progress_callback:
                    progress_callback(50, "Rust client files downloaded successfully!")
                return True
            else:
                logger.error("Failed to download Rust client files")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading Rust client files: {e}")
            return False
    
    def process_rust_assets(self, progress_callback=None) -> Dict[str, Any]:
        """Process Rust assets to build the item database"""
        try:
            if progress_callback:
                progress_callback(60, "Processing Rust assets...")
            
            # Look for item json files in the bundles directory
            # First check default Steam apps location, then fallback to custom paths
            steam_apps_path = self.steamcmd_dir / "steamapps" / "common" / "Rust"
            possible_paths = [
                steam_apps_path / "Bundles" / "items",
                steam_apps_path / "RustClient_Data" / "Bundles" / "items",
                self.rust_client_path / "Bundles" / "items",
                self.rust_client_path / "data" / "rustclient" / "Bundles" / "items",
                self.rust_client_path / "RustClient_Data" / "Bundles" / "items"
            ]
            
            items_dir = None
            for path in possible_paths:
                if path.exists():
                    items_dir = path
                    logger.info(f"Found items directory at: {items_dir}")
                    break
            
            if not items_dir:
                # Log all directories in steam_apps_path for debugging
                logger.error(f"Items directory not found. Available directories in {steam_apps_path}:")
                if steam_apps_path.exists():
                    for item in steam_apps_path.iterdir():
                        logger.error(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
                        if item.is_dir():
                            for subitem in item.iterdir():
                                logger.error(f"    - {subitem.name} ({'dir' if subitem.is_dir() else 'file'})")
                else:
                    logger.error(f"Steam apps path does not exist: {steam_apps_path}")
                raise FileNotFoundError(f"Items directory not found in any expected location: {[str(p) for p in possible_paths]}")
            
            # Get all JSON files in the items directory
            item_files = list(items_dir.glob("*.json"))
            
            logger.info(f"Found {len(item_files)} item files in {items_dir}")
            
            if not item_files:
                raise FileNotFoundError("No item files found")
            
            # Process each item file
            items = {}
            item_count = 0
            
            for file_path in item_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        item_data = json.load(f)
                    
                    # Use the numeric itemid as the key
                    item_id = str(item_data.get("itemid", ""))
                    
                    if item_id:
                        items[item_id] = {
                            "id": item_id,
                            "name": item_data.get("Name", file_path.stem),
                            "description": item_data.get("Description", ""),
                            "category": item_data.get("Category", "Uncategorized"),
                            "numericId": item_data.get("itemid"),
                            "shortname": item_data.get("shortname", ""),
                            "image": f"/api/items/images/{item_data.get('shortname', '')}.png",
                            "lastUpdated": datetime.now().isoformat()
                        }
                        
                        item_count += 1
                        
                        # Update progress every 100 items
                        if item_count % 100 == 0:
                            progress = min(int((item_count / len(item_files)) * 30) + 60, 90)
                            if progress_callback:
                                progress_callback(progress, f"Processed {item_count} of {len(item_files)} items")
                
                except Exception as e:
                    logger.error(f"Error processing item file {file_path}: {e}")
                    continue
            
            # Save the database to disk
            database = {
                "metadata": {
                    "itemCount": item_count,
                    "lastUpdated": datetime.now().isoformat(),
                    "rustAppId": self.RUST_APP_ID
                },
                "items": items
            }
            
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
            
            # Copy image files
            self.copy_item_images(progress_callback)
            
            logger.info(f"Successfully processed {item_count} items")
            
            return {
                "success": True,
                "message": f"Database updated with {item_count} items",
                "itemCount": item_count
            }
            
        except Exception as e:
            logger.error(f"Error processing item files: {e}")
            return {
                "success": False,
                "message": f"Error processing items: {str(e)}"
            }
    
    def copy_item_images(self, progress_callback=None):
        """Copy item images from Rust client to our images directory"""
        try:
            if progress_callback:
                progress_callback(90, "Copying item images...")
            
            # Use the same path detection logic as process_rust_assets
            steam_apps_path = self.steamcmd_dir / "steamapps" / "common" / "Rust"
            possible_paths = [
                steam_apps_path / "Bundles" / "items",
                steam_apps_path / "RustClient_Data" / "Bundles" / "items",
                self.rust_client_path / "Bundles" / "items",
                self.rust_client_path / "data" / "rustclient" / "Bundles" / "items",
                self.rust_client_path / "RustClient_Data" / "Bundles" / "items"
            ]
            
            item_images_dir = None
            for path in possible_paths:
                if path.exists():
                    item_images_dir = path
                    break
            
            if not item_images_dir:
                logger.warning("Items directory not found for image copying")
                return
            
            png_files = list(item_images_dir.glob("*.png"))
            
            logger.info(f"Found {len(png_files)} item images in {item_images_dir}")
            
            for png_file in png_files:
                dest_path = self.images_dir / png_file.name
                import shutil
                shutil.copy2(png_file, dest_path)
            
            logger.info(f"Copied {len(png_files)} item images to {self.images_dir}")
            
        except Exception as e:
            logger.error(f"Error copying item images: {e}")
            # Continue even if image copying fails
    
    def update_item_database(self, credentials: Optional[Dict] = None, progress_callback=None) -> Dict[str, Any]:
        """Update the item database"""
        try:
            # Start the update process
            if progress_callback:
                progress_callback(5, "Starting database update...")
            
            # Make sure directories exist
            self.ensure_directories_exist()
            
            # Install SteamCMD if necessary
            if not self.is_steamcmd_installed():
                if not self.install_steamcmd(progress_callback):
                    return {
                        "success": False,
                        "message": "Failed to install SteamCMD"
                    }
            
            # If no credentials provided, check if we're logged in
            if not credentials:
                login_status = self.check_steam_login()
                
                if not login_status["loggedIn"]:
                    if progress_callback:
                        progress_callback(0, f"Steam login required: {login_status['message']}")
                    return {
                        "success": False,
                        "requireSteamLogin": True,
                        "message": login_status["message"]
                    }
                
                # We're logged in, no need for explicit credentials
                logger.info(f"Using existing Steam login for user: {login_status['username']}")
            
            # Download Rust client if necessary
            if not self.download_rust_client(credentials, progress_callback):
                return {
                    "success": False,
                    "message": "Failed to download Rust client files"
                }
            
            # Process Rust assets
            result = self.process_rust_assets(progress_callback)
            
            # Copy item images from Rust client to our images directory
            self.copy_item_images(progress_callback)
            
            # Extract crafting data from Unity bundles
            # Find the items.preload.bundle file
            bundle_path = self.steamcmd_dir / "steamapps" / "common" / "Rust" / "Bundles" / "shared" / "items.preload.bundle"
            
            if bundle_path.exists():
                crafting_result = self.extract_crafting_data_from_bundles(bundle_path, progress_callback)
            else:
                crafting_result = {"success": False, "error": "Bundle file not found"}
            if crafting_result.get("success"):
                logger.info(f"Successfully extracted {crafting_result.get('recipe_count', 0)} crafting recipes")
            else:
                logger.warning(f"Crafting data extraction failed: {crafting_result.get('error', 'Unknown error')}")
            
            # Update complete
            if progress_callback:
                progress_callback(100, "Database update complete!")
            
            # Clear the cache to force a reload
            self.item_database_cache = None
            
            return {
                "success": True,
                "message": f"Database updated with {result.get('itemCount', 0)} items and {crafting_result.get('recipe_count', 0)} crafting recipes",
                "itemCount": result.get("itemCount", 0),
                "recipeCount": crafting_result.get("recipe_count", 0)
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
            
            # Try direct lookup first
            if id_str in database.get("items", {}):
                return database["items"][id_str]
            
            # If not found, try to find by numericId
            for key, item in database.get("items", {}).items():
                if item.get("numericId") == int(id_str):
                    return item
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting item by ID {item_id}: {e}")
            return None
    
    def get_all_items(self) -> Dict[str, Any]:
        """Get all items from the database"""
        try:
            database = self.load_database()
            return database.get("items", {})
        except Exception as e:
            logger.error(f"Error getting all items: {e}")
            return {}
    
    def get_crafting_recipe(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get crafting recipe for a specific item"""
        try:
            crafting_data_path = self.data_dir / "craftingData.json"
            if not crafting_data_path.exists():
                return None
            
            with open(crafting_data_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
            
            # Search for recipe by item_id or shortname
            for recipe in crafting_data.get("recipes", []):
                if (recipe.get("item_id") == item_id or 
                    recipe.get("shortname") == item_id):
                    return recipe
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get crafting recipe for {item_id}: {e}")
            return None
    
    def get_all_crafting_recipes(self) -> Dict[str, Any]:
        """Get all crafting recipes"""
        try:
            crafting_data_path = self.data_dir / "craftingData.json"
            if not crafting_data_path.exists():
                return {"recipes": []}
            
            with open(crafting_data_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
            
            return crafting_data
            
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
            if "ingredients" in item_data and item_data.get("userCraftable", False):
                recipe_count += 1
                craftable_items += 1
        
        return {
            "itemCount": database.get("metadata", {}).get("itemCount", 0),
            "recipeCount": recipe_count,
            "craftableItems": craftable_items,
            "lastUpdated": database.get("metadata", {}).get("lastUpdated")
        }
    
    def reset_item_database(self) -> Dict[str, Any]:
        """Reset the entire item database and remove all downloaded files"""
        logger.info("Resetting item database and removing all downloaded files...")
        
        dirs_to_remove = [
            self.images_dir,
            self.rust_client_path,
            self.steamcmd_dir
        ]
        
        files_to_remove = [
            self.database_path,
            self.steam_credentials_path,
            self.data_dir / "craftingData.json"  # Remove old crafting data file if it exists
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
        
        # Reset login state
        self.steam_login_state = {
            "loggedIn": False,
            "username": "",
            "timestamp": 0
        }
        
        # Clear cache
        self.item_database_cache = None
        self.last_cache_time = 0
        
        logger.info("Database reset complete")
        return {"success": True}
    
    def extract_crafting_data_from_bundles(self, bundle_path, progress_callback=None) -> Dict[str, Any]:
        """Extract crafting data from Unity bundle files and merge into item database"""
        try:
            if progress_callback:
                progress_callback(70, "Extracting crafting data from Unity bundles...")
            
            # Check if bundle path exists
            if not bundle_path.exists():
                logger.warning(f"Bundle file not found: {bundle_path}")
                return {"success": False, "error": "Bundle file not found"}
            
            logger.info(f"Using bundle file: {bundle_path}")
            
            # Extract crafting data using Unity asset extractor
            result = self.unity_extractor.extract_crafting_data(bundle_path)
            
            if result.get("success"):
                # Merge crafting data into the item database
                merge_result = self.merge_crafting_data_into_database(result["crafting_data"])
                
                if merge_result.get("success"):
                    logger.info(f"Merged {merge_result['recipes_added']} crafting recipes into item database")
                    logger.info(f"Note: Some recipes (like Night Vision Goggles) are hardcoded in the game and not stored in Unity bundles, so they cannot be extracted by UnityPy")
                    if progress_callback:
                        progress_callback(85, f"Merged {merge_result['recipes_added']} crafting recipes")
                else:
                    logger.warning(f"Failed to merge crafting data: {merge_result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract crafting data: {e}")
            return {"success": False, "error": str(e)}
    
    def merge_crafting_data_into_database(self, crafting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge crafting data into the existing item database"""
        try:
            # Load the current item database
            if not self.database_path.exists():
                logger.warning("Item database not found, cannot merge crafting data")
                return {"success": False, "error": "Item database not found"}
            
            with open(self.database_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            items = database.get("items", {})
            recipes = crafting_data.get("recipes", [])
            
            # Create a mapping from shortname to item_id for quick lookup
            shortname_to_item_id = {}
            for item_id, item_data in items.items():
                shortname = item_data.get("shortname", "")
                if shortname:
                    shortname_to_item_id[shortname] = item_id
            
            logger.info(f"Found {len(shortname_to_item_id)} items in database for crafting data matching")
            
            # Process each recipe and add crafting data to matching items
            recipes_added = 0
            recipes_by_item = {}
            
            # Group recipes by item shortname
            for recipe in recipes:
                recipe_shortname = recipe.get("shortname", "")
                if recipe_shortname not in recipes_by_item:
                    recipes_by_item[recipe_shortname] = []
                recipes_by_item[recipe_shortname].append(recipe)
            
            # Process each item's recipes
            for recipe_shortname, item_recipes in recipes_by_item.items():
                # Try to find the item by shortname (exact match first)
                item_id = None
                if recipe_shortname in shortname_to_item_id:
                    item_id = shortname_to_item_id[recipe_shortname]
                else:
                    # Special case mappings for known mismatches
                    special_mappings = {
                        "hat.nvg.item": "nightvisiongoggles",
                        "night.vision.goggles": "nightvisiongoggles",
                        "goggles.nightvision": "nightvisiongoggles",
                        # Weapon mod mappings
                        "extendedmags.item": "weapon.mod.extendedmags",
                        "muzzlebooster.item": "weapon.mod.muzzleboost",
                        "muzzlebrake.item": "weapon.mod.muzzlebrake",
                        "flashlightmod.item": "weapon.mod.flashlight",
                        "holosight.item": "weapon.mod.holosight",
                        "lasersight.item": "weapon.mod.lasersight",
                        "targetingattachment.item": "weapon.mod.targetingattachment",
                        # Tool/Trap mappings
                        "fishing_rod.item": "fishingrod.handmade",
                        "binoculars.item": "tool.binoculars",
                        "landmine.item": "trap.landmine",
                        "MixingTable.item": "mixingtable",
                        "hc_revolver.item": "revolver.hc",
                        # Additional mappings
                        "nailgunnail.item": "ammo.nailgun.nails",
                        "Lead_ArmorInsert.item": "clothing.mod.armorinsert_lead",
                        "fireplace.item": "fireplace.stone",
                        "flute.item": "fun.flute",
                        "legacy.shelter.wood.item": "legacy.shelter.wood",
                        "mixingtable.item": "mixingtable",
                        "detonator.item": "rf.detonator",
                        "mp5.item": "smg.mp5",
                        # New mappings from comprehensive extraction
                        "rocket_launcher.item": "rocket.launcher",
                        "tshirt.long.blue.item": "tshirt.long",
                        "wall.external.high.stone.item": "wall.external.high.stone",
                        "wall.window.bars.wood.item": "wall.window.bars.wood",
                        # Missing items - all found in bundle
                        "bass.item": "fun.bass",
                        "cowbell.item": "fun.cowbell",
                        "guitar.item": "fun.guitar",
                        "jerrycanguitar.item": "fun.jerrycanguitar",
                        "tambourine.item": "fun.tambourine",
                        "trumpet.item": "fun.trumpet",
                        "tuba.item": "fun.tuba",
                        "Wood_ArmorInsert.item": "clothing.mod.armorinsert_wood",
                        "rfpager.item": "rf_pager",
                        "TorpedoStraight.item": "submarine.torpedo.straight",
                        # Additional exact matches found
                        "easter_door_wreath.item": "easterdoorwreath",
                        # Non-craftable in Unity but craftable in database
                        "movember_moustache_card.item": "movembermoustachecard",
                        "spas12.item": "shotgun.spas12",
                        # Electric/Smart items
                        "SmartSwitch.item": "smart.switch",
                        "SmartAlarm.item": "smart.alarm",
                        "electricfurnace.item": "electric.furnace",
                        # Hide item mappings
                        "poncho.hide.item": "attire.hide.poncho",
                        "HideVest.item": "attire.hide.vest",
                        "pants.hide.item": "attire.hide.pants",
                        "HideBoots.item": "attire.hide.boots",
                        "halterneck.hide.item": "attire.hide.helterneck",
                        "HideSkirt.item": "attire.hide.skirt",
                        "electrical.modularcarlift.item": "modularcarlift",
                        "electrical.heater.item": "electric.heater",
                        "electrical.random.switch.item": "electric.random.switch",
                        "electrical.blocker.item": "electric.blocker",
                        # Additional electric items with different naming patterns
                        "RFReceiver.item": "electric.rf.receiver",
                        "RFBroadcaster.item": "electric.rf.broadcaster",
                        "Splitter.item": "electric.splitter",
                        "switch.item": "electric.switch",
                        "timer.item": "electric.timer",
                        "counter.item": "electric.counter",
                        # New mappings from comprehensive analysis
                        "metalshield.item": "metal.shield",
                        "trophy_2023.item": "trophy2023",
                        "HazmatPlushy.item": "hazmat.plushy",
                        "io.table": "iotable",
                        "rfpager.item": "rf_pager",
                        "homing_missile_launcher.item": "homingmissile.launcher",
                        "water.pump.item": "waterpump",
                        "FluidSplitter.item": "fluid.splitter",
                        "industrialcombiner.item": "industrial.combiner",
                        "Hazmat_Suit.item": "hazmatsuit",
                        "chineselantern_white.item": "chineselanternwhite",
                        "woodenshield.item": "wooden.shield",
                        "discordtrophy.item": "discord.trophy",
                        "skull_door_knocker.item": "skulldoorknocker",
                        "mini_crossbow.item": "minicrossbow",
                        "vendingmachine.item": "vending.machine",
                        "industrialconveyor.item": "industrial.conveyor",
                        "waterpurifier.item": "water.purifier",
                        "Hazmat_Youtooz.item": "hazmatyoutooz",
                        "skulltrophy.item": "skull.trophy",
                        "StorageMonitor.item": "storage.monitor",
                        "industrialsplitter.item": "industrial.splitter",
                        "bota_bag.item": "botabag",
                        "poweredwaterpurifier.item": "powered.water.purifier",
                        "HeavyScientist_Youtooz.item": "heavyscientistyoutooz",
                        "waterbarrel.item": "water.barrel",
                        "fluidswitch.item": "fluid.switch",
                        "connectedspeaker.item": "connected.speaker",
                        "industrialcrafter.item": "industrial.crafter",
                        "sparkplugs3.item": "sparkplug3",
                        "sparkplugs2.item": "sparkplug2",
                        "sparkplugs1.item": "sparkplug1",
                        "reinforcedwoodshield.item": "reinforced.wooden.shield",
                        "pistons3.item": "piston3",
                        "pistons1.item": "piston1",
                        "pistons2.item": "piston2",
                        "valves1.item": "valve1",
                        "valves2.item": "valve2",
                        "valves3.item": "valve3",
                        "boomboxportable.item": "fun.boomboxportable",
                        "hat.deerskullmask.item": "deer.skull.mask",
                        "double_doorgarland.item": "xmas.double.door.garland",
                        "wall.external.high.wood.item": "wall.external.high",
                        "repair_bench.item": "box.repair.bench",
                        "graveyardfence.item": "wall.graveyard.fence",
                        "instant_camera.item": "tool.instant_camera",
                        "windowgarland.item": "xmas.window.garland",
                        "GiantCandyCane.item": "giantcandycanedecor",
                        "doorgarland.item": "xmas.door.garland",
                        "flashlight.item": "flashlight.held",
                        "movember_moustache_style01.item": "movembermoustache",
                        "ammo_rifle_fire.item": "ammo.rifle.incendiary",
                        "HitchTrough.item": "hitchtroughcombo",
                        "romancandle.violet.item": "firework.romancandle.violet",
                        "halfheight_salvaged_bamboo_shelves.item": "salvaged.bamboo.shelves",
                        # Custom SMG mapping
                        "smg.item": "smg.2"
                    }
                    
                    if recipe_shortname in special_mappings:
                        mapped_shortname = special_mappings[recipe_shortname]
                        if mapped_shortname in shortname_to_item_id:
                            item_id = shortname_to_item_id[mapped_shortname]
                            logger.debug(f"Special mapping: {recipe_shortname} -> {mapped_shortname}")
                    
                    # If no special mapping, try normalized shortname (remove .item suffix and replace underscores with dots)
                    if item_id is None:
                        normalized_shortname = recipe_shortname.replace('.item', '').replace('_', '.')
                        if normalized_shortname in shortname_to_item_id:
                            item_id = shortname_to_item_id[normalized_shortname]
                        else:
                            # Try reverse normalization (replace dots with underscores and add .item)
                            reverse_shortname = recipe_shortname.replace('.', '_') + '.item'
                            if reverse_shortname in shortname_to_item_id:
                                item_id = shortname_to_item_id[reverse_shortname]
                            else:
                                # Try partial matching
                                for db_shortname, db_item_id in shortname_to_item_id.items():
                                    if (recipe_shortname.lower() in db_shortname.lower() or 
                                        db_shortname.lower() in recipe_shortname.lower()):
                                        item_id = db_item_id
                                        logger.debug(f"Partial match: {recipe_shortname} -> {db_shortname}")
                                        break
                
                if item_id:
                    item_data = items[item_id]
                    
                    # Find the best recipe (prefer user_craftable=True, then shortest craft time)
                    best_recipe = None
                    for recipe in item_recipes:
                        if recipe.get("user_craftable", False):
                            if best_recipe is None or recipe.get("craft_time", 999) < best_recipe.get("craft_time", 999):
                                best_recipe = recipe
                    
                    # If no user_craftable recipe found, use the first one
                    if best_recipe is None and item_recipes:
                        best_recipe = item_recipes[0]
                    
                    if best_recipe:
                        # Add crafting data to the item
                        item_data["userCraftable"] = best_recipe.get("user_craftable", False)
                        item_data["amountToCreate"] = best_recipe.get("amount_to_create", 1)
                        
                        # Convert ingredients to the format you specified
                        ingredients = []
                        for ingredient in best_recipe.get("ingredients", []):
                            ingredient_shortname = ingredient.get("shortname", "")
                            ingredient_item_id = ingredient.get("item_id", "")
                            
                            # Use the item_id directly from the UnityPy extraction
                            if ingredient_item_id:
                                try:
                                    # Convert string item_id to int
                                    numeric_id = int(ingredient_item_id)
                                    ingredients.append({
                                        "id": numeric_id,
                                        "amount": ingredient.get("amount", 0)
                                    })
                                    logger.debug(f"Added ingredient: {ingredient_shortname} (ID: {numeric_id})")
                                except ValueError:
                                    logger.debug(f"Invalid item_id for ingredient {ingredient_shortname}: {ingredient_item_id}")
                            else:
                                logger.debug(f"No item_id for ingredient: {ingredient_shortname}")
                        
                        item_data["ingredients"] = ingredients
                        recipes_added += 1
                        
                        logger.debug(f"Added crafting data to item: {recipe_shortname} (ID: {item_id}) with {len(ingredients)} ingredients")
                else:
                    logger.debug(f"Could not find item for recipe: {recipe_shortname}")
            
            # Save the updated database
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
            
            # Clear cache to force reload
            self.item_database_cache = None
            self.last_cache_time = 0
            
            logger.info(f"Successfully merged {recipes_added} crafting recipes into item database")
            return {
                "success": True,
                "recipes_added": recipes_added,
                "total_recipes": len(recipes)
            }
            
        except Exception as e:
            logger.error(f"Failed to merge crafting data into database: {e}")
            return {"success": False, "error": str(e)}
    
    def test_steamcmd_installation(self) -> Dict[str, Any]:
        """Test SteamCMD installation and provide detailed information"""
        try:
            logger.info("Testing SteamCMD installation...")
            
            result = {
                "steamcmd_exists": self.steamcmd_exe.exists(),
                "steamcmd_path": str(self.steamcmd_exe),
                "steamcmd_absolute_path": str(self.steamcmd_exe.absolute()) if self.steamcmd_exe.exists() else None,
                "is_executable": False,
                "test_result": None,
                "error": None
            }
            
            if not result["steamcmd_exists"]:
                result["error"] = "SteamCMD executable not found"
                return result
            
            # Test if it's executable
            try:
                if self.is_windows:
                    # Test with a simple command
                    process = subprocess.run(
                        [str(self.steamcmd_exe), "+quit"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        shell=False
                    )
                    result["is_executable"] = process.returncode == 0
                    result["test_result"] = {
                        "return_code": process.returncode,
                        "stdout": process.stdout,
                        "stderr": process.stderr
                    }
                else:
                    result["is_executable"] = os.access(self.steamcmd_exe, os.X_OK)
            except Exception as e:
                result["error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing SteamCMD installation: {e}")
            return {
                "steamcmd_exists": False,
                "steamcmd_path": str(self.steamcmd_exe),
                "steamcmd_absolute_path": None,
                "is_executable": False,
                "test_result": None,
                "error": str(e)
            }

# Global Steam manager instance
steam_manager = SteamManager()
