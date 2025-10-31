#!/usr/bin/env python3
"""
NexusController - Minimal Working Version
Testing specific components to identify segfault cause
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime

class NexusControllerMinimal:
    def __init__(self):
        print("Initializing minimal NexusController...")
        
        try:
            self.root = tk.Tk()
            self.root.title("NexusController - Minimal")
            self.root.geometry("800x600")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.shutdown_flag = False
            
            print("Creating basic UI...")
            self.create_basic_ui()
            
            print("Setup complete!")
            
        except Exception as e:
            print(f"Error in __init__: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def create_basic_ui(self):
        """Create minimal UI to test stability"""
        try:
            # Simple header
            header = tk.Frame(self.root, bg='#1a1a2e', height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            title_label = tk.Label(header, text="🌐 NexusController - Test", 
                                  font=("Arial", 18, "bold"), fg='#00d4ff', bg='#1a1a2e')
            title_label.pack(expand=True)
            
            # Notebook
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Test tab
            test_frame = ttk.Frame(self.notebook)
            self.notebook.add(test_frame, text="Test")
            
            # Simple content
            test_label = tk.Label(test_frame, text="Testing NexusController Stability", 
                                 font=("Arial", 14))
            test_label.pack(pady=20)
            
            # Test button
            test_button = tk.Button(test_frame, text="Test Function", 
                                   command=self.test_function,
                                   font=("Arial", 12), bg='#2a2a3e', fg='#00d4ff')
            test_button.pack(pady=10)
            
            # Status label
            self.status_label = tk.Label(test_frame, text="Status: Ready", 
                                        font=("Arial", 10))
            self.status_label.pack(pady=10)
            
            # Output area
            self.output = scrolledtext.ScrolledText(test_frame, height=15,
                                                   bg='#0a0a1e', fg='#0f8',
                                                   font=('Courier', 10))
            self.output.pack(fill='both', expand=True, padx=10, pady=10)
            
            self.output.insert(tk.END, "[NEXUS] Minimal controller initialized\\n")
            self.output.insert(tk.END, "[INFO] All systems operational\\n")
            
            print("UI created successfully!")
            
        except Exception as e:
            print(f"Error creating UI: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def test_function(self):
        """Test function to verify everything works"""
        try:
            self.status_label.config(text="Status: Running test...")
            self.output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Test function executed\\n")
            self.output.see(tk.END)
            
            # Test threading
            threading.Thread(target=self.background_test, daemon=True).start()
            
        except Exception as e:
            print(f"Error in test function: {e}")
            self.output.insert(tk.END, f"[ERROR] {e}\\n")
    
    def background_test(self):
        """Test background operation"""
        try:
            time.sleep(1)
            self.root.after(0, lambda: self.status_label.config(text="Status: Background test complete"))
            self.root.after(0, lambda: self.output.insert(tk.END, "[BACKGROUND] Test completed successfully\\n"))
            self.root.after(0, lambda: self.output.see(tk.END))
            
        except Exception as e:
            print(f"Error in background test: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        print("Shutting down...")
        self.shutdown_flag = True
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            print("Starting main loop...")
            self.root.mainloop()
            print("Main loop ended.")
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Starting NexusController Minimal Test...")
    
    try:
        app = NexusControllerMinimal()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("Application exited normally.")