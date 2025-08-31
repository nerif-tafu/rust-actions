import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
import sys
import os
import time
from datetime import datetime
import webbrowser
import subprocess
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import winreg
from steam_manager import steam_manager
import atexit
import pyperclip
import requests

# Configure logging to capture all messages
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class RustControllerGUI:
    def __init__(self):
        # Variables
        self.server_running = False
        self.log_queue = queue.Queue()
        self.startup_enabled = self.check_startup_enabled()
        self.start_minimized_enabled = self.check_start_minimized_enabled()
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.setup_logging()
        
        # Start server in main thread
        self.start_server()
        
        # Wait for server to be fully ready before starting GUI
        self.wait_for_server_ready()
        
        # Start background tasks before GUI
        self.start_background_tasks()
    
        # Run GUI in main thread (simpler and more reliable)
        self._run_gui()
    

    
    def _fetch_database_stats(self):
        """Fetch database statistics (called from background thread)"""
        try:
            response = requests.get("http://localhost:5000/steam/stats", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    item_count = stats.get('itemCount', 0)
                    last_updated = stats.get('lastUpdated', '')
                    if last_updated:
                        # Format the date nicely
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                            return f"Database: {item_count} items (Updated: {date_str})"
                        except:
                            return f"Database: {item_count} items"
                    else:
                        return f"Database: {item_count} items"
                else:
                    return "Database: No data available"
            else:
                return "Database: Server not responding"
        except Exception as e:
            return "Database: Not connected"
    

    
    def check_server_status(self):
        """Check if the server is actually running and responding"""
        if not self.server_running:
            return False
        
        try:
            # Check if server is responding
            response = requests.get("http://localhost:5000/health", timeout=2)
            if response.status_code == 200:
                return True
            else:
                self.server_running = False
                if hasattr(self, 'root') and self.root:
                    self.root.after_idle(lambda: self._update_server_status("Stopped"))
                self.log_message("⚠️ Server is not responding")
                return False
        except:
            self.server_running = False
            if hasattr(self, 'root') and self.root:
                self.root.after_idle(lambda: self._update_server_status("Stopped"))
            self.log_message("⚠️ Server is not responding")
            return False
    
    def _run_gui(self):
        """Run the GUI in the main thread"""
        self.root = tk.Tk()
        self.root.title("Rust Game Controller API")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 500)
        
        # Set window icon using keyfree-companion's exact approach
        def setup_window_icon():
            """Set the window icon using PhotoImage (keyfree-companion method)"""
            try:
                import os
                import sys
                
                # Handle both development and packaged executable paths
                if getattr(sys, 'frozen', False):
                    # Running as executable
                    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                else:
                    # Running as script
                    base_path = os.path.dirname(__file__)
                
                # Try camera.png first (PNG files work better with iconphoto)
                for icon_name in ['camera.png', 'rust_controller.png', 'camera.ico', 'rust_controller.ico']:
                    icon_path = os.path.join(base_path, icon_name)
                    if os.path.exists(icon_path):
                        try:
                            if icon_name.endswith('.png'):
                                # Load and set the icon using PhotoImage (keyfree-companion approach)
                                icon_image = tk.PhotoImage(file=icon_path)
                                self.root.iconphoto(True, icon_image)
                                # Keep a reference to prevent garbage collection
                                self.window_icon = icon_image
                                self.log_message(f"✅ Set window icon using PhotoImage: {icon_name}")
                                return
                            else:
                                # Fallback to iconbitmap for ICO files
                                self.root.iconbitmap(icon_path)
                                self.log_message(f"✅ Set window icon using iconbitmap: {icon_name}")
                                return
                        except Exception as e:
                            self.log_message(f"⚠️ Failed to load {icon_name}: {e}")
                            continue
                
                self.log_message("⚠️ No suitable icon files found")
            except Exception as e:
                self.log_message(f"⚠️ Failed to set window icon: {e}")
        
        # Set the icon immediately using keyfree-companion's method
        setup_window_icon()
        
        # Create GUI
        self.create_widgets()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Start log monitoring
        self.monitor_logs()
        
        # Handle window close and minimize
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Override minimize button to go to system tray
        self.root.bind("<Unmap>", self.on_minimize)
        
        # Also handle the minimize button directly
        self.root.bind("<Configure>", self.on_configure)
        
        # Add keyboard shortcut for minimize to tray (Alt+M)
        self.root.bind("<Alt-m>", lambda e: self.minimize_to_tray())
        self.root.bind("<Alt-M>", lambda e: self.minimize_to_tray())
        
        # Add keyboard shortcut for exit (Ctrl+Q)
        self.root.bind("<Control-q>", lambda e: self.quit_app())
        self.root.bind("<Control-Q>", lambda e: self.quit_app())
        
        # Update server status since server is already running
        if self.server_running:
            self._update_server_status("Running")
        
        # Populate dropdowns immediately since server is ready
        self.refresh_item_dropdowns()
        
        # Check if we should start minimized (either from command line or saved setting)
        should_start_minimized = '--minimized' in sys.argv or self.start_minimized_enabled
        if should_start_minimized:
            # Small delay to ensure everything is ready, then minimize to tray
            self.root.after(500, self.minimize_to_tray)
        

        
        # Start GUI main loop
        self.root.mainloop()
    

    
    def start_background_tasks(self):
        """Start background tasks in a single thread"""
        # Start combined background task thread
        self.background_thread = threading.Thread(target=self._background_task_loop, daemon=True)
        self.background_thread.start()
    
    def _background_task_loop(self):
        """Combined background task loop"""
        last_stats_update = 0
        last_server_check = 0
        
        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Update stats every 30 seconds
                if current_time - last_stats_update >= 30:
                    stats_data = self._fetch_database_stats()
                    if hasattr(self, 'root') and self.root:
                        self.root.after_idle(lambda: self._update_db_stats_display(stats_data))
                    last_stats_update = current_time
                
                # Check server status every 30 seconds
                if current_time - last_server_check >= 30:
                    if self.server_running and not self.check_server_status():
                        if hasattr(self, 'root') and self.root:
                            self.root.after_idle(lambda: self.log_message("⚠️ Server is not responding"))
                    last_server_check = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in background task loop: {e}")
                time.sleep(5)
    
    def setup_logging(self):
        """Setup logging to capture all messages"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Setup queue handler
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(formatter)
        
        # Get root logger and add handler
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.INFO)
        
        # Also capture Flask logs
        flask_logger = logging.getLogger('werkzeug')
        flask_logger.addHandler(queue_handler)
        flask_logger.setLevel(logging.INFO)
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Create menu bar
        self.create_menu_bar()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for two-column layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)  # Left column
        main_frame.columnconfigure(1, weight=1)  # Right column
        main_frame.rowconfigure(1, weight=1)     # Logs row
        
        # Title
        title_label = ttk.Label(main_frame, text="Rust Game Controller API", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Logs frame (left column)
        logs_frame = ttk.LabelFrame(main_frame, text="Server Logs", padding="5")
        logs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10), padx=(0, 5))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=20, 
                                                 font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls frame
        log_controls_frame = ttk.Frame(logs_frame)
        log_controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Clear logs button
        clear_logs_button = ttk.Button(log_controls_frame, text="Clear Logs", 
                                      command=self.clear_logs)
        clear_logs_button.pack(side=tk.LEFT)
        
        # Save logs button
        save_logs_button = ttk.Button(log_controls_frame, text="Save Logs", 
                                     command=self.save_logs)
        save_logs_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(log_controls_frame, text="Auto-scroll", 
                                           variable=self.auto_scroll_var)
        auto_scroll_check.pack(side=tk.RIGHT)
        
        # Info frame (left column)
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="5")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10), padx=(0, 5))
        
        # API info
        api_info = ttk.Label(info_frame, 
                            text="API URL: http://localhost:5000 | Health Check: http://localhost:5000/health")
        api_info.pack(anchor=tk.W)
        
        # Database info
        self.db_stats_var = tk.StringVar(value="Database: Loading...")
        db_info = ttk.Label(info_frame, textvariable=self.db_stats_var)
        db_info.pack(anchor=tk.W)
        
        # Version info
        version_info = ttk.Label(info_frame, text="Version: 1.0.0")
        version_info.pack(anchor=tk.W)
        
        # Steam Login frame (left column)
        steam_frame = ttk.LabelFrame(main_frame, text="Steam Integration", padding="5")
        steam_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10), padx=(0, 5))
        
        # Steam status
        self.steam_status_var = tk.StringVar(value="Checking Steam login...")
        steam_status_label = ttk.Label(steam_frame, textvariable=self.steam_status_var)
        steam_status_label.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Steam login controls
        ttk.Label(steam_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.steam_username_var = tk.StringVar()
        self.steam_username_entry = ttk.Entry(steam_frame, textvariable=self.steam_username_var, width=20)
        self.steam_username_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 5))
        
        ttk.Label(steam_frame, text="Password:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.steam_password_var = tk.StringVar()
        self.steam_password_entry = ttk.Entry(steam_frame, textvariable=self.steam_password_var, show="*", width=20)
        self.steam_password_entry.grid(row=1, column=3, sticky=tk.W, padx=(0, 5))
        
        ttk.Label(steam_frame, text="2FA Code:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.steam_2fa_var = tk.StringVar()
        self.steam_2fa_entry = ttk.Entry(steam_frame, textvariable=self.steam_2fa_var, show="*", width=20)
        self.steam_2fa_entry.grid(row=1, column=5, sticky=tk.W, padx=(0, 5))
        
        # Steam buttons
        self.steam_login_button = ttk.Button(steam_frame, text="Login to Steam", command=self.steam_login)
        self.steam_login_button.grid(row=1, column=6, padx=(5, 0))
        
        self.update_database_button = ttk.Button(steam_frame, text="Update Item Database", command=self.update_item_database)
        self.update_database_button.grid(row=1, column=7, padx=(5, 0))
        
        self.process_assets_button = ttk.Button(steam_frame, text="Process Assets Only", command=self.process_assets_only)
        self.process_assets_button.grid(row=1, column=8, padx=(5, 0))
        
        self.regenerate_binds_button = ttk.Button(steam_frame, text="Regenerate Rust-Actions Binds", command=self.regenerate_rust_actions_binds)
        self.regenerate_binds_button.grid(row=1, column=9, padx=(5, 0))
        
        # Progress bar for database updates
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(steam_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=9, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Progress label
        self.progress_label_var = tk.StringVar(value="")
        progress_label = ttk.Label(steam_frame, textvariable=self.progress_label_var)
        progress_label.grid(row=3, column=0, columnspan=9, sticky=(tk.W, tk.E), pady=(2, 0))
        
        # API Testing Panel (right column) - hidden by default
        self.api_panel_visible = False
        self.create_api_testing_panel(main_frame)
    
    def create_menu_bar(self):
        """Create the menu bar with Server, API, and Launch options"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Server menu
        server_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Server", menu=server_menu)
        server_menu.add_command(label="Start Server", command=self.start_server)
        server_menu.add_command(label="Stop Server", command=self.stop_server)
        
        # API menu
        api_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="API", menu=api_menu)
        api_menu.add_command(label="Show API Testing Panel", command=self.toggle_api_panel)
        api_menu.add_separator()
        api_menu.add_command(label="Open API in Browser", command=self.open_api)
        
        # Launch menu
        launch_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Launch", menu=launch_menu)
        
        # Startup toggle
        launch_menu.add_command(label="Start on Boot: Disabled", command=self.toggle_startup)
        
        # Start minimized toggle
        launch_menu.add_command(label="Start Minimized: Disabled", command=self.toggle_start_minimized)
        
        # Store references for updating menu states
        self.server_menu = server_menu
        self.api_menu = api_menu
        self.launch_menu = launch_menu
        
        # Update menu labels to reflect current state
        self.update_menu_labels()
    
    def test_api_call(self, action, params):
        """Make an API call to test the game control endpoints"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running. Please start the server first.")
            return
        
        # Check if server is actually responding
        if not self.check_server_status():
            messagebox.showwarning("Warning", "Server is not responding. Please check the server status.")
            return
        
        # Get the command delay from the GUI
        try:
            delay_ms = int(self.command_delay_var.get())
            if delay_ms > 0:
                # Log that command is being delayed
                self.log_message(f"Command delayed: {action.replace('_', ' ').title()} will execute in {delay_ms}ms")
                # Schedule the API call with delay
                self.root.after(delay_ms, lambda: self._execute_api_call(action, params))
                return
            elif delay_ms < 0:
                # Log warning for negative delay
                self.log_message(f"Warning: Negative delay ({delay_ms}ms) ignored, executing immediately")
        except ValueError:
            # If delay is not a valid number, use 0
            pass
        
        # Execute immediately if no delay or negative delay
        # Show info for long-running operations
        if action in ["stack_inventory", "cancel_all_crafting", "toggle_stack_inventory"]:
            self.log_message(f"⏳ Starting {action.replace('_', ' ').title()} - this may take up to 2 minutes...")
        
        # Run API call in background thread to prevent GUI freezing
        threading.Thread(target=self._execute_api_call, args=(action, params), daemon=True).start()
    
    def _execute_api_call(self, action, params):
        """Execute the actual API call"""
        try:
            import json
            
            # Map action names to API endpoints
            endpoint_map = {
                "craft": "/craft/name",  # Changed from /craft to /craft/name
                "cancel_craft": "/craft/cancel/name",  # Changed from /craft/cancel to /craft/cancel/name
                "cancel_all_crafting": "/craft/cancel-all",
                "suicide": "/player/suicide",
                "kill": "/player/kill",
                "respawn": "/player/respawn",
                "respawn_only": "/player/respawn-only",
                "respawn_random": "/player/respawn-random",
                "respawn_bed": "/player/respawn-bed",
                "gesture": "/player/gesture",
                "auto_run": "/player/auto-run",
                "auto_run_jump": "/player/auto-run-jump",
                "auto_crouch_attack": "/player/auto-crouch-attack",
                "global_chat": "/chat/global",
                "team_chat": "/chat/team",
                "quit_game": "/game/quit",
                "disconnect": "/game/disconnect",
                "connect": "/game/connect",
                            "stack_inventory": "/inventory/stack",
            "inventory_give": "/inventory/give",
            "set_look_radius": "/settings/look-radius",
            "set_voice_volume": "/settings/voice-volume",
            "set_master_volume": "/settings/master-volume",
            "set_hud_state": "/settings/hud",  # Changed from /settings/hud-state to /settings/hud
            "copy_json": "/clipboard/copy-json",
            "type_string": "/input/type-enter",  # Changed from /input/type to /input/type-enter
            "start_anti_afk": "/anti-afk/start",
            "stop_anti_afk": "/anti-afk/stop",
            "toggle_stack_inventory": "/inventory/toggle-stack",
                "noclip_toggle": "/player/noclip",
                "god_mode_toggle": "/player/god-mode",
                "set_time": "/player/set-time",
                "teleport_to_marker": "/player/teleport-marker",
                "toggle_combat_log": "/player/combat-log",
                "clear_console": "/player/clear-console",
                "toggle_console": "/player/toggle-console",
                "ent_kill": "/player/ent-kill"
            }
            
            endpoint = endpoint_map.get(action)
            if not endpoint:
                messagebox.showerror("Error", f"Unknown action: {action}")
                return
            
            url = f"http://localhost:5000{endpoint}"
            
            # Determine timeout based on action type
            # Long-running operations need more time
            if action in ["stack_inventory", "cancel_all_crafting", "toggle_stack_inventory", "inventory_give"]:
                timeout = 120  # 2 minutes for long operations
            else:
                timeout = 5    # 5 seconds for regular operations
            
            # Prepare the request
            if params:
                # Filter out empty values
                filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
                if filtered_params:
                    response = requests.post(url, json=filtered_params, timeout=timeout)
                else:
                    response = requests.post(url, timeout=timeout)
            else:
                response = requests.post(url, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                # Debug logging to see what the API returns
                self.log_message(f"DEBUG: API Response for {action}: {result}")
                if result.get('success'):
                    # Log success to server logs instead of showing popup
                    self.log_message(f"API Success: {action.replace('_', ' ').title()} - {result.get('message', 'Action completed successfully')}")
                else:
                    # Use after_idle for GUI updates from background thread
                    self.root.after_idle(lambda: messagebox.showerror("API Error", f"{action.replace('_', ' ').title()}: {result.get('message', 'Unknown error')}"))
            else:
                # Use after_idle for GUI updates from background thread
                self.root.after_idle(lambda: messagebox.showerror("HTTP Error", f"Server returned status code {response.status_code}"))
                
        except requests.exceptions.ConnectionError:
            # Use after_idle for GUI updates from background thread
            self.root.after_idle(lambda: messagebox.showerror("Connection Error", "Could not connect to the server. Make sure it's running."))
        except requests.exceptions.Timeout:
            # Use after_idle for GUI updates from background thread
            self.root.after_idle(lambda: messagebox.showerror("Timeout Error", "Request timed out. The server may be busy."))
        except Exception as e:
            # Use after_idle for GUI updates from background thread
            self.root.after_idle(lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
    
    def generate_curl_command(self, action, params):
        """Generate a Windows PowerShell compatible command for the given API call"""
        # Map action names to API endpoints
        endpoint_map = {
            "craft": "/craft/name",
            "cancel_craft": "/craft/cancel/name",
            "cancel_all_crafting": "/craft/cancel-all",
            "suicide": "/player/suicide",
            "kill": "/player/kill",
            "respawn": "/player/respawn",
            "respawn_only": "/player/respawn-only",
            "respawn_random": "/player/respawn-random",
            "respawn_bed": "/player/respawn-bed",
            "gesture": "/player/gesture",
            "auto_run": "/player/auto-run",
            "auto_run_jump": "/player/auto-run-jump",
            "auto_crouch_attack": "/player/auto-crouch-attack",
            "global_chat": "/chat/global",
            "team_chat": "/chat/team",
            "quit_game": "/game/quit",
            "disconnect": "/game/disconnect",
            "connect": "/game/connect",
            "stack_inventory": "/inventory/stack",
            "inventory_give": "/inventory/give",
            "set_look_radius": "/settings/look-radius",
            "set_voice_volume": "/settings/voice-volume",
            "set_master_volume": "/settings/master-volume",
            "set_hud_state": "/settings/hud",
            "copy_json": "/clipboard/copy-json",
            "type_string": "/input/type-enter",
            "toggle_stack_inventory": "/inventory/toggle-stack",
            "noclip_toggle": "/player/noclip",
            "god_mode_toggle": "/player/god-mode",
            "set_time": "/player/set-time",
            "teleport_to_marker": "/player/teleport-marker",
            "toggle_combat_log": "/player/combat-log",
            "clear_console": "/player/clear-console",
            "toggle_console": "/player/toggle-console",
            "ent_kill": "/player/ent-kill"
        }
        
        endpoint = endpoint_map.get(action)
        if not endpoint:
            return None
        
        url = f"http://localhost:5000{endpoint}"
        
        # Build the PowerShell command
        ps_cmd = f'Invoke-WebRequest -Uri "{url}" -Method POST'
        
        # Add headers
        ps_cmd += ' -Headers @{"Content-Type"="application/json"}'
        
        # Add JSON data if there are parameters
        if params:
            # Filter out empty values
            filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
            if filtered_params:
                import json
                json_data = json.dumps(filtered_params)
                # For PowerShell, we need to escape single quotes and use single quotes around the JSON
                json_data = json_data.replace("'", "''")
                ps_cmd += f" -Body '{json_data}'"
        
        return ps_cmd
    
    def copy_curl_to_clipboard(self, action, params):
        """Generate PowerShell command and copy to clipboard"""
        ps_cmd = self.generate_curl_command(action, params)
        if ps_cmd:
            try:
                pyperclip.copy(ps_cmd)
                self.log_message(f"✅ PowerShell command copied to clipboard: {action.replace('_', ' ').title()}")
            except Exception as e:
                messagebox.showerror("Clipboard Error", f"Failed to copy to clipboard: {str(e)}")
        else:
            messagebox.showerror("Error", f"Could not generate PowerShell command for action: {action}")

    def give_inventory_items(self):
        """Give multiple items to inventory using the inventory give API"""
        json_text = self.inventory_give_json_text.get("1.0", tk.END).strip()
        
        if not json_text:
            messagebox.showerror("Error", "Please enter JSON data")
            return
        
        try:
            import json
            items = json.loads(json_text)
            
            if not isinstance(items, list):
                messagebox.showerror("Error", "JSON must be an array of objects")
                return
            
            if not items:
                messagebox.showerror("Error", "JSON array cannot be empty")
                return
            
            # Validate each item
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    messagebox.showerror("Error", f"Item {i} must be an object")
                    return
                
                if 'item_name' not in item:
                    messagebox.showerror("Error", f"Item {i} missing required field 'item_name'")
                    return
                
                if 'quantity' in item and not isinstance(item['quantity'], (int, float)):
                    messagebox.showerror("Error", f"Item {i} quantity must be a number")
                    return
                
                if 'quantity' in item and item['quantity'] <= 0:
                    messagebox.showerror("Error", f"Item {i} quantity must be greater than 0")
                    return
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON format: {str(e)}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing JSON: {str(e)}")
            return
        
        # Call the API
        self.test_api_call("inventory_give", {"items": items})
    
    def copy_inventory_give_curl(self):
        """Copy the inventory give PowerShell command to clipboard"""
        json_text = self.inventory_give_json_text.get("1.0", tk.END).strip()
        
        if not json_text:
            messagebox.showerror("Error", "Please enter JSON data")
            return
        
        try:
            import json
            items = json.loads(json_text)
            
            if not isinstance(items, list):
                messagebox.showerror("Error", "JSON must be an array of objects")
                return
            
            if not items:
                messagebox.showerror("Error", "JSON array cannot be empty")
                return
            
            # Validate each item
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    messagebox.showerror("Error", f"Item {i} must be an object")
                    return
                
                if 'item_name' not in item:
                    messagebox.showerror("Error", f"Item {i} missing required field 'item_name'")
                    return
                
                if 'quantity' in item and not isinstance(item['quantity'], (int, float)):
                    messagebox.showerror("Error", f"Item {i} quantity must be a number")
                    return
                
                if 'quantity' in item and item['quantity'] <= 0:
                    messagebox.showerror("Error", f"Item {i} quantity must be greater than 0")
                    return
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON format: {str(e)}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing JSON: {str(e)}")
            return
        
        # Generate and copy the PowerShell command
        self.copy_curl_to_clipboard("inventory_give", {"items": items})
    
    def clear_inventory_json(self):
        """Clear the JSON input text box"""
        self.inventory_give_json_text.delete("1.0", tk.END)
        self.inventory_give_json_text.insert(tk.END, '[{"item_name": "wood", "quantity": 1000}]')

    

    

    
    def refresh_item_dropdowns(self):
        """Refresh the item dropdowns with data from the database"""
        try:
            # Get craftable items from the Steam database (only items with ingredients)
            response = requests.get("http://localhost:5000/steam/craftable-items", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('items'):
                    # Extract item names and sort them
                    item_names = []
                    items_dict = data['items']
                    
                    # Handle dictionary format from steam_manager.get_all_items()
                    for item_id, item_data in items_dict.items():
                        if isinstance(item_data, dict):
                            name = item_data.get('name', '')
                            if name and name not in item_names:
                                item_names.append(name)
                    
                    item_names.sort()  # Sort alphabetically
                    
                    # Update both dropdowns
                    self.craft_name_combo['values'] = item_names
                    self.cancel_name_combo['values'] = item_names
                    
                    # Set default values if empty
                    if not self.craft_name_var.get() and item_names:
                        self.craft_name_var.set(item_names[0])
                    if not self.cancel_name_var.get() and item_names:
                        self.cancel_name_var.set(item_names[0])
                    
                    # Log success to server logs instead of showing popup
                    self.log_message(f"Dropdown Refresh: Loaded {len(item_names)} craftable items into dropdowns")
                else:
                    messagebox.showwarning("Warning", "No craftable items found in database")
            else:
                messagebox.showerror("Error", f"Failed to load craftable items: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Could not connect to the server. Make sure it's running.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh dropdowns: {str(e)}")
            # Log the full error for debugging
            import traceback
            print(f"Full error: {traceback.format_exc()}")
    
    def start_anti_afk(self):
        """Start the anti-AFK feature"""
        try:
            response = requests.post("http://localhost:5000/anti-afk/start", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.anti_afk_status_var.set("Status: Running")
                    self.log_message("✅ Anti-AFK started successfully")
                else:
                    self.log_message(f"❌ Failed to start Anti-AFK: {result.get('message', 'Unknown error')}")
            else:
                self.log_message(f"❌ HTTP Error {response.status_code} when starting Anti-AFK")
        except Exception as e:
            self.log_message(f"❌ Error starting Anti-AFK: {str(e)}")
    
    def stop_anti_afk(self):
        """Stop the anti-AFK feature"""
        try:
            response = requests.post("http://localhost:5000/anti-afk/stop", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.anti_afk_status_var.set("Status: Stopped")
                    self.log_message("✅ Anti-AFK stopped successfully")
                else:
                    self.log_message(f"❌ Failed to stop Anti-AFK: {result.get('message', 'Unknown error')}")
            else:
                self.log_message(f"❌ HTTP Error {response.status_code} when stopping Anti-AFK")
        except Exception as e:
            self.log_message(f"❌ Error stopping Anti-AFK: {str(e)}")
    
    def check_anti_afk_status(self):
        """Check the current anti-AFK status"""
        try:
            response = requests.get("http://localhost:5000/anti-afk/status", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    is_running = result.get('running', False)
                    if is_running:
                        self.anti_afk_status_var.set("Status: Running")
                        self.log_message("✅ Anti-AFK is currently running")
                    else:
                        self.anti_afk_status_var.set("Status: Stopped")
                        self.log_message("ℹ️ Anti-AFK is not running")
                else:
                    self.log_message(f"❌ Failed to get Anti-AFK status: {result.get('message', 'Unknown error')}")
            else:
                self.log_message(f"❌ HTTP Error {response.status_code} when checking Anti-AFK status")
        except Exception as e:
            self.log_message(f"❌ Error checking Anti-AFK status: {str(e)}")
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        # Create system tray icon - standard approach
        try:
            # Check if we're running as an executable
            if getattr(sys, 'frozen', False):
                # Running as executable - try to load bundled icon files
                # For single-file executables, files are in sys._MEIPASS
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                
                # Try to load icon from bundled files
                icon_found = False
                for icon_name in ["camera.ico", "camera.png", "rust_controller.ico", "rust_controller.png"]:
                    icon_path = os.path.join(base_path, icon_name)
                    if os.path.exists(icon_path):
                        try:
                            self.icon_image = Image.open(icon_path)
                            # Convert to RGB for system tray compatibility
                            if self.icon_image.mode != 'RGB':
                                self.icon_image = self.icon_image.convert('RGB')
                            # Resize to appropriate size for system tray
                            self.icon_image = self.icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                            self.log_message(f"✅ Using bundled {icon_name} for system tray icon")
                            icon_found = True
                            break
                        except Exception as e:
                            self.log_message(f"⚠️ Error loading bundled {icon_name}: {e}")
                            continue
                
                if not icon_found:
                    # For single-file executables, we can't access bundled files directly
                    # Create a simple camera-like icon programmatically
                    try:
                        # Create a simple camera icon (black camera shape on white background)
                        self.icon_image = Image.new('RGB', (64, 64), color='white')
                        from PIL import ImageDraw
                        draw = ImageDraw.Draw(self.icon_image)
                        
                        # Draw a simple camera shape
                        # Camera body (rectangle)
                        draw.rectangle([12, 20, 52, 44], fill='black', outline='black')
                        # Camera lens (circle)
                        draw.ellipse([24, 26, 40, 38], fill='white', outline='black')
                        # Camera flash (small rectangle)
                        draw.rectangle([20, 16, 28, 20], fill='black', outline='black')
                        
                        self.log_message("✅ Created programmatic camera icon for system tray")
                        icon_found = True
                    except Exception as e:
                        self.log_message(f"⚠️ Error creating programmatic icon: {e}")
                        # Create a simple colored square as fallback
                        self.icon_image = Image.new('RGB', (64, 64), color='blue')
                        self.log_message("⚠️ Using fallback blue square")
            else:
                # Running as script - try to load icon files from current directory
                if os.path.exists("camera.ico"):
                    self.icon_image = Image.open("camera.ico")
                    # Convert to RGB for system tray compatibility
                    if self.icon_image.mode != 'RGB':
                        self.icon_image = self.icon_image.convert('RGB')
                    # Resize to appropriate size for system tray
                    self.icon_image = self.icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                    self.log_message("✅ Using camera.ico for system tray icon")
                elif os.path.exists("rust_controller.ico"):
                    self.icon_image = Image.open("rust_controller.ico")
                    # Convert to RGB for system tray compatibility
                    if self.icon_image.mode != 'RGB':
                        self.icon_image = self.icon_image.convert('RGB')
                    # Resize to appropriate size for system tray
                    self.icon_image = self.icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                    self.log_message("✅ Using rust_controller.ico for system tray icon")
                else:
                    # Create a simple colored square as fallback
                    self.icon_image = Image.new('RGB', (64, 64), color='blue')
                    self.log_message("⚠️ No .ico file found, using fallback blue square")
        except Exception as e:
            # Create a simple colored square as fallback
            self.icon_image = Image.new('RGB', (64, 64), color='blue')
            self.log_message(f"⚠️ Error loading icon: {e}, using fallback blue square")
        
        # Create system tray menu
        menu = pystray.Menu(
            item('Show Window', self.show_window),
            item('Start Server', self.start_server),
            item('Stop Server', self.stop_server),
            pystray.Menu.SEPARATOR,
            item('Open API', self.open_api),
            pystray.Menu.SEPARATOR,
            item('Exit', self.quit_app)
        )
        
        # Create system tray icon
        self.tray_icon = pystray.Icon("camera_controller", self.icon_image, 
                                     "Rust Game Controller API", menu)
        
        # Start system tray in a separate thread
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
    
    def start_server(self):
        """Start the Flask server"""
        if self.server_running:
            return
        
        try:
            self.log_message("Starting API server...")
            
            # Import and start Flask app directly instead of using subprocess
            def run_flask_server():
                try:
                    from app import app
                    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
                except Exception as e:
                    self.log_message(f"❌ Flask server error: {e}")
            
            # Start Flask server in a separate thread
            self.server_thread = threading.Thread(target=run_flask_server, daemon=True)
            self.server_thread.start()
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Check if the server is responding
            try:
                response = requests.get("http://localhost:5000/health", timeout=5)
                if response.status_code == 200:
                    self.server_running = True
                    self.log_message("✅ API server started successfully on http://localhost:5000")
                    # Update GUI status if GUI is ready
                    if hasattr(self, 'root') and self.root:
                        self.root.after_idle(lambda: self._update_server_status("Running"))
                else:
                    self.log_message("❌ Server started but not responding properly")
            except:
                self.log_message("❌ Server failed to start or respond")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start server: {e}")
            if hasattr(self, 'root') and self.root:
                self.root.after_idle(lambda: messagebox.showerror("Error", f"Failed to start server: {e}"))
    
    def wait_for_server_ready(self):
        """Wait for the server to be fully ready and responding"""
        self.log_message("Waiting for server to be ready...")
        max_attempts = 30  # Wait up to 30 seconds
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = requests.get("http://localhost:5000/health", timeout=2)
                if response.status_code == 200:
                    self.server_running = True
                    self.log_message("✅ Server is ready and responding")
                    return True
            except:
                pass
            
            attempt += 1
            time.sleep(1)
            if attempt % 5 == 0:  # Log every 5 seconds
                self.log_message(f"Still waiting for server... ({attempt}s)")
        
        self.log_message("❌ Server failed to become ready within timeout")
        return False
    
    def _test_server_health(self):
        """Test if the server is responding"""
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                self.log_message("✅ Server health check passed")
            else:
                self.log_message(f"⚠️ Server health check failed: {response.status_code}")
        except Exception as e:
            self.log_message(f"⚠️ Server health check failed: {e}")
    
    def _update_server_status(self, status):
        """Update server status in GUI (called from main thread)"""
        # Update menu states based on server status
        if hasattr(self, 'server_menu'):
            if status == "Running":
                self.server_menu.entryconfig(0, state="disabled")  # Start Server
                self.server_menu.entryconfig(1, state="normal")    # Stop Server
            else:
                self.server_menu.entryconfig(0, state="normal")    # Start Server
                self.server_menu.entryconfig(1, state="disabled")  # Stop Server
    
    def stop_server(self):
        """Stop the Flask server"""
        if not self.server_running:
            return
        
        try:
            # For thread-based server, we can't easily stop it
            # The thread will terminate when the main process ends
            self.server_running = False
            
            # Update GUI if it's ready
            if hasattr(self, 'root') and self.root:
                self.root.after_idle(lambda: self._update_server_status("Stopped"))
            
            self.log_message("Server stopped")
            
        except Exception as e:
            self.log_message(f"Failed to stop server: {e}")
            if hasattr(self, 'root') and self.root:
                self.root.after_idle(lambda: messagebox.showerror("Error", f"Failed to stop server: {e}"))
    
    def open_api(self):
        """Open the API in default browser"""
        try:
            webbrowser.open("http://localhost:5000/health")
        except Exception as e:
            self.log_message(f"Failed to open API: {e}")
    
    def log_message(self, message):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)
    
    def monitor_logs(self):
        """Monitor log queue and update GUI"""
        try:
            # Process all available messages at once
            messages = []
            while True:
                try:
                    message = self.log_queue.get_nowait()
                    messages.append(message)
                except queue.Empty:
                    break
            
            # Update GUI with all messages at once
            if messages:
                combined_message = '\n'.join(messages) + '\n'
                self.log_text.insert(tk.END, combined_message)
                
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
                
                # Limit log size (only check occasionally)
                lines = self.log_text.get("1.0", tk.END).split("\n")
                if len(lines) > 1000:
                    self.log_text.delete("1.0", "500.0")
                        
        except Exception as e:
            print(f"Error monitoring logs: {e}")
        
        # Schedule next check (further reduced frequency)
        self.root.after(1000, self.monitor_logs)
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete("1.0", tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get("1.0", tk.END))
                
                self.log_message(f"Logs saved to {filename}")
                
        except Exception as e:
            self.log_message(f"Failed to save logs: {e}")
            messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def _update_db_stats_display(self, text):
        """Update database stats display (called from main thread)"""
        if hasattr(self, 'db_stats_var'):
            self.db_stats_var.set(text)
    
    def check_startup_enabled(self):
        """Check if the app is enabled to start with Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "RustGameController")
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def update_startup_command(self):
        """Update the startup command in registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            
            app_path = sys.argv[0]
            if app_path.endswith('.py'):
                # If running as script, use python executable
                app_path = f'"{sys.executable}" "{app_path}"'
            else:
                # If running as exe
                app_path = f'"{app_path}"'
            
            # Add start minimized parameter if enabled
            if self.check_start_minimized_enabled():
                app_path += ' --minimized'
            
            winreg.SetValueEx(key, "RustGameController", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
        except Exception as e:
            self.log_message(f"Failed to update startup command: {e}")
    
    def check_start_minimized_enabled(self):
        """Check if the app is set to start minimized"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\RustGameController", 
                               0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "StartMinimized")
            winreg.CloseKey(key)
            return bool(value)
        except FileNotFoundError:
            # Key doesn't exist, return False
            return False
        except:
            return False

    def create_api_testing_panel(self, parent):
        """Create the API testing panel on the right side"""
        # Main API testing frame
        self.api_frame = ttk.LabelFrame(parent, text="API Testing", padding="5")
        # Create the frame but don't show it initially (hidden by default)
        self.api_frame.columnconfigure(0, weight=1)
        
        # Create a canvas with scrollbar for the testing panel
        canvas = tk.Canvas(self.api_frame, width=400)
        scrollbar = ttk.Scrollbar(self.api_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Command Delay Section
        delay_frame = ttk.Frame(scrollable_frame)
        delay_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(delay_frame, text="Command Delay (ms):").pack(side=tk.LEFT, padx=(0, 5))
        self.command_delay_var = tk.StringVar(value="0")
        delay_entry = ttk.Entry(delay_frame, textvariable=self.command_delay_var, width=8)
        delay_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add tooltip or help text
        ttk.Label(delay_frame, text="Delay before each command (0 = no delay)", 
                 font=("TkDefaultFont", 8), foreground="gray").pack(side=tk.LEFT)
        
        # Crafting Section
        crafting_frame = ttk.LabelFrame(scrollable_frame, text="Crafting", padding="5")
        crafting_frame.pack(fill="x", pady=(0, 10))
        
        # Craft by ID
        ttk.Label(crafting_frame, text="Craft by ID:").pack(anchor=tk.W)
        craft_id_frame = ttk.Frame(crafting_frame)
        craft_id_frame.pack(fill="x", pady=(0, 5))
        
        self.craft_id_var = tk.StringVar()
        ttk.Entry(craft_id_frame, textvariable=self.craft_id_var, width=15).pack(side=tk.LEFT, padx=(0, 5))
        
        self.craft_quantity_var = tk.StringVar(value="1")
        ttk.Entry(craft_id_frame, textvariable=self.craft_quantity_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(craft_id_frame, text="Craft", 
                  command=lambda: self.test_api_call("craft", {"item_id": self.craft_id_var.get(), "quantity": self.craft_quantity_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(craft_id_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("craft", {"item_id": self.craft_id_var.get(), "quantity": self.craft_quantity_var.get()})).pack(side=tk.LEFT)
        
        # Craft by Name
        ttk.Label(crafting_frame, text="Craft by Name:").pack(anchor=tk.W, pady=(10, 0))
        craft_name_frame = ttk.Frame(crafting_frame)
        craft_name_frame.pack(fill="x", pady=(0, 5))
        
        self.craft_name_var = tk.StringVar()
        self.craft_name_combo = ttk.Combobox(craft_name_frame, textvariable=self.craft_name_var, width=20, state="readonly")
        self.craft_name_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        self.craft_name_quantity_var = tk.StringVar(value="1")
        ttk.Entry(craft_name_frame, textvariable=self.craft_name_quantity_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(craft_name_frame, text="Craft", 
                  command=lambda: self.test_api_call("craft", {"item_name": self.craft_name_var.get(), "quantity": self.craft_name_quantity_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(craft_name_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("craft", {"item_name": self.craft_name_var.get(), "quantity": self.craft_name_quantity_var.get()})).pack(side=tk.LEFT)
        
        # Refresh items button
        ttk.Button(craft_name_frame, text="Refresh", 
                  command=self.refresh_item_dropdowns).pack(side=tk.LEFT, padx=(5, 0))
        
        # Cancel Craft by ID
        ttk.Label(crafting_frame, text="Cancel Craft by ID:").pack(anchor=tk.W, pady=(10, 0))
        cancel_id_frame = ttk.Frame(crafting_frame)
        cancel_id_frame.pack(fill="x", pady=(0, 5))
        
        self.cancel_id_var = tk.StringVar()
        ttk.Entry(cancel_id_frame, textvariable=self.cancel_id_var, width=15).pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_quantity_var = tk.StringVar(value="1")
        ttk.Entry(cancel_id_frame, textvariable=self.cancel_quantity_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_id_frame, text="Cancel", 
                  command=lambda: self.test_api_call("cancel_craft", {"item_id": self.cancel_id_var.get(), "quantity": self.cancel_quantity_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_id_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("cancel_craft", {"item_id": self.cancel_id_var.get(), "quantity": self.cancel_quantity_var.get()})).pack(side=tk.LEFT)
        
        # Cancel Craft by Name
        ttk.Label(crafting_frame, text="Cancel Craft by Name:").pack(anchor=tk.W, pady=(10, 0))
        cancel_name_frame = ttk.Frame(crafting_frame)
        cancel_name_frame.pack(fill="x", pady=(0, 5))
        
        self.cancel_name_var = tk.StringVar()
        self.cancel_name_combo = ttk.Combobox(cancel_name_frame, textvariable=self.cancel_name_var, width=20, state="readonly")
        self.cancel_name_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_name_quantity_var = tk.StringVar(value="1")
        ttk.Entry(cancel_name_frame, textvariable=self.cancel_name_quantity_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_name_frame, text="Cancel", 
                  command=lambda: self.test_api_call("cancel_craft", {"item_name": self.cancel_name_var.get(), "quantity": self.cancel_name_quantity_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_name_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("cancel_craft", {"item_name": self.cancel_name_var.get(), "quantity": self.cancel_name_quantity_var.get()})).pack(side=tk.LEFT)
        
        # Cancel All Crafting
        cancel_all_frame = ttk.Frame(crafting_frame)
        cancel_all_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(cancel_all_frame, text="Iterations:").pack(side=tk.LEFT, padx=(0, 5))
        self.cancel_iterations_var = tk.StringVar(value="80")
        ttk.Entry(cancel_all_frame, textvariable=self.cancel_iterations_var, width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_all_frame, text="Cancel All Crafting", 
                  command=lambda: self.test_api_call("cancel_all_crafting", {"iterations": int(self.cancel_iterations_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(cancel_all_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("cancel_all_crafting", {"iterations": int(self.cancel_iterations_var.get())})).pack(side=tk.LEFT)
        
        # Stack Inventory
        stack_inventory_frame = ttk.Frame(crafting_frame)
        stack_inventory_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(stack_inventory_frame, text="Iterations:").pack(side=tk.LEFT, padx=(0, 5))
        self.stack_iterations_var = tk.StringVar(value="80")
        ttk.Entry(stack_inventory_frame, textvariable=self.stack_iterations_var, width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(stack_inventory_frame, text="Stack Inventory", 
                  command=lambda: self.test_api_call("stack_inventory", {"iterations": int(self.stack_iterations_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(stack_inventory_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("stack_inventory", {"iterations": int(self.stack_iterations_var.get())})).pack(side=tk.LEFT)
        
        # Toggle Stack Inventory
        toggle_stack_frame = ttk.Frame(crafting_frame)
        toggle_stack_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(toggle_stack_frame, text="Enable Continuous Stack", 
                  command=lambda: self.test_api_call("toggle_stack_inventory", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toggle_stack_frame, text="Disable Continuous Stack", 
                  command=lambda: self.test_api_call("toggle_stack_inventory", {"enable": False})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toggle_stack_frame, text="Copy Enable PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("toggle_stack_inventory", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toggle_stack_frame, text="Copy Disable PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("toggle_stack_inventory", {"enable": False})).pack(side=tk.LEFT)
        
        # Inventory Give Section
        inventory_give_frame = ttk.Frame(crafting_frame)
        inventory_give_frame.pack(fill="x", pady=(10, 0))
        
        # JSON Input Label
        ttk.Label(inventory_give_frame, text="Items JSON (array of objects with 'item_name' and 'quantity'):").pack(anchor=tk.W, pady=(0, 5))
        
        # JSON Input Text Box
        json_frame = ttk.Frame(inventory_give_frame)
        json_frame.pack(fill="x", pady=(0, 5))
        
        self.inventory_give_json_var = tk.StringVar(value='[{"item_name": "wood", "quantity": 1000}]')
        self.inventory_give_json_text = scrolledtext.ScrolledText(json_frame, height=4, width=50)
        self.inventory_give_json_text.pack(fill="x", expand=True)
        self.inventory_give_json_text.insert(tk.END, self.inventory_give_json_var.get())
        
        # Buttons
        buttons_frame = ttk.Frame(inventory_give_frame)
        buttons_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(buttons_frame, text="Give Items", 
                  command=self.give_inventory_items).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(buttons_frame, text="Copy PowerShell", 
                  command=self.copy_inventory_give_curl).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(buttons_frame, text="Clear JSON", 
                  command=self.clear_inventory_json).pack(side=tk.LEFT, padx=(0, 5))
        
        # Player Actions Section
        player_frame = ttk.LabelFrame(scrollable_frame, text="Player Actions", padding="5")
        player_frame.pack(fill="x", pady=(0, 10))
        
        # Suicide and Respawn
        suicide_respawn_frame = ttk.Frame(player_frame)
        suicide_respawn_frame.pack(fill="x", pady=(0, 5))
        
        # Row 1: Suicide (just kill)
        row1_frame = ttk.Frame(suicide_respawn_frame)
        row1_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(row1_frame, text="Suicide (just kill)", 
                  command=lambda: self.test_api_call("kill", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row1_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("kill", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 2: Random spawn (just respawn)
        row2_frame = ttk.Frame(suicide_respawn_frame)
        row2_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(row2_frame, text="Random spawn (just respawn)", 
                  command=lambda: self.test_api_call("respawn_only", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("respawn_only", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 3: Respawn random (kill and respawn)
        row3_frame = ttk.Frame(suicide_respawn_frame)
        row3_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(row3_frame, text="Respawn random (kill and respawn)", 
                  command=lambda: self.test_api_call("respawn_random", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("respawn_random", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 4: Respawn bed (kill and respawn_sleepingbag <id>)
        row4_frame = ttk.Frame(suicide_respawn_frame)
        row4_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(row4_frame, text="Bed ID:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.respawn_bed_id_var = tk.StringVar()
        ttk.Entry(row4_frame, textvariable=self.respawn_bed_id_var, width=10).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row4_frame, text="Respawn bed (kill and respawn_sleepingbag <id>)", 
                  command=lambda: self.test_api_call("respawn_bed", {"spawn_id": self.respawn_bed_id_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row4_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("respawn_bed", {"spawn_id": self.respawn_bed_id_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        # Movement Actions
        movement_frame = ttk.Frame(player_frame)
        movement_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(movement_frame, text="Auto Run", 
                  command=lambda: self.test_api_call("auto_run", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(movement_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("auto_run", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(movement_frame, text="Auto Run & Jump", 
                  command=lambda: self.test_api_call("auto_run_jump", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(movement_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("auto_run_jump", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(movement_frame, text="Auto Crouch & Attack", 
                  command=lambda: self.test_api_call("auto_crouch_attack", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(movement_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("auto_crouch_attack", {})).pack(side=tk.LEFT)
        
        # Emotes Section
        emote_frame = ttk.Frame(player_frame)
        emote_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(emote_frame, text="Emotes:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Define available emotes
        self.emotes = [
            "wave", "victory", "shrug", "thumbsup", "hurry", "ok", "thumbsdown", 
            "clap", "point", "friendly", "cabbagepatch", "twist", "raisetheroof", 
            "beatchest", "throatcut", "fingergun", "shush", "shush_vocal", 
            "watchingyou", "loser", "nono", "knucklescrack", "rps"
        ]
        
        self.emote_var = tk.StringVar()
        self.emote_combo = ttk.Combobox(emote_frame, textvariable=self.emote_var, values=self.emotes, width=15, state="readonly")
        self.emote_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # Set default value
        if self.emotes:
            self.emote_var.set(self.emotes[0])
        
        ttk.Button(emote_frame, text="Perform", 
                  command=lambda: self.test_api_call("gesture", {"gesture_name": self.emote_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(emote_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("gesture", {"gesture_name": self.emote_var.get()})).pack(side=tk.LEFT)
        
        # Admin Commands Section
        admin_frame = ttk.Frame(player_frame)
        admin_frame.pack(fill="x", pady=(5, 0))
        
        # Noclip
        noclip_frame = ttk.Frame(admin_frame)
        noclip_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(noclip_frame, text="Noclip ON", 
                  command=lambda: self.test_api_call("noclip_toggle", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(noclip_frame, text="Noclip OFF", 
                  command=lambda: self.test_api_call("noclip_toggle", {"enable": False})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(noclip_frame, text="Copy ON PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("noclip_toggle", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(noclip_frame, text="Copy OFF PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("noclip_toggle", {"enable": False})).pack(side=tk.LEFT)
        
        # God Mode
        god_frame = ttk.Frame(admin_frame)
        god_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(god_frame, text="God Mode ON", 
                  command=lambda: self.test_api_call("god_mode_toggle", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(god_frame, text="God Mode OFF", 
                  command=lambda: self.test_api_call("god_mode_toggle", {"enable": False})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(god_frame, text="Copy ON PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("god_mode_toggle", {"enable": True})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(god_frame, text="Copy OFF PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("god_mode_toggle", {"enable": False})).pack(side=tk.LEFT)
        
        # Time Control
        time_frame = ttk.Frame(admin_frame)
        time_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.time_var = tk.StringVar(value="12")
        time_combo = ttk.Combobox(time_frame, textvariable=self.time_var, 
                                 values=["0", "4", "8", "12", "16", "20", "24"], width=5, state="readonly")
        time_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(time_frame, text="Set Time", 
                  command=lambda: self.test_api_call("set_time", {"time_hour": int(self.time_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(time_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("set_time", {"time_hour": int(self.time_var.get())})).pack(side=tk.LEFT)
        
        # Teleport and Console
        teleport_console_frame = ttk.Frame(admin_frame)
        teleport_console_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Teleport to Marker", 
                  command=lambda: self.test_api_call("teleport_to_marker", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("teleport_to_marker", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Toggle Combat Log", 
                  command=lambda: self.test_api_call("toggle_combat_log", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("toggle_combat_log", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Ent Kill", 
                  command=lambda: self.test_api_call("ent_kill", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(teleport_console_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("ent_kill", {})).pack(side=tk.LEFT)
        
        # Console Controls
        console_frame = ttk.Frame(admin_frame)
        console_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(console_frame, text="Clear Console", 
                  command=lambda: self.test_api_call("clear_console", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(console_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("clear_console", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(console_frame, text="Toggle Console", 
                  command=lambda: self.test_api_call("toggle_console", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(console_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("toggle_console", {})).pack(side=tk.LEFT)
        
        # Chat Section
        chat_frame = ttk.LabelFrame(scrollable_frame, text="Chat", padding="5")
        chat_frame.pack(fill="x", pady=(0, 10))
        
        # Global Chat
        ttk.Label(chat_frame, text="Global Chat:").pack(anchor=tk.W)
        global_chat_frame = ttk.Frame(chat_frame)
        global_chat_frame.pack(fill="x", pady=(0, 5))
        
        self.global_chat_var = tk.StringVar()
        ttk.Entry(global_chat_frame, textvariable=self.global_chat_var, width=25).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(global_chat_frame, text="Send", 
                  command=lambda: self.test_api_call("global_chat", {"message": self.global_chat_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(global_chat_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("global_chat", {"message": self.global_chat_var.get()})).pack(side=tk.LEFT)
        
        # Team Chat
        ttk.Label(chat_frame, text="Team Chat:").pack(anchor=tk.W, pady=(10, 0))
        team_chat_frame = ttk.Frame(chat_frame)
        team_chat_frame.pack(fill="x", pady=(0, 5))
        
        self.team_chat_var = tk.StringVar()
        ttk.Entry(team_chat_frame, textvariable=self.team_chat_var, width=25).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(team_chat_frame, text="Send", 
                  command=lambda: self.test_api_call("team_chat", {"message": self.team_chat_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(team_chat_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("team_chat", {"message": self.team_chat_var.get()})).pack(side=tk.LEFT)
        
        # Game Management Section
        game_frame = ttk.LabelFrame(scrollable_frame, text="Game Management", padding="5")
        game_frame.pack(fill="x", pady=(0, 10))
        
        # Quit and Disconnect
        quit_disconnect_frame = ttk.Frame(game_frame)
        quit_disconnect_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(quit_disconnect_frame, text="Quit Game", 
                  command=lambda: self.test_api_call("quit_game", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(quit_disconnect_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("quit_game", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(quit_disconnect_frame, text="Disconnect", 
                  command=lambda: self.test_api_call("disconnect", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(quit_disconnect_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("disconnect", {})).pack(side=tk.LEFT)
        
        # Connect to Server
        ttk.Label(game_frame, text="Connect to Server:").pack(anchor=tk.W, pady=(10, 0))
        connect_frame = ttk.Frame(game_frame)
        connect_frame.pack(fill="x", pady=(0, 5))
        
        self.server_ip_var = tk.StringVar()
        ttk.Entry(connect_frame, textvariable=self.server_ip_var, width=20).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(connect_frame, text="Connect", 
                  command=lambda: self.test_api_call("connect", {"server_ip": self.server_ip_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(connect_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("connect", {"server_ip": self.server_ip_var.get()})).pack(side=tk.LEFT)
        
        # Settings Section
        settings_frame = ttk.LabelFrame(scrollable_frame, text="Settings", padding="5")
        settings_frame.pack(fill="x", pady=(0, 10))
        
        # Look at radius
        ttk.Label(settings_frame, text="Look at Radius:").pack(anchor=tk.W)
        radius_frame = ttk.Frame(settings_frame)
        radius_frame.pack(fill="x", pady=(0, 5))
        
        self.radius_var = tk.StringVar(value="20")
        radius_combo = ttk.Combobox(radius_frame, textvariable=self.radius_var, 
                                   values=["20", "0.0002"], width=10, state="readonly")
        radius_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(radius_frame, text="Set", 
                  command=lambda: self.test_api_call("set_look_radius", {"radius": float(self.radius_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(radius_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("set_look_radius", {"radius": float(self.radius_var.get())})).pack(side=tk.LEFT)
        
        # Volume controls
        volume_frame = ttk.Frame(settings_frame)
        volume_frame.pack(fill="x", pady=(10, 0))
        
        # Voice Volume
        ttk.Label(volume_frame, text="Voice Volume:").pack(anchor=tk.W)
        voice_volume_frame = ttk.Frame(volume_frame)
        voice_volume_frame.pack(fill="x", pady=(0, 5))
        
        self.voice_volume_var = tk.StringVar(value="0.5")
        voice_volume_combo = ttk.Combobox(voice_volume_frame, textvariable=self.voice_volume_var, 
                                         values=["0", "0.25", "0.5", "0.75", "1"], width=10, state="readonly")
        voice_volume_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(voice_volume_frame, text="Set", 
                  command=lambda: self.test_api_call("set_voice_volume", {"volume": float(self.voice_volume_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(voice_volume_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("set_voice_volume", {"volume": float(self.voice_volume_var.get())})).pack(side=tk.LEFT, padx=(0, 10))
        
        # Master Volume
        ttk.Label(volume_frame, text="Master Volume:").pack(anchor=tk.W, pady=(10, 0))
        master_volume_frame = ttk.Frame(volume_frame)
        master_volume_frame.pack(fill="x", pady=(0, 5))
        
        self.master_volume_var = tk.StringVar(value="0.5")
        master_volume_combo = ttk.Combobox(master_volume_frame, textvariable=self.master_volume_var, 
                                          values=["0", "0.25", "0.5", "0.75", "1"], width=10, state="readonly")
        master_volume_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(master_volume_frame, text="Set", 
                  command=lambda: self.test_api_call("set_master_volume", {"volume": float(self.master_volume_var.get())})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(master_volume_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("set_master_volume", {"volume": float(self.master_volume_var.get())})).pack(side=tk.LEFT)
        
        # HUD State
        hud_frame = ttk.Frame(settings_frame)
        hud_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(hud_frame, text="HUD State:").pack(anchor=tk.W)
        self.hud_state_var = tk.StringVar(value="enabled")
        hud_combo = ttk.Combobox(hud_frame, textvariable=self.hud_state_var, values=["enabled", "disabled"], width=10, state="readonly")
        hud_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(hud_frame, text="Set", 
                  command=lambda: self.test_api_call("set_hud_state", {"enabled": self.hud_state_var.get() == "enabled"})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(hud_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("set_hud_state", {"enabled": self.hud_state_var.get() == "enabled"})).pack(side=tk.LEFT)
        
        # Anti-AFK Section
        anti_afk_frame = ttk.Frame(settings_frame)
        anti_afk_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(anti_afk_frame, text="Anti-AFK:").pack(anchor=tk.W)
        
        # Anti-AFK status label
        self.anti_afk_status_var = tk.StringVar(value="Status: Unknown")
        anti_afk_status_label = ttk.Label(anti_afk_frame, textvariable=self.anti_afk_status_var)
        anti_afk_status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Anti-AFK buttons
        anti_afk_buttons_frame = ttk.Frame(anti_afk_frame)
        anti_afk_buttons_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(anti_afk_buttons_frame, text="Start Anti-AFK", 
                  command=self.start_anti_afk).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(anti_afk_buttons_frame, text="Stop Anti-AFK", 
                  command=self.stop_anti_afk).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(anti_afk_buttons_frame, text="Check Status", 
                  command=self.check_anti_afk_status).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(anti_afk_buttons_frame, text="Copy PowerShell (Start)", 
                  command=lambda: self.copy_curl_to_clipboard("start_anti_afk", {})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(anti_afk_buttons_frame, text="Copy PowerShell (Stop)", 
                  command=lambda: self.copy_curl_to_clipboard("stop_anti_afk", {})).pack(side=tk.LEFT)
        
        # Input/Clipboard Section
        input_frame = ttk.LabelFrame(scrollable_frame, text="Input & Clipboard", padding="5")
        input_frame.pack(fill="x", pady=(0, 10))
        
        # Copy JSON to clipboard
        ttk.Label(input_frame, text="Copy JSON to Clipboard:").pack(anchor=tk.W)
        json_frame = ttk.Frame(input_frame)
        json_frame.pack(fill="x", pady=(0, 5))
        
        self.json_var = tk.StringVar()
        ttk.Entry(json_frame, textvariable=self.json_var, width=25).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(json_frame, text="Copy", 
                  command=lambda: self.test_api_call("copy_json", {"json_data": self.json_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(json_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("copy_json", {"json_data": self.json_var.get()})).pack(side=tk.LEFT)
        
        # Type string and enter
        ttk.Label(input_frame, text="Type String & Enter:").pack(anchor=tk.W, pady=(10, 0))
        type_frame = ttk.Frame(input_frame)
        type_frame.pack(fill="x", pady=(0, 5))
        
        self.type_string_var = tk.StringVar()
        ttk.Entry(type_frame, textvariable=self.type_string_var, width=25).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(type_frame, text="Type", 
                  command=lambda: self.test_api_call("type_string", {"text": self.type_string_var.get()})).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(type_frame, text="Copy PowerShell", 
                  command=lambda: self.copy_curl_to_clipboard("type_string", {"text": self.type_string_var.get()})).pack(side=tk.LEFT)
    
    def on_minimize(self, event=None):
        """Handle minimize button click"""
        # Check if the window is being minimized (not just moved or resized)
        if self.root.state() == 'iconic':
            self.minimize_to_tray()
    
    def on_configure(self, event=None):
        """Handle window configuration changes"""
        # Check if window is being minimized
        if hasattr(self, 'root') and self.root:
            if self.root.state() == 'iconic':
                # Small delay to ensure the minimize action is complete
                self.root.after(100, self.minimize_to_tray)
    
    def minimize_to_tray(self):
        """Minimize window to system tray"""
        self.root.withdraw()
        self.tray_icon.visible = True
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.tray_icon:
            self.tray_icon.visible = False
    
    def on_window_close(self):
        """Handle window close - ask user if they want to quit or minimize"""
        if messagebox.askyesno("Exit Application", "Do you want to exit the application?\n\nClick 'Yes' to exit completely.\nClick 'No' to minimize to system tray."):
            self.quit_app()
        else:
            self.minimize_to_tray()
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                           "Rust Game Controller API\n\n"
                           "Version: 1.0.0\n"
                           "A tool for controlling Rust game through API commands.\n\n"
                           "Features:\n"
                           "• Inventory management\n"
                           "• Crafting automation\n"
                           "• Game controls\n"
                           "• Steam integration\n\n"
                           "Keyboard Shortcuts:\n"
                           "• Ctrl+Q: Exit application\n"
                           "• Alt+M: Minimize to tray")
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.shutdown_event.set()
        self.stop_server()
        if self.tray_icon:
            self.tray_icon.visible = False
            self.tray_icon.stop()
        self.root.quit()
        # Force exit the process
        os._exit(0)
    
    def check_steam_login_status(self):
        """Check Steam login status"""
        try:
            login_status = steam_manager.check_steam_login()
            
            if login_status["loggedIn"]:
                self.steam_status_var.set(f"Steam: Logged in as {login_status['username']}")
                self.steam_username_var.set(login_status["username"])
            else:
                self.steam_status_var.set(f"Steam: {login_status['message']}")
            
        except Exception as e:
            self.steam_status_var.set(f"Steam: Error checking status - {str(e)}")
    
    def steam_login(self):
        """Handle Steam login"""
        username = self.steam_username_var.get().strip()
        password = self.steam_password_var.get().strip()
        twofa_code = self.steam_2fa_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # Disable login button during login
        self.steam_login_button.config(state="disabled")
        self.steam_status_var.set("Steam: Logging in...")
        
        # Run login in separate thread
        def login_thread():
            try:
                result = steam_manager.steam_login(username, password, twofa_code if twofa_code else None)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_login_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_login_result({
                    "success": False,
                    "loggedIn": False,
                    "message": f"Login error: {str(e)}"
                }))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def handle_login_result(self, result):
        """Handle Steam login result"""
        self.steam_login_button.config(state="normal")
        
        if result["success"] and result["loggedIn"]:
            self.steam_status_var.set(f"Steam: Logged in as {result['username']}")
            self.steam_password_var.set("")  # Clear password
            messagebox.showinfo("Success", f"Steam login successful for {result['username']}")
        else:
            self.steam_status_var.set(f"Steam: Login failed - {result['message']}")
            messagebox.showerror("Login Failed", result["message"])
    
    def update_item_database(self):
        """Update the item database using Steam"""
        # Disable update button during update
        self.update_database_button.config(state="disabled")
        self.progress_var.set(0)
        self.progress_label_var.set("Starting database update...")
        
        def progress_callback(progress, message):
            """Callback for progress updates"""
            self.root.after(0, lambda: self.update_progress(progress, message))
        
        def update_thread():
            try:
                result = steam_manager.update_item_database(progress_callback=progress_callback)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_update_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_update_result({
                    "success": False,
                    "message": f"Update error: {str(e)}"
                }))
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def update_progress(self, progress, message):
        """Update progress bar and label"""
        self.progress_var.set(progress)
        self.progress_label_var.set(message)
    
    def handle_update_result(self, result):
        """Handle database update result"""
        self.update_database_button.config(state="normal")
        
        if result["success"]:
            self.progress_label_var.set(f"Update complete: {result['message']}")
            messagebox.showinfo("Success", f"Database updated successfully!\n{result['message']}")
            # Refresh database stats
            stats_data = self._fetch_database_stats()
            self._update_db_stats_display(stats_data)
            # Automatically refresh the crafting dropdowns with new data
            self.refresh_item_dropdowns()
        else:
            if result.get("requireSteamLogin"):
                self.progress_label_var.set("Steam login required")
                messagebox.showwarning("Steam Login Required", 
                                     "Please log in to Steam first before updating the database.")
            else:
                self.progress_label_var.set(f"Update failed: {result['message']}")
                messagebox.showerror("Update Failed", result["message"])
    
    def process_assets_only(self):
        """Process Rust assets only (without downloading files)"""
        # Disable process button during operation
        self.process_assets_button.config(state="disabled")
        self.progress_var.set(0)
        self.progress_label_var.set("Processing Rust assets...")
        
        def progress_callback(progress, message):
            """Callback for progress updates"""
            self.root.after(0, lambda: self.update_progress(progress, message))
        
        def process_thread():
            try:
                # Process Rust assets only (skip download)
                result = steam_manager.process_rust_assets(progress_callback=progress_callback)
                
                if result.get("success"):
                    # Extract crafting data from Unity bundles
                    progress_callback(70, "Extracting crafting data from Unity bundles...")
                    
                    # Find the items.preload.bundle file
                    bundle_path = steam_manager.steamcmd_dir / "steamapps" / "common" / "Rust" / "Bundles" / "shared" / "items.preload.bundle"
                    
                    if bundle_path.exists():
                        crafting_result = steam_manager.extract_crafting_data_from_bundles(bundle_path, progress_callback)
                        if crafting_result.get("success"):
                            result["recipeCount"] = crafting_result.get("recipe_count", 0)
                            result["message"] = f"Database updated with {result.get('itemCount', 0)} items and {result.get('recipeCount', 0)} crafting recipes"
                        else:
                            result["recipeCount"] = 0
                            result["message"] = f"Database updated with {result.get('itemCount', 0)} items (crafting extraction failed: {crafting_result.get('error', 'Unknown error')})"
                    else:
                        result["recipeCount"] = 0
                        result["message"] = f"Database updated with {result.get('itemCount', 0)} items (bundle file not found)"
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_process_assets_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_process_assets_result({
                    "success": False,
                    "message": f"Process error: {str(e)}"
                }))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def handle_process_assets_result(self, result):
        """Handle process assets result"""
        self.process_assets_button.config(state="normal")
        
        if result.get("success", False):
            item_count = result.get("itemCount", 0)
            self.progress_label_var.set(f"Assets processed: {item_count} items")
            messagebox.showinfo("Success", f"Rust assets processed successfully!\n{item_count} items processed and database updated.")
            # Refresh database stats
            stats_data = self._fetch_database_stats()
            self._update_db_stats_display(stats_data)
            # Automatically refresh the crafting dropdowns with new data
            self.refresh_item_dropdowns()
        else:
            error_msg = result.get("message", "Unknown error")
            self.progress_label_var.set(f"Process failed: {error_msg}")
            messagebox.showerror("Process Failed", f"Failed to process Rust assets:\n{error_msg}")
    
    def regenerate_rust_actions_binds(self):
        """Regenerate all rust-actions binds in keys.cfg"""
        # Disable regenerate button during operation
        self.regenerate_binds_button.config(state="disabled")
        self.progress_label_var.set("Regenerating rust-actions binds...")
        
        def regenerate_thread():
            try:
                # Call the Flask server to regenerate binds with cleared dynamic binds
                try:
                    response = requests.post("http://localhost:5000/binds-manager/regenerate-cleared", timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        success = result.get('success', False)
                        if not success:
                            self.log_message(f"⚠️ Regenerate warning: {result.get('message', 'Unknown error')}")
                    else:
                        success = False
                        self.log_message(f"⚠️ Could not regenerate binds: HTTP {response.status_code}")
                except Exception as e:
                    success = False
                    self.log_message(f"⚠️ Error calling regenerate endpoint: {str(e)}")
                
                if success:
                    # Clear keyboard manager cache and refresh it
                    try:
                        # Get the keyboard manager instance from the Flask app
                        response = requests.get("http://localhost:5000/keyboard-manager/clear-cache", timeout=5)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                self.log_message("✅ Keyboard manager cache cleared successfully")
                            else:
                                self.log_message(f"⚠️ Keyboard manager cache clear warning: {result.get('message', 'Unknown')}")
                        else:
                            self.log_message(f"⚠️ Could not clear keyboard manager cache: HTTP {response.status_code}")
                    except Exception as e:
                        self.log_message(f"⚠️ Error clearing keyboard manager cache: {str(e)}")
                    
                    self.log_message("✅ Dynamic binds have been RESET and cleared")
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_regenerate_result(success))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_regenerate_result(False, str(e)))
        
        threading.Thread(target=regenerate_thread, daemon=True).start()
    
    def handle_regenerate_result(self, success, error_message=None):
        """Handle regenerate binds result"""
        self.regenerate_binds_button.config(state="normal")
        
        if success:
            self.progress_label_var.set("Rust-actions binds regenerated and RESET successfully!")
            messagebox.showinfo("Success", "All rust-actions binds have been regenerated successfully!\n\nThis includes:\n• Crafting binds for all items\n• API command binds\n• Dynamic chat/connection binds (COMPLETELY RESET)\n\nAll dynamic binds have been permanently cleared and reset.\nYou may need to restart Rust or press F1 and type 'exec keys.cfg' to apply the changes.")
        else:
            error_msg = error_message or "Unknown error occurred"
            self.progress_label_var.set(f"Regenerate failed: {error_msg}")
            messagebox.showerror("Regenerate Failed", f"Failed to regenerate rust-actions binds:\n{error_msg}")
    
    def run(self):
        """Start the GUI application"""
        # Check Steam login status on startup
        self.check_steam_login_status()
        self.root.mainloop()

    def toggle_api_panel(self):
        """Toggle the API testing panel visibility"""
        if hasattr(self, 'api_frame'):
            if self.api_panel_visible:
                # Currently visible, so hide it
                self.api_frame.grid_remove()
                self.api_menu.entryconfig(0, label="Show API Testing Panel")
                self.api_panel_visible = False
            else:
                # Currently hidden, so show it
                self.api_frame.grid(row=1, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
                self.api_menu.entryconfig(0, label="Hide API Testing Panel")
                self.api_panel_visible = True

    def toggle_startup(self):
        """Toggle startup with Windows option"""
        try:
            current_state = self.check_startup_enabled()
            if current_state:
                # Disable startup
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                   0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
                try:
                    winreg.DeleteValue(key, "RustGameController")
                except:
                    pass
                winreg.CloseKey(key)
                self.log_message("Startup disabled")
            else:
                # Enable startup
                self.update_startup_command()
                self.log_message("Startup enabled")
            
            # Update menu label
            self.update_menu_labels()
            
        except Exception as e:
            self.log_message(f"⚠️ Failed to toggle startup: {e}")

    def toggle_start_minimized(self):
        """Toggle start minimized option"""
        try:
            current_state = self.check_start_minimized_enabled()
            
            # Create the key if it doesn't exist
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\RustGameController", 
                                   0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            except FileNotFoundError:
                # Create the key
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                     r"Software\RustGameController")
            
            if current_state:
                # Disable start minimized
                winreg.SetValueEx(key, "StartMinimized", 0, winreg.REG_DWORD, 0)
                self.log_message("Start minimized disabled")
            else:
                # Enable start minimized
                winreg.SetValueEx(key, "StartMinimized", 0, winreg.REG_DWORD, 1)
                self.log_message("Start minimized enabled")
            
            winreg.CloseKey(key)
            
            # Update startup command if startup is enabled
            if self.check_startup_enabled():
                self.update_startup_command()
            
            # Update menu label
            self.update_menu_labels()
            
        except Exception as e:
            self.log_message(f"⚠️ Failed to toggle start minimized: {e}")

    def update_menu_labels(self):
        """Update menu labels to reflect current state"""
        if hasattr(self, 'launch_menu'):
            # Update startup label
            startup_enabled = self.check_startup_enabled()
            startup_label = "Start on Boot: Enabled" if startup_enabled else "Start on Boot: Disabled"
            self.launch_menu.entryconfig(0, label=startup_label)
            
            # Update start minimized label
            start_minimized_enabled = self.check_start_minimized_enabled()
            start_minimized_label = "Start Minimized: Enabled" if start_minimized_enabled else "Start Minimized: Disabled"
            self.launch_menu.entryconfig(1, label=start_minimized_label)

    def update_startup_command(self):
        """Update the startup command in registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            
            app_path = sys.argv[0]
            if app_path.endswith('.py'):
                # If running as script, use python executable
                app_path = f'"{sys.executable}" "{app_path}"'
            else:
                # If running as exe
                app_path = f'"{app_path}"'
            
            # Add start minimized parameter if enabled
            if self.check_start_minimized_enabled():
                app_path += ' --minimized'
            
            winreg.SetValueEx(key, "RustGameController", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
        except Exception as e:
            self.log_message(f"Failed to update startup command: {e}")

def main():
    """Main entry point"""
    app = RustControllerGUI()
    
    # Register cleanup function
    def cleanup():
        app.shutdown_event.set()
    
    atexit.register(cleanup)
    
    try:
        # Start the GUI application
        app.run()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
