#!/usr/bin/env python3
"""
Debug exact line causing segfault in dashboard creation
"""

import sys
import tkinter as tk
from tkinter import ttk

class DashboardDebug:
    def __init__(self):
        print("Initializing dashboard debug...")
        
        self.root = tk.Tk()
        self.root.title("Dashboard Debug")
        self.root.geometry("800x600")
        
        # Create notebook first
        print("Creating notebook...")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Now debug dashboard creation line by line
        print("Starting dashboard creation debug...")
        self.create_dashboard_debug()
        
        print("Dashboard debug complete!")
    
    def create_dashboard_debug(self):
        """Debug dashboard creation step by step"""
        try:
            print("Step A: Creating dashboard frame...")
            dashboard_frame = ttk.Frame(self.notebook)
            self.notebook.add(dashboard_frame, text="🎯 Dashboard")
            
            print("Step B: Creating main frame...")
            main_frame = tk.Frame(dashboard_frame, bg='#0f0f1e')
            main_frame.pack(fill='both', expand=True)
            
            print("Step C: Creating overview frame...")
            overview_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='ridge', bd=2)
            overview_frame.pack(fill='x', padx=10, pady=10)
            
            print("Step D: Creating title label...")
            tk.Label(overview_frame, text="SYSTEM STATUS", 
                    font=("Courier", 14, "bold"), fg='#00d4ff', bg='#1a1a2e').pack(pady=10)
            
            print("Step E: Creating CPU label...")
            self.cpu_label = tk.Label(overview_frame, text="⚡ CPU: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
            self.cpu_label.pack(anchor='w', padx=10, pady=2)
            
            print("Step F: Creating memory label...")
            self.mem_label = tk.Label(overview_frame, text="💾 Memory: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
            self.mem_label.pack(anchor='w', padx=10, pady=2)
            
            print("Step G: Creating disk label...")
            self.disk_label = tk.Label(overview_frame, text="💿 Disk: Checking...", 
                                      bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
            self.disk_label.pack(anchor='w', padx=10, pady=2)
            
            print("Step H: Creating server label...")
            self.server_label = tk.Label(overview_frame, text="🖥️ Ebon: Checking...", 
                                        bg='#1a1a2e', fg='#fa0', font=("Courier", 10))
            self.server_label.pack(anchor='w', padx=10, pady=2)
            
            print("Step I: Creating actions frame...")
            actions_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='groove', bd=2)
            actions_frame.pack(fill='x', padx=10, pady=10)
            
            print("Step J: Creating actions title...")
            tk.Label(actions_frame, text="QUICK ACTIONS", 
                    font=("Courier", 12, "bold"), fg='#00d4ff', bg='#1a1a2e').pack(pady=10)
            
            print("Step K: Creating button frame...")
            button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
            button_frame.pack(pady=10)
            
            print("Step L: Defining button style...")
            button_style = {
                'font': ('Courier', 10, 'bold'),
                'bg': '#2a2a3e',
                'fg': '#00d4ff',
                'activebackground': '#3a3a4e',
                'relief': 'raised',
                'bd': 2,
                'padx': 15
            }
            
            print("Step M: Creating first button...")
            tk.Button(button_frame, text="🔍 SYSTEM SCAN", 
                     command=self.dummy_function, **button_style).pack(side='left', padx=5)
            
            print("Step N: Creating second button...")
            tk.Button(button_frame, text="🔗 TEST EBON", 
                     command=self.dummy_function, **button_style).pack(side='left', padx=5)
            
            print("Step O: Creating third button...")
            tk.Button(button_frame, text="📊 UPDATE STATUS", 
                     command=self.dummy_function, **button_style).pack(side='left', padx=5)
            
            print("✅ All dashboard steps completed successfully!")
            
        except Exception as e:
            print(f"💥 SEGFAULT AT: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def dummy_function(self):
        """Dummy function for buttons"""
        print("Button clicked!")
    
    def run(self):
        """Run the debug test"""
        try:
            print("Starting debug main loop...")
            self.root.mainloop()
        except Exception as e:
            print(f"Error in debug main loop: {e}")

if __name__ == '__main__':
    print("Starting dashboard creation debug...")
    
    try:
        debug = DashboardDebug()
        debug.run()
    except Exception as e:
        print(f"Fatal debug error: {e}")
        import traceback
        traceback.print_exc()
    
    print("Debug test complete.")