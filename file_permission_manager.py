#!/usr/bin/env python3
"""
File Permission Manager for Rust Actions
Utility script to manage file permissions for keys.cfg
"""

import sys
import os
from binds_manager import BindsManager
from keyboard_manager import KeyboardManager

def show_current_status():
    """Show the current status of the keys.cfg file."""
    manager = BindsManager()
    
    print("=== Rust Actions File Permission Status ===")
    print(f"File: {manager.keys_cfg_path}")
    
    if os.path.exists(manager.keys_cfg_path):
        is_readonly = manager.is_file_readonly()
        print(f"Exists: Yes")
        print(f"Read-only: {is_readonly}")
        
        if is_readonly:
            print("Status: ✅ PROTECTED - File is read-only and safe from game modifications")
        else:
            print("Status: ⚠️  UNPROTECTED - File is writable and may be modified by the game")
    else:
        print("Exists: No")
        print("Status: ❌ MISSING - File does not exist")

def set_protected():
    """Set the keys.cfg file to read-only (protected)."""
    print("=== Setting File to Protected (Read-Only) ===")
    
    manager = BindsManager()
    
    if not os.path.exists(manager.keys_cfg_path):
        print("❌ Error: keys.cfg file does not exist")
        return False
    
    success = manager.set_file_readonly()
    if success:
        print("✅ Successfully set keys.cfg to read-only")
        print("The file is now protected from game modifications")
        return True
    else:
        print("❌ Failed to set file to read-only")
        return False

def set_writable():
    """Set the keys.cfg file to writable."""
    print("=== Setting File to Writable ===")
    
    manager = BindsManager()
    
    if not os.path.exists(manager.keys_cfg_path):
        print("❌ Error: keys.cfg file does not exist")
        return False
    
    success = manager.set_file_writable()
    if success:
        print("✅ Successfully set keys.cfg to writable")
        print("The file can now be modified (use with caution)")
        return True
    else:
        print("❌ Failed to set file to writable")
        return False

def regenerate_protected():
    """Regenerate the keys.cfg file with protected write operations."""
    print("=== Regenerating keys.cfg with Protection ===")
    
    manager = BindsManager()
    
    success = manager.write_keys_cfg_with_sections_protected()
    if success:
        print("✅ Successfully regenerated keys.cfg with protection")
        print("The file is now read-only and protected from game modifications")
        return True
    else:
        print("❌ Failed to regenerate keys.cfg")
        return False

def regenerate_writable():
    """Regenerate the keys.cfg file and leave it writable."""
    print("=== Regenerating keys.cfg (Writable) ===")
    
    manager = BindsManager()
    
    # Set to writable first
    if not manager.set_file_writable():
        print("❌ Failed to set file to writable")
        return False
    
    # Write the file
    success = manager.write_keys_cfg_with_sections()
    if success:
        print("✅ Successfully regenerated keys.cfg")
        print("The file is writable (remember to protect it later)")
        return True
    else:
        print("❌ Failed to regenerate keys.cfg")
        return False

def test_keyboard_manager():
    """Test the keyboard manager functionality."""
    print("=== Testing Keyboard Manager ===")
    
    try:
        manager = KeyboardManager()
        stats = manager.get_stats()
        
        print("✅ Keyboard Manager initialized successfully")
        print(f"Total binds: {stats['total_binds']}")
        print(f"Crafting items: {stats['available_commands']['crafting_items']}")
        print(f"API commands: {stats['available_commands']['api_commands']}")
        print(f"Chat commands: {stats['available_commands']['chat_commands']}")
        
        return True
    except Exception as e:
        print(f"❌ Keyboard Manager test failed: {e}")
        return False

def show_help():
    """Show help information."""
    print("=== Rust Actions File Permission Manager ===")
    print()
    print("Usage: python file_permission_manager.py [command]")
    print()
    print("Commands:")
    print("  status          - Show current file status")
    print("  protect         - Set file to read-only (protected)")
    print("  writable        - Set file to writable")
    print("  regenerate      - Regenerate keys.cfg with protection")
    print("  regenerate-w    - Regenerate keys.cfg (writable)")
    print("  test            - Test keyboard manager")
    print("  help            - Show this help message")
    print()
    print("Examples:")
    print("  python file_permission_manager.py status")
    print("  python file_permission_manager.py protect")
    print("  python file_permission_manager.py regenerate")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_current_status()
    elif command == "protect":
        set_protected()
    elif command == "writable":
        set_writable()
    elif command == "regenerate":
        regenerate_protected()
    elif command == "regenerate-w":
        regenerate_writable()
    elif command == "test":
        test_keyboard_manager()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_help()

if __name__ == "__main__":
    main()
